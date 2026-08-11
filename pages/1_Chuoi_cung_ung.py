import pandas as pd
import streamlit as st

from src import insights
from src.components.filters import company_selector
from src.config import vi
from src.data import loader, repository
from src.theme import chart_config
from src.viz.supply_chain import build_group_supply_map, build_supply_chain_network

st.title("🔗 Chuỗi cung ứng")

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

companies = repository.get_companies(workbook_bytes)
supply_chain = repository.get_supply_chain(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
risk_counts_sc = repository.risk_counts_by_sc_link(risks)
available_ids = repository.companies_in(
    supply_chain, companies, ["upstream_entity_id", "downstream_entity_id"]
)

view = st.radio(
    "Phạm vi", ["Theo công ty", "Toàn hệ thống"], horizontal=True, key="sc_view", label_visibility="collapsed"
)

shared = insights.shared_upstream_entities(supply_chain, companies)

# ---------------------------------------------------------------- toàn hệ thống
if view == "Toàn hệ thống":
    st.caption(
        "Gộp toàn bộ công ty thành viên vào một sơ đồ để lộ ra các đối tác thượng nguồn "
        "**dùng chung cho nhiều công ty** — rủi ro tập trung cấp tập đoàn mà sơ đồ theo "
        "từng công ty riêng lẻ không thể hiện được."
    )

    if shared.empty:
        st.info("Chưa phát hiện đối tác thượng nguồn nào phục vụ từ 2 công ty thành viên trở lên.")
    else:
        for _, r in shared.iterrows():
            st.warning(
                f"**{r['upstream_entity_id']}** cung cấp cho **{r['so_cong_ty']} công ty** "
                f"({r['cong_ty']}) — {r['dau_vao']}."
                + ("  Cả hai bên đều đánh giá **khó thay thế**." if r["kho_thay_the"] else "")
            )

    height = st.slider("Chiều cao biểu đồ", 400, 1000, 560, step=20, key="sc_group_height")
    fig = build_group_supply_map(supply_chain, companies, shared)
    if fig is None:
        st.info("Chưa có dữ liệu chuỗi cung ứng.")
    else:
        fig.update_layout(height=height)
        st.plotly_chart(fig, width="stretch", config=chart_config())
        st.caption("Viền đỏ đậm = đối tác dùng chung cho nhiều công ty thành viên.")
    st.stop()

# ---------------------------------------------------------------- theo công ty
st.caption(
    "Đối tác thượng nguồn → công ty → bên hạ nguồn. Mỗi ô ghi tên đối tác và đầu vào/đầu ra thực tế. "
    "Màu viền và đường nối theo mức độ phụ thuộc: **đỏ** = phụ thuộc một nguồn / khó thay thế, "
    "**cam** = cần xác nhận, **xám** = đã đa dạng hoá."
)

involvement = pd.concat([supply_chain["upstream_entity_id"], supply_chain["downstream_entity_id"]])
preferred = involvement.value_counts().index.tolist()

col_filter, col_type, col_height = st.columns([2.2, 1.8, 1])
with col_filter:
    company_id = company_selector(companies, available_ids, key="selected_company", preferred=preferred)
with col_height:
    height = st.slider("Chiều cao biểu đồ", 320, 900, 520, step=20, key="sc_chart_height")

if company_id is None:
    st.info("Chưa có dữ liệu công ty.")
    st.stop()

type_options = sorted(
    supply_chain.loc[supply_chain["downstream_entity_id"] == company_id, "upstream_entity_type"]
    .dropna().unique().tolist()
)
with col_type:
    entity_types = set(
        st.multiselect("Loại đối tác thượng nguồn", type_options, default=type_options, key="sc_entity_types")
    ) or set(type_options)

all_rows = supply_chain[
    (supply_chain["upstream_entity_id"] == company_id) | (supply_chain["downstream_entity_id"] == company_id)
]

if all_rows.empty:
    có_dữ_liệu = ", ".join(sorted(available_ids)) or "chưa có công ty nào"
    st.info(
        f"Chưa có dữ liệu chuỗi cung ứng cho **{company_id}**. "
        f"Hiện chỉ các công ty sau đã khai báo chuỗi cung ứng: **{có_dữ_liệu}** — "
        "chọn lại ở ô *Công ty* phía trên."
    )
    st.stop()

# Áp dụng bộ lọc loại đối tác cho CẢ chỉ số, cảnh báo và bảng — để mọi con số luôn khớp
# với sơ đồ người dùng đang nhìn. Liên kết đầu ra (công ty -> khách hàng) không bị lọc
# vì bộ lọc chỉ nói về loại đối tác THƯỢNG NGUỒN.
rows = all_rows[
    all_rows["upstream_entity_type"].isin(entity_types) | (all_rows["upstream_entity_id"] == company_id)
]
if rows.empty:
    st.info("Không có liên kết nào khớp bộ lọc hiện tại. Hãy chọn thêm loại đối tác.")
    st.stop()

if len(rows) < len(all_rows):
    st.caption(f"Đang lọc: hiển thị {len(rows)}/{len(all_rows)} liên kết của {company_id}.")

is_input = rows["downstream_entity_id"] == company_id  # liên kết đầu vào của công ty
is_concentrated = rows["single_source_flag"].astype(str).str.startswith("Có")
up_single_n = int((is_input & is_concentrated).sum())
hard_n = int(rows["substitutability"].isin(["Khó", "Không thể thay thế trong ngắn hạn"]).sum())
risk_n = int(sum(int(risk_counts_sc.get(x, 0)) > 0 for x in rows["sc_link_id"]))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Liên kết", len(rows))
k2.metric(
    "Đầu vào phụ thuộc 1 NCC", f"{up_single_n}/{len(rows)}",
    help="Chỉ tính liên kết đầu vào. Đầu ra tập trung vào một khách hàng được nêu riêng ở phần cảnh báo.",
)
k3.metric("Khó thay thế", f"{hard_n}/{len(rows)}", help=f"{hard_n / len(rows):.0%} tổng số liên kết")
k4.metric("Đã gắn rủi ro", f"{risk_n}/{len(rows)}")

alerts = insights.supply_chain_alerts(rows, company_id, risk_counts_sc)

shared_here = shared[shared["upstream_entity_id"].isin(rows["upstream_entity_id"])] if not shared.empty else shared
for _, r in shared_here.iterrows():
    others = [c for c in str(r["cong_ty"]).split(", ") if c != company_id]
    if others:
        alerts.insert(
            0,
            insights.Insight(
                "warning",
                f"**{r['upstream_entity_id']}** không chỉ phục vụ {company_id} mà còn **{', '.join(others)}** — "
                "chuyển sang *Toàn hệ thống* để thấy mức độ tập trung.",
            ),
        )

insights.render(alerts, st)

fig = build_supply_chain_network(
    supply_chain, company_id, risk_counts=risk_counts_sc, entity_types=entity_types
)
if fig is not None:
    fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", config=chart_config())

with st.expander(f"Bảng chi tiết {len(rows)} liên kết của {company_id}"):
    st.dataframe(vi(rows), width="stretch", hide_index=True)
