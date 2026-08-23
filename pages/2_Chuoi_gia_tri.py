import streamlit as st

from src.components.risk_dialog import show_activity_risks
from src.data import loader, repository
from src.theme import chart_config, nz, risk_palette
from src.viz.value_chain import build_risk_by_function_bar_v2, build_value_chain_blocks

st.title("⛓️ Chuỗi giá trị")
st.caption(
    "Mô hình Chuỗi giá trị Porter chuẩn — **9 khối, dùng chung cho toàn Tập đoàn** (nguồn: Sheet1), "
    "không phân theo công ty. Hàng trên là 5 khối **hoạt động chính**, hàng dưới là 4 khối "
    "**hoạt động hỗ trợ**. Mỗi khối là 1 ô trung tính — bấm vào để xem danh sách hoạt động "
    "(sub-value chain) bên trong, rồi bấm tiếp để xem chi tiết rủi ro."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

vc2 = repository.get_value_chain_v2(workbook_bytes)
taxonomy = repository.get_risk_taxonomy(workbook_bytes)
trigger_edges = repository.get_risk_trigger_edges(workbook_bytes)

if vc2.empty:
    st.info("Chưa có dữ liệu Chuỗi giá trị.")
    st.stop()

categories = set(
    st.multiselect(
        "Nhóm hoạt động (áp dụng cho danh sách hoạt động khi bấm vào 1 khối)",
        ["Chính", "Hỗ trợ"], default=["Chính", "Hỗ trợ"], key="vc2_categories",
    )
) or {"Chính", "Hỗ trợ"}

nodes = vc2.drop_duplicates(subset=["vc2_id"])
with_risk = vc2.dropna(subset=["risk_id"])
risk_counts = with_risk.groupby("vc2_id")["risk_id"].nunique()
n_activities_with_risk = with_risk["vc2_id"].nunique()
n_risks = with_risk["risk_id"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Hoạt động", len(nodes))
k2.metric("Khối chức năng", nodes["vc1_name"].nunique())
k3.metric("Hoạt động có rủi ro", f"{n_activities_with_risk}/{len(nodes)}")
k4.metric("Tổng rủi ro", n_risks)

if not with_risk.empty:
    by_fn = with_risk.groupby("vc1_name")["risk_id"].nunique().sort_values(ascending=False)
    top_fn, top_n = by_fn.index[0], int(by_fn.iloc[0])
    with st.container(border=True):
        st.markdown("**Điểm cần chú ý**")
        st.markdown(f"⚠️ Khối **{top_fn}** tập trung nhiều rủi ro nhất ({top_n} rủi ro) — điểm nóng cần ưu tiên rà soát.")

fig = build_value_chain_blocks(vc2)
fig.update_layout(height=300)
event = st.plotly_chart(
    fig, width="stretch", config=chart_config(),
    key="vc2_blocks", on_select="rerun", selection_mode="points",
)
st.caption("💡 Bấm vào một khối để xem danh sách hoạt động (sub-value chain) bên trong.")

clicked_points = (event or {}).get("selection", {}).get("points", [])
if clicked_points:
    clicked_block = clicked_points[0].get("customdata")
    if clicked_block and clicked_block != st.session_state.get("_vc2_block_ack"):
        st.session_state["_vc2_block_ack"] = clicked_block
        st.session_state["_vc2_selected_block"] = clicked_block

selected_block = st.session_state.get("_vc2_selected_block")
if selected_block:
    palette = risk_palette()
    with st.container(border=True):
        head_l, head_r = st.columns([5, 1])
        head_l.subheader(f"Hoạt động trong khối: {selected_block}")
        if head_r.button("✕ Đóng", key="close_block_panel"):
            st.session_state["_vc2_selected_block"] = None
            st.rerun()

        block_rows = nodes[(nodes["vc1_name"] == selected_block) & (nodes["category"].isin(categories))]
        if block_rows.empty:
            st.caption("Không có hoạt động nào khớp bộ lọc \"Nhóm hoạt động\" hiện tại trong khối này.")
        for _, r in block_rows.iterrows():
            count = int(risk_counts.get(r["vc2_id"], 0))
            color = palette["none"] if count == 0 else (palette["low"] if count == 1 else palette["high"])
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.1, 3.2, 1, 1.4])
                c1.markdown(f"`{r['vc2_id']}`")
                c2.write(nz(r.get("vc2_name")))
                c3.caption(nz(r.get("category")))
                label = f"{count} rủi ro" if count else "chưa có rủi ro"
                c4.markdown(f"<span style='color:{color};font-weight:600;font-size:0.85rem'>{label}</span>", unsafe_allow_html=True)
                if count and st.button("Xem rủi ro", key=f"view_risk_{r['vc2_id']}"):
                    show_activity_risks(
                        vc2[vc2["vc2_id"] == r["vc2_id"]],
                        f"{r['vc2_id']} — {nz(r.get('vc2_name'), '')}",
                        f"{nz(r.get('vc1_name'))} · {nz(r.get('category'))}",
                        edges=trigger_edges,
                    )

st.info(
    "ℹ️ Sheet1 không có cột thể hiện hoạt động nào nối tiếp hoạt động nào, nên bản đồ này "
    "**không vẽ mũi tên luồng quy trình**. Cấu trúc được thể hiện đúng theo những gì file "
    "cung cấp: nhóm theo khối chức năng và phân loại Chính/Hỗ trợ."
)

st.divider()

col_bar, col_detail = st.columns([1, 1.3])

with col_bar:
    st.subheader("Rủi ro theo khối chức năng")
    bar = build_risk_by_function_bar_v2(vc2)
    if bar is not None:
        bar.update_layout(height=max(260, 34 * nodes["vc1_name"].nunique() + 90))
        st.plotly_chart(bar, width="stretch", config=chart_config())
    st.caption("Khối có nhiều rủi ro nhất là điểm nóng nên ưu tiên rà soát kiểm soát.")

with col_detail:
    st.subheader("Chi tiết hoạt động")
    rows = nodes[nodes["category"].isin(categories)].reset_index(drop=True)
    node_labels = {r.vc2_id: f"{r.vc2_id} — {nz(r.vc2_name, '')}" for r in rows.itertuples()}
    selected_node = st.selectbox(
        "Chọn hoạt động", rows["vc2_id"].tolist(),
        format_func=lambda n: node_labels.get(n, n), key="vc2_selected_node",
    )
    node_row = rows[rows["vc2_id"] == selected_node].iloc[0]
    activity_risks = vc2[vc2["vc2_id"] == selected_node].dropna(subset=["risk_id"])
    with st.container(border=True):
        st.markdown(f"**{selected_node} — {nz(node_row.get('vc2_name'))}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Khối", nz(node_row.get("vc1_name")))
        c2.metric("Nhóm", nz(node_row.get("category")))
        c3.metric("Rủi ro liên kết", len(activity_risks))

        if activity_risks.empty:
            st.caption("Chưa có rủi ro nào gắn với hoạt động này.")
        else:
            st.dataframe(
                activity_risks[["risk_id", "risk_name", "problem"]].rename(columns={
                    "risk_id": "Mã rủi ro", "risk_name": "Tên rủi ro", "problem": "Vấn đề",
                }),
                width="stretch", hide_index=True,
            )
