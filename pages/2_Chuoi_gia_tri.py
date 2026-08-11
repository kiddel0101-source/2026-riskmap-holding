import pandas as pd
import streamlit as st

from src import insights
from src.components.filters import company_selector
from src.config import vi
from src.data import loader, repository
from src.theme import chart_config, nz
from src.viz.value_chain import build_risk_by_function_bar, build_value_chain_map

st.title("⛓️ Chuỗi giá trị")
st.caption(
    "Bản đồ hoạt động theo từng khối chức năng. Mỗi ô là một hoạt động, màu theo số rủi ro đang gắn: "
    "**xanh** = chưa có, **cam** = 1, **đỏ** = từ 2 trở lên. Viền liền = hoạt động chính (Primary), "
    "viền chấm = hoạt động hỗ trợ (Support). Di chuột lên ô để xem mô tả và ghi chú phụ thuộc."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

companies = repository.get_companies(workbook_bytes)
value_chain = repository.get_value_chain(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
available_ids = repository.companies_in(value_chain, companies, ["company_id"])
risk_counts = repository.risk_counts_by_node(risks)
risks_exploded = repository.risks_exploded_by_vc_node(risks)
preferred = value_chain["company_id"].value_counts().index.tolist()

col_filter, col_cat, col_height = st.columns([2.4, 1.6, 1])
with col_filter:
    company_id = company_selector(companies, available_ids, key="selected_company", preferred=preferred)
with col_cat:
    categories = set(
        st.multiselect(
            "Nhóm hoạt động", ["Primary", "Support"], default=["Primary", "Support"], key="vc_categories"
        )
    ) or {"Primary", "Support"}
with col_height:
    height = st.slider("Chiều cao biểu đồ", 320, 900, 520, step=20, key="vc_chart_height")

if company_id is None:
    st.info("Chưa có dữ liệu công ty.")
    st.stop()

nodes = value_chain[value_chain["company_id"] == company_id]
if nodes.empty:
    có_dữ_liệu = ", ".join(sorted(available_ids)) or "chưa có công ty nào"
    st.info(
        f"Chưa có dữ liệu chuỗi giá trị cho **{company_id}**. "
        f"Hiện chỉ các công ty sau đã khai báo chuỗi giá trị: **{có_dữ_liệu}** — "
        "chọn lại ở ô *Công ty* phía trên."
    )
    st.stop()

covered = risks_exploded.merge(nodes[["vc_node_id"]], on="vc_node_id")["vc_node_id"].nunique()
n_risks = risks_exploded.merge(nodes[["vc_node_id"]], on="vc_node_id")["risk_id"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Hoạt động", len(nodes))
k2.metric("Khối chức năng", nodes["vc_function"].nunique())
k3.metric("Hoạt động đã gắn rủi ro", f"{covered}/{len(nodes)}")
k4.metric("Rủi ro liên quan", n_risks)

insights.render(insights.value_chain_hotspots(value_chain, risks, company_id), st)

fig = build_value_chain_map(value_chain, risk_counts, company_id, categories=categories)
if fig is None:
    st.info("Không có hoạt động nào khớp bộ lọc hiện tại.")
else:
    fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", config=chart_config())

st.info(
    "ℹ️ Dữ liệu nguồn không có cột thể hiện hoạt động nào nối tiếp hoạt động nào, "
    "nên bản đồ này **không vẽ mũi tên luồng quy trình**. Cấu trúc được thể hiện đúng theo "
    "những gì file cung cấp: nhóm theo khối chức năng và phân loại Primary/Support."
)

st.divider()

col_bar, col_detail = st.columns([1, 1.3])

with col_bar:
    st.subheader("Rủi ro theo khối chức năng")
    bar = build_risk_by_function_bar(value_chain, risks_exploded, company_id)
    if bar is not None:
        bar.update_layout(height=max(260, 34 * nodes["vc_function"].nunique() + 90))
        st.plotly_chart(bar, width="stretch", config=chart_config())
    st.caption("Khối có nhiều rủi ro nhất là điểm nóng nên ưu tiên rà soát kiểm soát.")

with col_detail:
    st.subheader("Chi tiết hoạt động")
    rows = nodes[nodes["vc_category"].isin(categories)].reset_index(drop=True)
    node_labels = {r.vc_node_id: f"{r.vc_node_id} — {nz(r.vc_sub_function, '')}" for r in rows.itertuples()}
    selected_node = st.selectbox(
        "Chọn hoạt động", rows["vc_node_id"].tolist(),
        format_func=lambda n: node_labels.get(n, n), key="vc_selected_node",
    )
    node_row = rows[rows["vc_node_id"] == selected_node].iloc[0]
    with st.container(border=True):
        st.markdown(f"**{selected_node} — {nz(node_row.get('vc_sub_function'), '')}**")
        st.write(nz(node_row.get("activity_description")))
        c1, c2, c3 = st.columns(3)
        c1.metric("Chủ trì", nz(node_row.get("process_owner")))
        c2.metric("Nhóm", nz(node_row.get("vc_category")))
        c3.metric("Rủi ro liên kết", int(risk_counts.get(selected_node, 0)))
        if pd.notna(node_row.get("dependency_note")):
            st.warning(f"Phụ thuộc: {node_row['dependency_note']}")

        linked_risks = repository.risks_for_node(risks, selected_node)
        if linked_risks.empty:
            st.caption("Chưa có rủi ro nào gắn với hoạt động này.")
        else:
            st.dataframe(
                vi(linked_risks[["risk_id", "risk_category_l1", "risk_event_l3", "status_rag"]]),
                width="stretch", hide_index=True,
            )
