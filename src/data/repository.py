import io

import pandas as pd

from src.config import SHEET_HEADER_ROW


def _read_sheet(workbook_bytes: bytes, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(workbook_bytes), sheet_name=sheet, header=SHEET_HEADER_ROW[sheet])
    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
    return df


def get_companies(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "1_Company_Master")


def get_value_chain(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "2_Value_Chain_Master")


def get_supply_chain(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "3_Supply_Chain_Master")


def get_risks(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "4_Risk_Register")


def risks_exploded_by_vc_node(risks: pd.DataFrame) -> pd.DataFrame:
    """No cot vc_node_id da-gia-tri (vd "MS-001, MS-002") thanh nhieu dong, moi dong 1 node."""
    df = risks.dropna(subset=["vc_node_id"]).copy()
    df["vc_node_id"] = df["vc_node_id"].astype(str).str.split(",")
    df = df.explode("vc_node_id")
    df["vc_node_id"] = df["vc_node_id"].str.strip()
    return df[df["vc_node_id"] != ""]


def risk_counts_by_node(risks: pd.DataFrame) -> pd.Series:
    if risks.empty or "vc_node_id" not in risks.columns:
        return pd.Series(dtype=int)
    exploded = risks_exploded_by_vc_node(risks)
    if exploded.empty:
        return pd.Series(dtype=int)
    return exploded.groupby("vc_node_id")["risk_id"].nunique()


def risks_for_node(risks: pd.DataFrame, vc_node_id: str) -> pd.DataFrame:
    exploded = risks_exploded_by_vc_node(risks)
    if exploded.empty:
        return exploded
    return risks[risks["risk_id"].isin(exploded.loc[exploded["vc_node_id"] == vc_node_id, "risk_id"])]


def risk_counts_by_sc_link(risks: pd.DataFrame) -> pd.Series:
    """sc_link_id la single-value (khong nhu vc_node_id) nen khong can explode."""
    if risks.empty or "sc_link_id" not in risks.columns:
        return pd.Series(dtype=int)
    df = risks.dropna(subset=["sc_link_id"])
    if df.empty:
        return pd.Series(dtype=int)
    return df.groupby("sc_link_id")["risk_id"].nunique()


def risks_for_sc_link(risks: pd.DataFrame, sc_link_id: str) -> pd.DataFrame:
    return risks[risks["sc_link_id"] == sc_link_id]


def get_risk_taxonomy(workbook_bytes: bytes) -> pd.DataFrame:
    """Danh muc rui ro toan Tap doan GELEX (sheet '0. Danh muc rui ro', 146 dong - RONG hon
    4_Risk_Register dang dung, nhung dung chung khong gian ma risk_id). Chi lay 2 cot can
    de tra cuu: risk_id -> risk_category_l2 (ma nhom dang so, vd '4.3. Mua hang/dich vu'),
    la khoa noi voi sheet 8_Risk_node (xem risks_triggered_by)."""
    df = _read_sheet(workbook_bytes, "0. Danh mục rủi ro")
    return df[["risk_id", "risk_category_l2"]].dropna()


def get_risk_trigger_edges(workbook_bytes: bytes) -> pd.DataFrame:
    """Quan he "nhom rui ro nay co the kich hoat nhom khac" (sheet 8_Risk_node, 220 dong).
    Chieu da xac nhan voi nguoi dung: Source Node -> kich hoat -> Target Node. Cot mau va
    cot "a" trong sheet goc khong co y nghia (da hoi nguoi dung) - bo qua khong doc."""
    df = _read_sheet(workbook_bytes, "8_Risk_node")
    df = df.rename(columns={"Source Node": "source", "Target Node": "target"})
    return df[["source", "target"]].dropna()


def risks_triggered_by(risk_id: str, taxonomy: pd.DataFrame, edges: pd.DataFrame) -> list[str]:
    """Ten cac nhom rui ro (risk_category_l2) ma risk_id da cho co the kich hoat, dua theo
    danh muc rui ro Tap doan + sheet 8_Risk_node. Tra ve rong neu khong tra duoc nhom, hoac
    nhom do khong co quan he kich hoat nao - KHONG tu suy dien."""
    cat_rows = taxonomy.loc[taxonomy["risk_id"] == risk_id, "risk_category_l2"]
    if cat_rows.empty:
        return []
    return risks_triggered_by_category(cat_rows.iloc[0], edges)


def risks_triggered_by_category(category_l2: str, edges: pd.DataFrame) -> list[str]:
    """Nhu risks_triggered_by nhung tra thang theo 1 ma nhom rui ro cap 2 da biet (dung cho
    rui ro nhap - noi nguoi dung tu chon nhom thay vi co san risk_id)."""
    return sorted(edges.loc[edges["source"] == category_l2, "target"].unique().tolist())


def companies_in(df: pd.DataFrame, companies: pd.DataFrame, id_columns: list[str]) -> set[str]:
    """Cong ty (trong Company Master) co xuat hien trong 1 hoac nhieu cot id cua df da cho.
    Dung de tinh available_ids rieng cho tung trang (vd supply chain xet ca 2 cot
    upstream/downstream_entity_id, value chain/risk chi xet company_id)."""
    valid_ids = set(companies["company_id"].dropna().astype(str).str.strip())
    ids: set[str] = set()
    for col in id_columns:
        if col in df.columns:
            ids |= set(df[col].dropna().astype(str).str.strip())
    return ids & valid_ids


def companies_with_data(
    companies: pd.DataFrame, value_chain: pd.DataFrame, supply_chain: pd.DataFrame, risks: pd.DataFrame
) -> set[str]:
    """Cong ty co du lieu o BAT KY sheet nao (hop cua ca 3 nguon) - dung cho KPI tong quan
    o trang chu. Cac trang rieng le nen dung companies_in() voi cot phu hop hon."""
    return (
        companies_in(value_chain, companies, ["company_id"])
        | companies_in(risks, companies, ["company_id"])
        | companies_in(supply_chain, companies, ["upstream_entity_id", "downstream_entity_id"])
    )
