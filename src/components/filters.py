import pandas as pd
import streamlit as st


def _label_map(companies: pd.DataFrame) -> dict:
    return {
        str(r.company_id): f"{r.company_id} — {r.company_name}"
        for r in companies.itertuples()
        if pd.notna(r.company_id)
    }


def company_selector(
    companies: pd.DataFrame,
    available_ids: set,
    *,
    key: str = "selected_company",
    preferred: list[str] | None = None,
) -> str | None:
    """Selectbox 1 cong ty. Gia tri duoc luu trong st.session_state[key] nen se giu nguyen
    khi nguoi dung chuyen sang trang khac cung dung chung key nay. `preferred` (vd sap xep
    theo so dong du lieu giam dan) chi anh huong lua chon mac dinh lan dau, khong ep buoc
    khi da co lua chon truoc do."""
    options = companies["company_id"].dropna().astype(str).tolist()
    if not options:
        return None
    labels = _label_map(companies)

    def fmt(cid: str) -> str:
        base = labels.get(cid, cid)
        return base if cid in available_ids else f"{base}  ·  chưa có dữ liệu"

    if key not in st.session_state or st.session_state[key] not in options:
        candidates = [c for c in (preferred or []) if c in available_ids] + [
            c for c in options if c in available_ids
        ]
        st.session_state[key] = next(iter(candidates), options[0])

    return st.selectbox("Công ty", options, key=key, format_func=fmt)


def company_multiselector(
    companies: pd.DataFrame, available_ids: set, *, key: str = "selected_companies"
) -> list[str]:
    options = companies["company_id"].dropna().astype(str).tolist()
    labels = _label_map(companies)

    def fmt(cid: str) -> str:
        return labels.get(cid, cid)

    if key not in st.session_state:
        st.session_state[key] = [c for c in options if c in available_ids] or options

    return st.multiselect("Công ty", options, key=key, format_func=fmt)
