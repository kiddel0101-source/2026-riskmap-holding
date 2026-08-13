"""Do tu khoa (khong AI) tu 1 su kien nguoi dung nhap vao Risk Register / Value Chain /
Supply Chain hien co, cho trang Su kien rui ro. Chi chi ra du lieu DA CO lien quan, khong
tu suy dien them rui ro moi - moi ket qua phai giai thich duoc khop vi cot nao, tu khoa nao.

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
from src.theme import nz

_RISK_FIELDS = [
    "risk_category_l1", "risk_category_l2", "risk_event_l3",
    "root_cause", "impact_description", "impact_area", "existing_controls",
]
_VC_FIELDS = ["vc_function", "vc_sub_function", "activity_description", "dependency_note"]
_SC_FIELDS = [
    "input_output_type", "geographic_origin", "contract_type",
    "substitutability", "upstream_entity_id", "downstream_entity_id",
]

_SPLIT_PATTERN = re.compile(
    r"[,.;\n]| và | làm | khiến | gây | dẫn đến | do | vì ", flags=re.IGNORECASE
)


@dataclass
class EventMatch:
    source: str  # "risk" | "value_chain" | "supply_chain"
    ref_id: str
    label: str
    company_id: str
    field_label: str
    snippet_html: str
    keyword: str
    is_exact: bool  # False = chi khop sau khi bo dau (co the khac nghia, can doc lai trich doan)


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


def _label_value_chain(r):
    sub = r.get("vc_sub_function")
    return f"{r['vc_node_id']} — {sub}" if pd.notna(sub) and str(sub).strip() else str(r["vc_node_id"])


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
    if source == "value_chain":
        return _scan_rows(
            df, _VC_FIELDS, keywords, loose=loose, source="value_chain", ref_col="vc_node_id",
            label_fn=_label_value_chain, company_fn=lambda r: nz(r.get("company_id")),
        )
    if source == "supply_chain":
        return _scan_rows(
            df, _SC_FIELDS, keywords, loose=loose, source="supply_chain", ref_col="sc_link_id",
            label_fn=lambda r: f"{r['sc_link_id']} — {r['upstream_entity_id']} → {r['downstream_entity_id']}",
            company_fn=lambda r: _company_supply_chain(r, member_company_ids or set()),
        )
    raise ValueError(source)


def scan_all(
    risks: pd.DataFrame, value_chain: pd.DataFrame, supply_chain: pd.DataFrame,
    keywords: list[str], member_company_ids: set[str],
) -> dict[str, list[EventMatch]]:
    """Khop chinh xac truoc cho ca 3 nguon; tu khoa nao khong ra khop chinh xac nao (o CA 3
    nguon) moi duoc thu lai bang khop gan dung (bo dau) - de khong lam loang ket qua dung
    bang qua nhieu khop gan dung khi da co khop chinh xac roi."""
    sources = {
        "risk": risks, "value_chain": value_chain, "supply_chain": supply_chain,
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


# Giu lai 3 ham rieng (chi khop chinh xac) de smoke test/noi khac goi don gian neu can,
# khong can di qua scan_all.
def scan_risks(risks: pd.DataFrame, keywords: list[str], *, loose: bool = False) -> list[EventMatch]:
    return _scan_source("risk", risks, keywords, loose=loose)


def scan_value_chain(vc: pd.DataFrame, keywords: list[str], *, loose: bool = False) -> list[EventMatch]:
    return _scan_source("value_chain", vc, keywords, loose=loose)


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
