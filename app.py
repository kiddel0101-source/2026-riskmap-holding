import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.data import loader

st.set_page_config(page_title="Risk Map GELEX", page_icon="🗺️", layout="wide")

pages = [
    st.Page("pages/0_Trang_chu.py", title="Trang chủ", icon="🗺️", default=True),
    st.Page("pages/1_Chuoi_cung_ung.py", title="Chuỗi cung ứng", icon="🔗"),
    st.Page("pages/2_Chuoi_gia_tri.py", title="Chuỗi giá trị", icon="⛓️"),
    st.Page("pages/3_Danh_muc_rui_ro.py", title="Danh mục rủi ro", icon="🛑"),
]
pg = st.navigation(pages)

with st.sidebar:
    st.caption("RISK MAP · GELEX")
    if st.button("🔄 Làm mới dữ liệu", width="stretch"):
        loader.refresh_workbook()
        st.rerun()

pg.run()
