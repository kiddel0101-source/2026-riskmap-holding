import math

import streamlit as st

from src.components.risk_dialog import rcm_block_health_color, rcm_group_health_color, show_activity_risks
from src.data import loader, repository
from src.theme import chart_config, nz, risk_palette
from src.viz.value_chain import build_risk_by_function_bar_v2


def _uniform_name_height(names, chars_per_line: int) -> str:
    """Uoc luong chieu cao (em) DU cho ten DAI NHAT trong 1 luoi o, ap dung CHUNG cho moi o
    trong luoi do - Streamlit khong tu can bang chieu cao giua cac cot doc lap trong
    st.columns() (moi cot cao theo dung noi dung rieng no), nen ten ngan/dai khac nhau lam
    cac o lech chieu cao, nut bam khong thang hang. `chars_per_line` la uoc luong tho (khong
    do font that) - can chinh lai neu doi font-size/so cot."""
    lines = [max(1, math.ceil(len(n) / chars_per_line)) for n in names if n]
    max_lines = min(max(lines, default=1), 4)  # tran o 4 dong, tranh 1 ten qua dai keo ca luoi
    return f"{max_lines * 1.3}em"

st.title("⛓️ Chuỗi giá trị")
st.caption(
    "Mô hình Chuỗi giá trị Porter chuẩn — **9 khối, dùng chung cho toàn Tập đoàn** (nguồn: "
    "2_VC_Master), không phân theo công ty. Hàng trên là 5 khối **hoạt động chính**, hàng dưới "
    "là 4 khối **hoạt động hỗ trợ**. Khối có màu (xanh/vàng/cam/đỏ) nếu có dữ liệu Ma trận "
    "kiểm soát rủi ro (CADIVI_RCM) — bấm vào 1 khối để xem lưới nhóm hoạt động (VC2) ngay bên "
    "dưới, rồi bấm 1 nhóm để xem danh sách hoạt động cụ thể và chi tiết rủi ro Sheet1."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

vc2 = repository.get_value_chain_v2(workbook_bytes)
rcm = repository.get_rcm_risks(workbook_bytes)

if vc2.empty:
    st.info("Chưa có dữ liệu Chuỗi giá trị.")
    st.stop()

categories = set(
    st.multiselect(
        "Nhóm hoạt động (áp dụng cho danh sách nhóm/hoạt động khi bấm vào 1 khối)",
        ["Chính", "Hỗ trợ"], default=["Chính", "Hỗ trợ"], key="vc2_categories",
    )
) or {"Chính", "Hỗ trợ"}

nodes = vc2.drop_duplicates(subset=["vc2_id"])
with_risk = vc2.dropna(subset=["risk_id"])
risk_counts = with_risk.groupby("vc2_id")["risk_id"].nunique()

n_sheet1_risks = with_risk["risk_id"].nunique()
n_rcm_risks = len(rcm)
# CADIVI_RCM gan rui ro o cap NHOM NHO (vc1_id/vc2_id cua no), khong phai cap hoat dong cu the
# (VC3) nhu app dang hien thi chi tiet - nguoi dung da xac nhan CHUA gan xuong duoc toi hoat
# dong cu the (xem CLAUDE.md Muc 11.4), nen "Hoat dong co rui ro" chi tinh theo Sheet1.
n_activities_with_risk = with_risk["vc2_id"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Hoạt động", len(nodes))
k2.metric("Khối chức năng", nodes["vc1_name"].nunique())
k3.metric("Hoạt động có rủi ro", f"{n_activities_with_risk}/{len(nodes)}")
k3.caption("Chỉ tính rủi ro Sheet1 — CADIVI_RCM chưa gắn được xuống từng hoạt động cụ thể.")
k4.metric("Tổng rủi ro", n_sheet1_risks + n_rcm_risks)
k4.caption(f"{n_sheet1_risks} từ Sheet1 · {n_rcm_risks} từ CADIVI_RCM (theo khối/nhóm)")

vc2_to_vc1_id = dict(nodes[["vc2_id", "vc1_id"]].itertuples(index=False))
vc1_id_to_name = dict(nodes[["vc1_id", "vc1_name"]].itertuples(index=False))
sheet1_by_block = risk_counts.groupby(lambda vc2_id: vc2_to_vc1_id.get(vc2_id, "—")).sum()
rcm_by_block = rcm.groupby("vc1_id").size()
combined_by_block = sheet1_by_block.add(rcm_by_block, fill_value=0)
if not combined_by_block.empty:
    top_id = combined_by_block.sort_values(ascending=False).index[0]
    top_n = int(combined_by_block.max())
    top_name = vc1_id_to_name.get(top_id, top_id)
    with st.container(border=True):
        st.markdown("**Điểm cần chú ý**")
        st.markdown(f"⚠️ Khối **{top_name}** tập trung nhiều rủi ro nhất ({top_n} rủi ro, gộp Sheet1 + CADIVI_RCM) — điểm nóng cần ưu tiên rà soát.")

block_colors = {}
for vc1_id in nodes["vc1_id"].dropna().unique():
    color = rcm_block_health_color(vc1_id, rcm)
    if color:
        block_colors[vc1_id] = color

counts_by_vc1 = nodes.groupby("vc1_id").size()
bands = repository.vc1_bands(nodes["vc1_id"].dropna().unique())

palette = risk_palette()
st.caption("💡 Bấm vào một khối để xem lưới nhóm hoạt động (VC2) ngay bên dưới.")
st.caption(
    "Màu khối/nhóm (nếu có) theo tổng số kiểm soát CADIVI_RCM không hiệu lực & không hiệu quả: "
    f"<span style='color:{palette['none']}'>■ xanh</span> &lt;3 · "
    f"<span style='color:{palette['yellow']}'>■ vàng</span> ≥3 · "
    f"<span style='color:{palette['low']}'>■ cam</span> ≥5 · "
    f"<span style='color:{palette['high']}'>■ đỏ</span> ≥7 · chưa có dữ liệu CADIVI_RCM giữ màu trung tính.",
    unsafe_allow_html=True,
)

GROUP_COLS = 4
selected_block_id = st.session_state.get("_vc2_selected_block_id")
selected_group = st.session_state.get("_vc2_selected_group")


def _render_block_expansion(vc1_id: str) -> None:
    fn = vc1_id_to_name.get(vc1_id, vc1_id)
    with st.container(border=True):
        head_l, head_r = st.columns([5, 1])
        head_l.subheader(f"Nhóm hoạt động trong khối: {fn}")
        if head_r.button("✕ Đóng", key="close_block_panel"):
            st.session_state["_vc2_selected_block_id"] = None
            st.session_state["_vc2_selected_group"] = None
            st.rerun()
        st.caption(
            "ℹ️ Số rủi ro Sheet1 dưới đây tính theo hoạt động cụ thể (VC3); màu ô nhóm (VC2) "
            "dưới đây theo dữ liệu Ma trận kiểm soát rủi ro (CADIVI_RCM) — khớp đúng cấp này."
        )

        block_rows = nodes[(nodes["vc1_id"] == vc1_id) & (nodes["category"].isin(categories))]
        if block_rows.empty:
            st.caption("Không có nhóm nào khớp bộ lọc \"Nhóm hoạt động\" hiện tại trong khối này.")

        group_rows = block_rows.drop_duplicates(subset=["group_id"]).sort_values("group_id")
        group_counts = block_rows.groupby("group_id")["vc2_id"].nunique()
        group_list = group_rows["group_id"].tolist()

        group_sheet1_risk = block_rows.assign(
            _n=block_rows["vc2_id"].map(risk_counts).fillna(0)
        ).groupby("group_id")["_n"].sum()
        group_rcm_risk = rcm.groupby("vc2_id").size()
        group_name_height = _uniform_name_height(group_rows["group_name"].fillna("").tolist(), chars_per_line=20)

        for i in range(0, len(group_list), GROUP_COLS):
            cols = st.columns(GROUP_COLS)
            for col, (_, g) in zip(cols, group_rows.iloc[i:i + GROUP_COLS].iterrows()):
                with col:
                    g_color = rcm_group_health_color(g["group_id"], rcm)
                    n_act = int(group_counts.get(g["group_id"], 0))
                    n_risk = int(group_sheet1_risk.get(g["group_id"], 0) + group_rcm_risk.get(g["group_id"], 0))
                    is_selected = selected_group == g["group_id"]
                    with st.container(border=True):
                        name_style = f"color:{g_color};" if g_color else ""
                        st.markdown(
                            f"<div style='font-size:0.8rem;font-weight:600;min-height:{group_name_height};{name_style}'>{nz(g.get('group_name'))}</div>",
                            unsafe_allow_html=True,
                        )
                        st.caption(f"{g['group_id']} · {n_act} hoạt động")
                        risk_style = f"color:{palette['low']};font-weight:600;" if n_risk else f"color:{palette['grey']};"
                        st.markdown(
                            f"<div style='font-size:0.72rem;{risk_style}margin-top:-6px;margin-bottom:6px'>{n_risk} rủi ro</div>",
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "✓ Đang chọn" if is_selected else "Chọn nhóm",
                            key=f"group_{g['group_id']}", disabled=is_selected, width="stretch",
                        ):
                            st.session_state["_vc2_selected_group"] = g["group_id"]
                            st.rerun()

        if selected_group and selected_group in group_list:
            group_label = group_rows.loc[group_rows["group_id"] == selected_group, "group_name"].iloc[0]
            st.divider()
            st.markdown(f"**Hoạt động trong nhóm: {nz(group_label)}**")
            vc3_rows = block_rows[block_rows["group_id"] == selected_group]
            for _, r in vc3_rows.iterrows():
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
                            f"{fn} · {nz(r.get('category'))}",
                        )


for band_label, ids in bands:
    st.markdown(f"**{band_label}**")
    band_name_height = _uniform_name_height(
        [vc1_id_to_name.get(vc1_id, vc1_id).upper() for vc1_id in ids], chars_per_line=16,
    )
    cols = st.columns(len(ids))
    for col, vc1_id in zip(cols, ids):
        with col:
            fn = vc1_id_to_name.get(vc1_id, vc1_id)
            n_act = int(counts_by_vc1.get(vc1_id, 0))
            n_risk = int(combined_by_block.get(vc1_id, 0))
            color = block_colors.get(vc1_id)
            is_active = selected_block_id == vc1_id
            with st.container(border=True):
                name_style = f"color:{color};" if color else ""
                st.markdown(
                    f"<div style='font-size:0.82rem;font-weight:700;min-height:{band_name_height};{name_style}'>{fn.upper()}</div>",
                    unsafe_allow_html=True,
                )
                st.caption(f"{n_act} hoạt động")
                risk_style = f"color:{palette['low']};font-weight:600;" if n_risk else f"color:{palette['grey']};"
                st.markdown(
                    f"<div style='font-size:0.75rem;{risk_style}margin-top:-8px'>{n_risk} rủi ro</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "✓ Đang chọn" if is_active else "Chọn khối",
                    key=f"block_{vc1_id}", disabled=is_active, width="stretch",
                ):
                    st.session_state["_vc2_selected_block_id"] = vc1_id
                    st.session_state["_vc2_selected_group"] = None
                    st.rerun()

    if selected_block_id in ids:
        _render_block_expansion(selected_block_id)

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
        c3.metric("Rủi ro liên kết (Sheet1)", len(activity_risks))

        if activity_risks.empty:
            st.caption("Chưa có rủi ro nào gắn với hoạt động này.")
        else:
            st.dataframe(
                activity_risks[["risk_id", "risk_name", "problem"]].rename(columns={
                    "risk_id": "Mã rủi ro", "risk_name": "Tên rủi ro", "problem": "Vấn đề",
                }),
                width="stretch", hide_index=True,
            )
