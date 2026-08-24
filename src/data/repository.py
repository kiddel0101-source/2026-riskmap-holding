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
    """Danh muc rui ro toan Tap doan GELEX (sheet '0. Danh muc rui ro', 145 dong - RONG hon
    4_Risk_Register dang dung, nhung dung chung khong gian ma risk_id). Lay risk_id +
    VC2_ID (da xac minh: cot noi thang risk_id sang hoat dong trong Sheet1, phu 143/145
    dong) - la khoa noi sang get_value_chain_v2()/get_risk_trigger_edges() (xem
    risks_triggered_by). Sheet co 2 cot trung ten "VC2_ID"; pandas tu doi ten cot thu 2
    thanh "VC2_ID.1" - chi dung cot dau (chinh).
    """
    df = _read_sheet(workbook_bytes, "0. Danh mục rủi ro")
    out = df[["risk_id", "VC2_ID"]].rename(columns={"VC2_ID": "vc2_id"})
    return out.dropna()


def get_value_chain_v2(workbook_bytes: bytes) -> pd.DataFrame:
    """Mo hinh Chuoi gia tri Porter DAY DU 9 khoi (sheet 'Sheet1', 75 dong) dung chung cho
    toan Tap doan GELEX - KHONG co cot cong ty, thay the 2_Value_Chain_Master CHI o trang
    Chuoi gia tri (cac trang khac - Trang chu, Su kien rui ro - van dung
    2_Value_Chain_Master nhu cu, xem CLAUDE.md Muc 11.3).

    1 dong = 1 (hoat dong, rui ro) - 1 hoat dong (vc2_id) co the lap lai nhieu dong neu co
    nhieu rui ro gan truc tiep (toi da 3), cot rui ro se rong o cac hoat dong chua co rui ro.

    ⚠️ Sheet nay dang duoc nguoi phu trach du lieu chinh sua truc tiep tren SharePoint - da
    it nhat 1 lan doi ten cot goc (vd "Chuoi gia tri 1" -> "Value Chain"). Rename map o day
    chap nhan CA 2 ten cu/moi cho tung cot de giam rui ro vo lai khi ho doi tiep.
    """
    df = _read_sheet(workbook_bytes, "Sheet1")
    return df.rename(columns={
        "Chuỗi giá trị 1": "vc1_name", "Value Chain": "vc1_name", "VC1_ID": "vc1_id",
        "Chuỗi giá trị 2": "vc2_name", "Sub-Value Chain": "vc2_name", "VC2_ID": "vc2_id",
        "Phân loại": "category", "Value chain_3": "vc3_name",
        "Risk": "risk_name", "Risk_ID": "risk_id",
        "Problem": "problem", "Details": "details",
    })


def get_risk_trigger_edges(workbook_bytes: bytes) -> pd.DataFrame:
    """Quan he "rui ro nay co the kich hoat rui ro khac" (sheet Risk_Linkages) - CHI TIET
    hon han 8_Risk_node cu (noi thang risk_id voi risk_id, kem mo ta co che + muc anh
    huong, khong chi noi ten nhom chung chung). Da chot voi nguoi dung chuyen han sang dung
    sheet nay. ⚠️ Hien CHI co 1 dong du lieu that (LNK-001) - do phu con rat thap, nguoi
    dung da chap nhan dung tam trong luc cho bo sung them."""
    df = _read_sheet(workbook_bytes, "Risk_Linkages")
    return df.rename(columns={
        "Source_Risk_ID": "source_risk_id", "Source_Risk_Name": "source_risk_name",
        "Target_Risk_ID": "target_risk_id", "Target_Risk_Name": "target_risk_name",
        "Mô tả cơ chế liên kết": "mechanism", "Mức độ ảnh hưởng": "impact_level",
    }).dropna(subset=["source_risk_id", "target_risk_id"])


def risks_triggered_by_vc2(vc2_id: str, vc2_df: pd.DataFrame, edges: pd.DataFrame) -> list[dict]:
    """Danh sach rui ro CO THE BI KICH HOAT boi 1 hoat dong Chuoi gia tri (vc2_id) - tra ve
    rong neu hoat dong chua gan rui ro nao, hoac rui ro do khong co quan he kich hoat nao
    trong Risk_Linkages - KHONG tu suy dien. Dung truc tiep cho rui ro nhap (nguoi dung tu
    chon 1 hoat dong thay vi co san risk_id)."""
    source_ids = vc2_df.loc[vc2_df["vc2_id"] == vc2_id, "risk_id"].dropna().unique().tolist()
    if not source_ids:
        return []
    hits = edges[edges["source_risk_id"].isin(source_ids)]
    return hits[["target_risk_id", "target_risk_name", "mechanism", "impact_level"]].drop_duplicates().to_dict("records")


