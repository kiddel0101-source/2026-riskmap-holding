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


# Thu tu 9 khoi Porter day du cho trang Chuoi gia tri, phan loai theo MA khoi (vc1_id) chu
# KHONG theo ten hien thi (vc1_name) - ten hien thi tren SharePoint da bi doi it nhat 3 lan
# ("Vận hành / Sản xuất" -> "Sản xuất", "Marketing & Bán hàng" -> "Bán hàng", "Thu mua" ->
# "Mua hàng"...) trong khi ma (IL/OP/OL/MS/SV/PR/TD/FI/HR, cung la tien to cua vc2_id nhu
# "OP-001") on dinh qua tat ca cac lan doi ten.
VC1_ID_ORDER = ["IL", "OP", "OL", "MS", "SV", "PR", "TD", "FI", "HR"]
# 5 ma CHINH (Primary) + 4 ma HO TRO (Support) theo dung khung Porter - day la phan loai o CAP
# KHOI, khac voi cot "category" (Phan loai Chinh/Ho tro) trong tung dong du lieu von la phan
# loai o CAP HOAT DONG (vd hoat dong "PR-003" thuoc khoi Ho tro "Mua hàng" nhung ban than no
# van co the duoc gan category="Hỗ trợ" trong du lieu - 2 truc doc lap nhau).
VC1_PRIMARY_IDS = set(VC1_ID_ORDER[:5])


def vc1_bands(vc1_ids) -> list[tuple[str, list[str]]]:
    """Chia danh sach ma khoi (vc1_id) thanh 2 "band" theo khung Porter: [("HOẠT ĐỘNG CHÍNH",
    [...]), ("HOẠT ĐỘNG HỖ TRỢ", [...])], moi band da sap xep dung thu tu VC1_ID_ORDER. Ma nao
    khong khop danh sach Chinh (ke ca ma la vd "KHÁC" du phong) deu xep vao Ho tro, tranh bi
    RUNG mat khoi giao dien neu du lieu nguon phat sinh ma khoi moi. Dung chung cho trang
    Chuoi gia tri (luoi khoi Streamlit) va bar chart rui ro theo khoi."""
    order_index = {code: i for i, code in enumerate(VC1_ID_ORDER)}
    all_ids = list(dict.fromkeys(vc1_ids))
    primary = sorted(
        [i for i in all_ids if i in VC1_PRIMARY_IDS],
        key=lambda code: order_index.get(code, len(VC1_ID_ORDER)),
    )
    support = sorted(
        [i for i in all_ids if i not in VC1_PRIMARY_IDS],
        key=lambda code: order_index.get(code, len(VC1_ID_ORDER)),
    )
    bands = []
    if primary:
        bands.append(("HOẠT ĐỘNG CHÍNH", primary))
    if support:
        bands.append(("HOẠT ĐỘNG HỖ TRỢ", support))
    return bands


def get_companies(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "1_Company_Master")


def get_supply_chain(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "3_Supply_Chain_Master")


def get_risks(workbook_bytes: bytes) -> pd.DataFrame:
    return _read_sheet(workbook_bytes, "4_Risk_Register")


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


def get_value_chain_v2(workbook_bytes: bytes) -> pd.DataFrame:
    """Mo hinh Chuoi gia tri Porter DAY DU 9 khoi (sheet '2_VC_Master', ten cu la "Sheet1" -
    da doi ten tren SharePoint, xem CLAUDE.md Muc 11.3) dung chung cho toan Tap doan GELEX -
    KHONG co cot cong ty. Day la nguon DUY NHAT cho mo hinh Chuoi gia tri trong app - sheet
    "2_Value_Chain_Master" (mo hinh CU theo cong ty, truoc day dung o Trang chu + Su kien rui
    ro) da bi xoa khoi workbook nguon, khong co sheet thay the, tinh nang phu thuoc no da bi
    go bo (xem CLAUDE.md Muc 11.5).

    1 dong = 1 (hoat dong, rui ro) - 1 hoat dong (vc2_id) co the lap lai nhieu dong neu co
    nhieu rui ro gan truc tiep (toi da 3), cot rui ro se rong o cac hoat dong chua co rui ro.

    ⚠️ Sheet nay dang duoc nguoi phu trach du lieu chinh sua truc tiep tren SharePoint - da
    nhieu lan doi ten cot goc (vd "Chuoi gia tri 1" -> "Value Chain"). Rename map o day chap
    nhan CA ten cu/moi cho tung cot de giam rui ro vo lai khi ho doi tiep.

    Sheet co 3 cap phan cap: VC1 (khoi, vd "IL") -> VC2 "Value Chain L2" (nhom nho, vd
    "IL-01") -> VC3 "Value Chain L3" (hoat dong cu the, vd "IL-011") - ca 3 cap nay HIEN DA
    DAY DU (187/187 dong, khong con thua nhu truoc). App van dung khai niem "vc2_id"/
    "vc2_name" cho CAP HOAT DONG CU THE NHAT (tuc la lay tu VC3_ID/Value Chain L3, KHONG
    phai VC2_ID/Value Chain L2 - 2 ten nay de gay nham vi trung voi khai niem vc2_id cua app)
    - chon qua `_first_non_empty_column()` de tu dong uu tien cot co du lieu that, phong khi
    cau truc doi tiep.

    Cap "Value Chain L2"/VC2_ID (nhom nho) tra ve qua `group_id`/`group_name` (xem CLAUDE.md
    Muc 11.6) - dung ten KHAC han "vc2_id"/"vc2_name" (da la ten co san cho cap VC3) de tranh
    nham lan. Trang Chuoi gia tri dung cap nay lam 1 tang trung gian giua khoi (VC1) va hoat
    dong cu the (VC3) khi bam vao 1 khoi.
    """
    df = _read_sheet(workbook_bytes, "2_VC_Master")
    out = df.rename(columns={
        "Chuỗi giá trị 1": "vc1_name", "Value Chain": "vc1_name", "VC1_ID": "vc1_id",
        "Phân loại": "category", "Value chain_3": "vc3_name",
        "Risk": "risk_name", "Risk_ID": "risk_id",
        "Problem": "problem", "Details": "details",
    })
    out["vc2_id"] = _first_non_empty_column(df, ["VC3_ID", "VC2_ID"])
    out["vc2_name"] = _first_non_empty_column(df, ["Value Chain L3", "Sub-Value Chain", "Chuỗi giá trị 2"])
    out["group_id"] = df["VC2_ID"] if "VC2_ID" in df.columns else None
    out["group_name"] = df["Value Chain L2"] if "Value Chain L2" in df.columns else None
    return out


