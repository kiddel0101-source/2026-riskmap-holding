"""Do tu khoa (khong AI) tu 1 su kien nguoi dung nhap vao Risk Register / Supply Chain / Risk
Driver Library hien co, cho trang Su kien rui ro. Chi chi ra du lieu DA CO lien quan, khong tu
suy dien them rui ro moi - moi ket qua phai giai thich duoc khop vi cot nao, tu khoa nao.

⚠️ Truoc day co them nguon "Value Chain" (dua vao sheet "2_Value_Chain_Master") - sheet do da
bi xoa khoi workbook nguon, khong co sheet thay the, da bo nguon nay (xem CLAUDE.md Muc 11.5).

Do 2 tang: KHOP CHINH XAC (giu nguyen dau, chi bo qua hoa/thuong) chay truoc; chi tu khoa
nao khong ra ket qua chinh xac nao moi thu lai bang KHOP GAN DUNG (bo dau). Ly do: bo het
dau tieng Viet lam nhieu tu khac nghia bi gop lam mot (vd "đồng" [kim loai] va "động" [hoat
dong] deu rut gon thanh "dong"), tung gay khop sai hang loat khi test - xem smoke test.
"""

import html
import re
import unicodedata
from dataclasses import dataclass

import pandas as pd

from src.config import COLUMN_LABELS
from src.data.repository import decode_industries
from src.theme import nz

_RISK_FIELDS = [
    "risk_category_l1", "risk_desc", "risk_event_l3",
    "root_cause", "impact_description", "impact_area", "existing_controls",
]
_SC_FIELDS = [
    "input_output_type", "geographic_origin", "contract_type",
    "substitutability", "upstream_entity_id", "downstream_entity_id",
]
_DRIVER_FIELDS = ["driver_category", "driver_name", "driver_details"]

_SPLIT_PATTERN = re.compile(
    r"[,.;\n]| và | làm | khiến | gây | dẫn đến | do | vì ", flags=re.IGNORECASE
)


@dataclass
class EventMatch:
    source: str  # "risk" | "supply_chain"
    ref_id: str
    label: str
    company_id: str
    field_label: str
    snippet_html: str
    keyword: str
    is_exact: bool  # False = chi khop sau khi bo dau (co the khac nghia, can doc lai trich doan)


@dataclass
class DriverMatch:
    """Khop tu khoa voi 1 yeu to dan phat (Risk_Driver_Library, xem CLAUDE.md Muc 11.11) - khac
    EventMatch vi 1 driver co san san du lieu tong hop (nganh + danh sach danh muc rui ro lien
    quan) ngay tu chinh no, khong can join/dem tu nguon khac."""
    driver_name: str
    driver_category: str
    keyword: str
    is_exact: bool
    snippet_html: str
    field_label: str
    industries: list[str]
    risk_links: list[dict]  # [{"risk_category_id":.., "risk_category_l2":.., "mechanism":..}]
    source_url: str | None


def strip_diacritics(text: str) -> str:
    norm = unicodedata.normalize("NFD", text)
    no_marks = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return no_marks.replace("đ", "d").replace("Đ", "D").lower()


def parse_keywords(raw: str) -> list[str]:
    return [k.strip() for k in raw.split(",") if k.strip()]


def suggest_keywords(description: str) -> str:
    """Tach cau mo ta thanh cum tu khoa goi y - cat theo dau cau va vai lien tu thuong
    gap (khong phai AI/NLP, chi la regex split), giu lai cum > 1 tu de tranh qua vun.
    Nguoi dung xem lai/sua truoc khi tim, nen goi y sai cung khong sao."""
    if not description.strip():
        return ""
    parts = _SPLIT_PATTERN.split(description)
    cleaned = [p.strip(" .,;") for p in parts]
    cleaned = [p for p in cleaned if len(p.split()) >= 2]
    return ", ".join(cleaned[:6])


def _snippet_html(original: str, keyword: str, *, loose: bool, context: int = 45) -> str | None:
    if loose:
        haystack, needle = strip_diacritics(original), strip_diacritics(keyword)
    else:
        haystack, needle = original.lower(), keyword.lower()
    idx = haystack.find(needle)
    if idx < 0:
        return None
    end_idx = idx + len(needle)
    start = max(0, idx - context)
    end = min(len(original), end_idx + context)
    before = html.escape(original[start:idx])
    matched = html.escape(original[idx:end_idx])
    after = html.escape(original[end_idx:end])
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(original) else ""
    return f"{prefix}{before}<mark>{matched}</mark>{after}{suffix}"