def risks_triggered_by(risk_id: str, taxonomy: pd.DataFrame, vc2_df: pd.DataFrame, edges: pd.DataFrame) -> list[dict]:
    """Nhu risks_triggered_by_vc2 nhung bat dau tu 1 risk_id da co trong Risk Register
    (RR.xxxx) - tra qua VC2_ID (0. Danh muc rui ro) roi tra tiep nhu tren."""
    vc2_rows = taxonomy.loc[taxonomy["risk_id"] == risk_id, "vc2_id"]
    if vc2_rows.empty:
        return []
    return risks_triggered_by_vc2(vc2_rows.iloc[0], vc2_df, edges)


def get_rcm_risks(workbook_bytes: bytes) -> pd.DataFrame:
    """Ma tran kiem soat rui ro (sheet '7_RCM', header dong dau tien) - nguon rui ro THU 3, tach
    biet han risk_id RSK-xxx (Sheet1) va RR.xxxx (Risk Register): cot "Risk" o day la MO TA rui
    ro theo danh muc (vd "3.4.2. Quan ly chinh sach ban hang, chiet khau", ma "Risk_category_ID"
    = "RC-3.4"), khong phai 1 ma dinh danh rui ro. Gan theo cong ty (company_id: CADIVI/EMIC).
    Noi sang Sheet1 qua VC2_ID - da xac minh khop 16/16.

    ⚠️ Doc theo VI TRI COT (khong theo ten) vi sheet co nhieu cot TRUNG TEN nhau giua khoi
    kiem soat Entity Level va Transaction Level (vd 2 cot "Mo ta kiem soat", va ten cot danh gia
    "hieu luc" bi go thieu dau cach - "hiệu lựccủa" - khac "hiệu lực của" o ban Transaction, nen
    khong the dua vao ten cot on dinh). Mapping theo dung thu tu cot Excel nguoi dung da xac
    nhan (xem CLAUDE.md Muc 11.4): I-N = chi tiet kiem soat Entity Level, O-P = danh gia hieu
    luc/hieu qua Entity, R-W = chi tiet kiem soat Transaction Level, X-Y = danh gia hieu
    luc/hieu qua Transaction. Neu nguoi phu trach du lieu chen/xoa/doi thu tu cot tren
    SharePoint, mapping nay se doc sai ma KHONG bao loi - phai doi chieu lai truc tiep voi sheet
    that khi thay so lieu bat thuong.

    Sheet co dong lap y het nhau (vd 1 rui ro co ca kiem soat Entity lan Transaction se chiem 2
    dong tho) - drop_duplicates tren (company_id, vc2_id, risk_desc, risk_category_id) de con
    dung cac rui ro duy nhat.
    """
    df = _read_sheet(workbook_bytes, "7_RCM")
    out = pd.DataFrame({
        "company_id": df.iloc[:, 0], "vc1_name": df.iloc[:, 1], "vc1_id": df.iloc[:, 2],
        "vc2_name": df.iloc[:, 3], "vc2_id": df.iloc[:, 4],
        "risk_desc": df.iloc[:, 5], "risk_category_id": df.iloc[:, 6], "risk_details": df.iloc[:, 7],
        # Kiem soat cap Entity Level - cot I-N (chi tiet) + O-P (danh gia hieu luc/hieu qua)
        "ent_control_desc": df.iloc[:, 8], "ent_owner": df.iloc[:, 9], "ent_approval": df.iloc[:, 10],
        "ent_coverage": df.iloc[:, 11], "ent_quant": df.iloc[:, 12], "ent_frequency": df.iloc[:, 13],
        "ent_valid": df.iloc[:, 14], "ent_effective": df.iloc[:, 15],
        # Kiem soat cap Transaction Level - cot R-W (chi tiet) + X-Y (danh gia hieu luc/hieu qua)
        "tx_control_desc": df.iloc[:, 17], "tx_reviewer": df.iloc[:, 18], "tx_approver": df.iloc[:, 19],
        "tx_frequency": df.iloc[:, 20], "tx_form": df.iloc[:, 21], "tx_platform": df.iloc[:, 22],
        "tx_valid": df.iloc[:, 23], "tx_effective": df.iloc[:, 24],
    })
    out = out.dropna(subset=["vc2_id"])
    return out.drop_duplicates(subset=["company_id", "vc2_id", "risk_desc", "risk_category_id"])


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
