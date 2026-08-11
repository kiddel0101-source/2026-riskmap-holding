import streamlit as st

from src.data import loader, repository

st.title("🗺️ Risk Map — GELEX")
st.markdown(
    "Visual hoá chuỗi cung ứng, chuỗi giá trị và rủi ro của các công ty thành viên GELEX, "
    "lấy dữ liệu trực tiếp từ file `GELEX_Risk_Map_Database.xlsx` trên SharePoint "
    "(không lưu bản sao cục bộ — mỗi lần làm mới sẽ kéo lại đúng dữ liệu mới nhất)."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

st.caption(f"Dữ liệu mới nhất từ SharePoint lúc {fetched_at:%d/%m/%Y %H:%M}.")

companies = repository.get_companies(workbook_bytes)
value_chain = repository.get_value_chain(workbook_bytes)
supply_chain = repository.get_supply_chain(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
available_ids = repository.companies_with_data(companies, value_chain, supply_chain, risks)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Công ty", len(companies))
c2.metric("Công ty có dữ liệu", len(available_ids))
c3.metric("Tổng số rủi ro", len(risks))
red_count = int((risks["status_rag"] == "Red").sum()) if "status_rag" in risks.columns else 0
c4.metric("Rủi ro mức Red", red_count)

st.divider()
st.subheader("Đi tới")

p1, p2, p3 = st.columns(3)
with p1:
    st.page_link("pages/1_Chuoi_cung_ung.py", label="Chuỗi cung ứng", icon="🔗", width="stretch")
    st.caption("Mạng nhà cung cấp — công ty — khách hàng.")
with p2:
    st.page_link("pages/2_Chuoi_gia_tri.py", label="Chuỗi giá trị", icon="⛓️", width="stretch")
    st.caption("Dòng chảy hoạt động theo chuỗi giá trị từng công ty.")
with p3:
    st.page_link("pages/3_Danh_muc_rui_ro.py", label="Danh mục rủi ro", icon="🛑", width="stretch")
    st.caption("Bảng rủi ro, heatmap và risk migration.")

st.divider()
st.caption(
    "Phạm vi đợt này: 3 trang trên. KRI, Risk Appetite, RCM và trang Overview chi tiết để lại đợt sau."
)