def _scan_rows(rows: pd.DataFrame, fields: list[str], keywords: list[str], *, loose: bool,
                source: str, ref_col: str, label_fn, company_fn) -> list[EventMatch]:
    kws = [k for k in keywords if k.strip()]
    matches: list[EventMatch] = []
    for _, row in rows.iterrows():
        matched_cols: set[str] = set()
        for col in fields:
            if col not in row or pd.isna(row[col]) or col in matched_cols:
                continue
            text = str(row[col])
            if not text.strip():
                continue
            for kw in kws:
                snippet = _snippet_html(text, kw, loose=loose)
                if snippet:
                    matches.append(EventMatch(
                        source=source,
                        ref_id=str(row[ref_col]),
                        label=label_fn(row),
                        company_id=company_fn(row),
                        field_label=COLUMN_LABELS.get(col, col),
                        snippet_html=snippet,
                        keyword=kw,
                        is_exact=not loose,
                    ))
                    matched_cols.add(col)
                    break
    return matches


def _company_supply_chain(r, member_company_ids: set[str]):
    if str(r.get("downstream_entity_id")) in member_company_ids:
        return str(r["downstream_entity_id"])
    if str(r.get("upstream_entity_id")) in member_company_ids:
        return str(r["upstream_entity_id"])
    return "—"


def _scan_source(source: str, df: pd.DataFrame, keywords: list[str], *, loose: bool,
                  member_company_ids: set[str] | None = None) -> list[EventMatch]:
    if source == "risk":
        return _scan_rows(
            df, _RISK_FIELDS, keywords, loose=loose, source="risk", ref_col="risk_id",
            label_fn=lambda r: str(r["risk_id"]), company_fn=lambda r: nz(r.get("company_id")),
        )
    if source == "supply_chain":
        return _scan_rows(
            df, _SC_FIELDS, keywords, loose=loose, source="supply_chain", ref_col="sc_link_id",
            label_fn=lambda r: f"{r['sc_link_id']} — {r['upstream_entity_id']} → {r['downstream_entity_id']}",
            company_fn=lambda r: _company_supply_chain(r, member_company_ids or set()),
        )
    raise ValueError(source)


def scan_all(
    risks: pd.DataFrame, supply_chain: pd.DataFrame,
    keywords: list[str], member_company_ids: set[str],
) -> dict[str, list[EventMatch]]:
    """Khop chinh xac truoc cho ca 2 nguon; tu khoa nao khong ra khop chinh xac nao (o CA 2
    nguon) moi duoc thu lai bang khop gan dung (bo dau) - de khong lam loang ket qua dung
    bang qua nhieu khop gan dung khi da co khop chinh xac roi."""
    sources = {
        "risk": risks, "supply_chain": supply_chain,
    }
    exact = {
        name: _scan_source(name, df, keywords, loose=False, member_company_ids=member_company_ids)
        for name, df in sources.items()
    }
    exact_keywords = {m.keyword for group in exact.values() for m in group}
    remaining = [k for k in keywords if k not in exact_keywords]
    if not remaining:
        return exact

    loose = {
        name: _scan_source(name, df, remaining, loose=True, member_company_ids=member_company_ids)
        for name, df in sources.items()
    }
    return {name: exact[name] + loose[name] for name in sources}


# Giu lai 2 ham rieng (chi khop chinh xac) de smoke test/noi khac goi don gian neu can,
# khong can di qua scan_all.
def scan_risks(risks: pd.DataFrame, keywords: list[str], *, loose: bool = False) -> list[EventMatch]:
    return _scan_source("risk", risks, keywords, loose=loose)


def scan_supply_chain(
    sc: pd.DataFrame, keywords: list[str], member_company_ids: set[str], *, loose: bool = False
) -> list[EventMatch]:
    return _scan_source("supply_chain", sc, keywords, loose=loose, member_company_ids=member_company_ids)


def group_matches(matches: list[EventMatch]) -> list[dict]:
    """Gop nhieu EventMatch cua CUNG 1 doi tuong (vd 1 rui ro khop ca cot "Su kien rui ro"
    lan "Kiem soat hien co") thanh 1 nhom - de ve 1 the/1 checkbox duy nhat thay vi lap lai
    nhieu lan cho cung 1 rui ro/hoat dong."""
    groups: dict[tuple, dict] = {}
    order: list[tuple] = []
    for m in matches:
        key = (m.ref_id, m.company_id)
        if key not in groups:
            groups[key] = {"ref_id": m.ref_id, "label": m.label, "company_id": m.company_id, "items": []}
            order.append(key)
        groups[key]["items"].append(m)
    return [groups[k] for k in order]


