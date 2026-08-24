import streamlit as st

from src.components.risk_dialog import rcm_block_health_color, rcm_control_health_color, show_activity_risks
from src.data import loader, repository
from src.theme import chart_config, nz, risk_palette
from src.viz.value_chain import build_risk_by_function_bar_v2, build_value_chain_blocks

st.title("⛓️ Chuỗi giá trị")
st.caption(
    "Mô hình Chuỗi giá trị Porter chuẩn — **9 khối, dùng chung cho toàn Tập đoàn** (nguồn: Sheet1), "
    "không phân theo công ty. Hàng trên là 5 khối **hoạt động chính**, hàng dưới là 4 khối "
    "**hoạt động hỗ trợ**. Khối có màu (xanh/vàng/cam/đỏ) nếu có dữ liệu 7_RCM đánh giá kiểm "
    "soát — bấm vào để xem danh sách hoạt động (sub-value chain) bên trong, rồi bấm tiếp để "
    "xem chi tiết rủi ro — gộp từ **Sheet1** và **Ma trận kiểm soát rủi ro (7_RCM)**, luôn ghi "
    "rõ nguồn cho từng rủi ro."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

vc2 = repository.get_value_chain_v2(workbook_bytes)
taxonomy = repository.get_risk_taxonomy(workbook_bytes)
trigger_edges = repository.get_risk_trigger_edges(workbook_bytes)
rcm = repository.get_rcm_risks(workbook_bytes)

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
rcm_counts = rcm.groupby("vc2_id").size()
combined_counts = risk_counts.add(rcm_counts, fill_value=0).astype(int)

n_sheet1_risks = with_risk["risk_id"].nunique()
n_rcm_risks = len(rcm)
n_activities_with_risk = len(set(with_risk["vc2_id"]) | set(rcm["vc2_id"]))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Hoạt động", len(nodes))
k2.metric("Khối chức năng", nodes["vc1_name"].nunique())
k3.metric("Hoạt động có rủi ro", f"{n_activities_with_risk}/{len(nodes)}")
k4.metric("Tổng rủi ro", n_sheet1_risks + n_rcm_risks)
k4.caption(f"{n_sheet1_risks} từ Sheet1 · {n_rcm_risks} từ 7_RCM")

if not combined_counts.empty:
    vc2_to_vc1 = dict(nodes[["vc2_id", "vc1_name"]].itertuples(index=False))
    by_fn = combined_counts.groupby(lambda vc2_id: vc2_to_vc1.get(vc2_id, "—")).sum().sort_values(ascending=False)
    top_fn, top_n = by_fn.index[0], int(by_fn.iloc[0])
    with st.container(border=True):
        st.markdown("**Điểm cần chú ý**")
        st.markdown(f"⚠️ Khối **{top_fn}** tập trung nhiều rủi ro nhất ({top_n} rủi ro, gộp Sheet1 + 7_RCM) — điểm nóng cần ưu tiên rà soát.")

block_colors = {}
for vc1_id in nodes["vc1_id"].dropna().unique():
    color = rcm_block_health_color(vc1_id, rcm)
    if color:
        block_colors[vc1_id] = color

fig = build_value_chain_blocks(vc2, block_colors=block_colors)
fig.update_layout(height=300)
event = st.plotly_chart(
    fig, width="stretch", config=chart_config(),
    key="vc2_blocks", on_select="rerun", selection_mode="points",
)
palette = risk_palette()
st.caption("💡 Bấm vào một khối để xem danh sách hoạt động (sub-value chain) bên trong.")
st.caption(
    "Màu khối (nếu có) theo tổng số kiểm soát 7_RCM không hiệu lực & không hiệu quả trong "
    "TẤT CẢ hoạt động của khối: "
    f"<span style='color:{palette['none']}'>■ xanh</span> &lt;3 · "
    f"<span style='color:{palette['yellow']}'>■ vàng</span> ≥3 · "
    f"<span style='color:{palette['low']}'>■ cam</span> ≥5 · "
    f"<span style='color:{palette['high']}'>■ đỏ</span> ≥7 · khối chưa có dữ liệu 7_RCM giữ màu trung tính.",
    unsafe_allow_html=True,
)

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
        st.caption(
            "Màu mã hoạt động (nếu có) theo số kiểm soát 7_RCM không hiệu lực & không hiệu quả: "
            f"<span style='color:{palette['none']}'>■ xanh</span> &lt;3 · "
            f"<span style='color:{palette['yellow']}'>■ vàng</span> ≥3 · "
            f"<span style='color:{palette['low']}'>■ cam</span> ≥5 · "
            f"<span style='color:{palette['high']}'>■ đỏ</span> ≥7",
            unsafe_allow_html=True,
        )

        block_rows = nodes[(nodes["vc1_name"] == selected_block) & (nodes["category"].isin(categories))]
        if block_rows.empty:
            st.caption("Không có hoạt động nào khớp bộ lọc \"Nhóm hoạt động\" hiện tại trong khối này.")
        for _, r in block_rows.iterrows():
            count = int(combined_counts.get(r["vc2_id"], 0))
            color = palette["none"] if count == 0 else (palette["low"] if count == 1 else palette["high"])
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.1, 3.2, 1, 1.4])
                code_color = rcm_control_health_color(r["vc2_id"], rcm)
                if code_color:
                    c1.markdown(f"<code style='color:{code_color};font-weight:700'>{r['vc2_id']}</code>", unsafe_allow_html=True)
                else:
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
                        rcm_risks=rcm[rcm["vc2_id"] == r["vc2_id"]],
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
    activity_rcm = rcm[rcm["vc2_id"] == selected_node]
    with st.container(border=True):
        st.markdown(f"**{selected_node} — {nz(node_row.get('vc2_name'))}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Khối", nz(node_row.get("vc1_name")))
        c2.metric("Nhóm", nz(node_row.get("category")))
        c3.metric("Rủi ro liên kết", len(activity_risks) + len(activity_rcm))
        c3.caption(f"{len(activity_risks)} từ Sheet1 · {len(activity_rcm)} từ 7_RCM")

        st.caption("Từ Sheet1")
        if activity_risks.empty:
            st.caption("Chưa có rủi ro nào trong Sheet1 gắn với hoạt động này.")
        else:
            st.dataframe(
                activity_risks[["risk_id", "risk_name", "problem"]].rename(columns={
                    "risk_id": "Mã rủi ro", "risk_name": "Tên rủi ro", "problem": "Vấn đề",
                }),
                width="stretch", hide_index=True,
            )

        if not activity_rcm.empty:
            st.caption("Từ Ma trận kiểm soát rủi ro (7_RCM)")
            st.dataframe(
                activity_rcm[["company_id", "risk_desc", "risk_category_id"]].rename(columns={
                    "company_id": "Công ty", "risk_desc": "Rủi ro", "risk_category_id": "Mã danh mục",
                }),
                width="stretch", hide_index=True,
            )