def _first_non_empty_column(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """Tra ve cot dau tien trong danh sach CO DU LIEU THAT (khong rong hoan toan). Dung cho
    cac truong hop Sheet1 doi ten cot nhung van GIU LAI cot cu rong lam vet tich - khong the
    chi dua vao "cot co ton tai trong sheet" nhu cach rename() thong thuong, phai kiem tra co
    du lieu that hay khong moi chon."""
    for name in candidates:
        if name in df.columns and df[name].notna().any():
            return df[name]
    for name in candidates:
        if name in df.columns:
            return df[name]
    return pd.Series([None] * len(df), index=df.index)


def get_rcm_risks(workbook_bytes: bytes) -> pd.DataFrame:
    """Ma tran kiem soat rui ro (sheet 'CADIVI_RCM', ten cu la "7_RCM" - da doi ten VA tach
    rieng theo cong ty tren SharePoint, hien CHI co CADIVI, xem CLAUDE.md Muc 11.4) - nguon rui
    ro THU 3, tach biet han risk_id RSK-xxx (2_VC_Master) va RR.xxxx (Risk Register): cot
    "Risk" o day la MO TA rui ro theo danh muc (vd "3.4.2. Quan ly chinh sach ban hang, chiet
    khau", ma "Risk_category_ID" = "RC-3.4"), khong phai 1 ma dinh danh rui ro.

    ⚠️ QUAN TRONG - "vc2_id" o day la MA CAP NHOM NHO ("Value Chain L2" cua 2_VC_Master, vd
    "FI-02"), KHONG PHAI ma hoat dong cu the (VC3, vd "FI-021") ma pages/2_Chuoi_gia_tri.py
    dang hien thi chi tiet - da kiem tra truc tiep: 0/10 ma trong CADIVI_RCM khop voi VC3_ID,
    10/10 khop voi VC2_ID cua 2_VC_Master. 1 nhom VC2 co the co NHIEU hoat dong VC3 con (vd
    nhom "PR-01" co 5 hoat dong con) - da hoi nguoi dung, CHUA can gan rui ro nay xuong tung
    hoat dong VC3 cu the (chi gan o cap nhom/khoi). VI VAY: cho nao dang so khop "vc2_id" cua
    ham nay voi "vc2_id" cua get_value_chain_v2() (cap VC3) se KHONG BAO GIO khop - dung y,
    KHONG phai loi - chi dung duoc o cap KHOI (vc1_id, xem rcm_block_health_color) cho toi khi
    co quyet dinh khac.

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
    df = _read_sheet(workbook_bytes, "CADIVI_RCM")
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
    companies: pd.DataFrame, supply_chain: pd.DataFrame, risks: pd.DataFrame
) -> set[str]:
    """Cong ty co du lieu o BAT KY sheet nao (hop cua 2 nguon) - dung cho KPI tong quan o
    trang chu. Cac trang rieng le nen dung companies_in() voi cot phu hop hon.

    ⚠️ Truoc day gop them ca "2_Value_Chain_Master" - sheet do da bi xoa khoi workbook
    nguon, khong co sheet thay the (xem CLAUDE.md Muc 11.5), da bo tham so nay."""
    return (
        companies_in(risks, companies, ["company_id"])
        | companies_in(supply_chain, companies, ["upstream_entity_id", "downstream_entity_id"])
    )