def _aggregate_drivers(drivers: pd.DataFrame) -> pd.DataFrame:
    """Risk_Driver_Library co 1 dong = 1 CAP (driver, danh muc rui ro) - 1 driver lap lai tren
    nhieu dong voi driver_name/details/category GIONG HET nhau (xem CLAUDE.md Muc 11.11). Neu
    do tu khoa truc tiep tren df tho, 1 driver co N dong se ra N ket qua trung lap vo ich (cung
    trich doan). Gop truoc thanh 1 dong/driver: `industries` = UNION decode_industries() tren
    MOI dong (da gap 3/49 driver ghi Industry_type khong nhat quan giua cac dong - gop khong
    chan), `risk_links` = danh sach {risk_category_id, risk_category_l2, mechanism} theo tung
    dong goc cua driver do."""
    if drivers.empty:
        return drivers

    rows = []
    for name, g in drivers.groupby("driver_name", sort=False):
        industries: list[str] = []
        for v in g.get("industry_type", []):
            for ind in decode_industries(v):
                if ind not in industries:
                    industries.append(ind)
        risk_links = [
            {
                "risk_category_id": r.get("risk_category_id"),
                "risk_category_l2": r.get("risk_category_l2"),
                "mechanism": r.get("mechanism"),
            }
            for _, r in g.iterrows()
            if pd.notna(r.get("risk_category_l2")) or pd.notna(r.get("mechanism"))
        ]
        first = g.iloc[0]
        rows.append({
            "driver_name": name,
            "driver_category": first.get("driver_category"),
            "driver_details": first.get("driver_details"),
            "industries": industries,
            "risk_links": risk_links,
            "source_url": next((u for u in g.get("source_url", []) if pd.notna(u)), None),
        })
    return pd.DataFrame(rows)


def _scan_drivers(drivers_agg: pd.DataFrame, keywords: list[str], *, loose: bool) -> list[DriverMatch]:
    kws = [k for k in keywords if k.strip()]
    matches: list[DriverMatch] = []
    for _, row in drivers_agg.iterrows():
        matched_cols: set[str] = set()
        for col in _DRIVER_FIELDS:
            if col not in row or pd.isna(row[col]) or col in matched_cols:
                continue
            text = str(row[col])
            if not text.strip():
                continue
            for kw in kws:
                snippet = _snippet_html(text, kw, loose=loose)
                if snippet:
                    matches.append(DriverMatch(
                        driver_name=row["driver_name"], driver_category=nz(row.get("driver_category")),
                        keyword=kw, is_exact=not loose, snippet_html=snippet,
                        field_label=COLUMN_LABELS.get(col, col),
                        industries=row["industries"], risk_links=row["risk_links"],
                        source_url=row.get("source_url"),
                    ))
                    matched_cols.add(col)
                    break
    return matches


def scan_drivers_all(drivers: pd.DataFrame, keywords: list[str]) -> list[DriverMatch]:
    """Khop chinh xac truoc, tu khoa nao khong ra ket qua moi thu lai bang khop gan dung (bo
    dau) - dung 2 tang giong scan_all(). Tu gop driver truoc khi do (xem _aggregate_drivers)."""
    agg = _aggregate_drivers(drivers)
    if agg.empty:
        return []
    exact = _scan_drivers(agg, keywords, loose=False)
    exact_keywords = {m.keyword for m in exact}
    remaining = [k for k in keywords if k not in exact_keywords]
    if not remaining:
        return exact
    loose = _scan_drivers(agg, remaining, loose=True)
    return exact + loose


def group_driver_matches(matches: list[DriverMatch]) -> list[dict]:
    """Gop nhieu DriverMatch cua CUNG 1 driver (vd khop ca driver_name lan driver_details)
    thanh 1 nhom - 1 the/driver duy nhat."""
    groups: dict[str, dict] = {}
    order: list[str] = []
    for m in matches:
        if m.driver_name not in groups:
            groups[m.driver_name] = {
                "driver_name": m.driver_name, "driver_category": m.driver_category,
                "industries": m.industries, "risk_links": m.risk_links,
                "source_url": m.source_url, "items": [],
            }
            order.append(m.driver_name)
        groups[m.driver_name]["items"].append(m)
    return [groups[k] for k in order]
