import pandas as pd
import streamlit as st

from src import insights
from src.components.filters import company_multiselector
from src.config import RAG_COLORS, vi
from src.data import event_store, loader, repository
from src.theme import chart_config, nz, risk_palette
from src.viz.risk import build_risk_heatmap, build_risk_migration_chart

st.title("🛑 Danh mục rủi ro")
st.caption(
    "Heatmap Likelihood × Impact và biểu đồ risk migration minh hoạ hiệu quả kiểm soát "
    "(mũi tên kéo rủi ro từ điểm trước kiểm soát về sau kiểm soát)."
)

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

companies = repository.get_companies(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
taxonomy = repository.get_risk_taxonomy(workbook_bytes)
trigger_edges = repository.get_risk_trigger_edges(workbook_bytes)
available_ids = repository.companies_in(risks, companies, ["company_id"])

if risks.empty:
    st.info("Chưa có dữ liệu rủi ro.")
    st.stop()

scored = int(risks["inherent_score"].notna().sum())
k1, k2, k3, k4 = st.columns(4)
k1.metric("Tổng rủi ro", len(risks))
k2.metric("Đã chấm điểm", f"{scored}/{len(risks)}", help=f"Độ phủ {scored / len(risks):.0%}")
k3.metric("Mức Red", int((risks["status_rag"] == "Red").sum()))
k4.metric("Chưa đánh giá", int((risks["status_rag"] == "Chưa đánh giá").sum()))

insights.render(insights.risk_data_gaps(risks) + insights.control_effectiveness_anomalies(risks), st)

st.divider()

f1, f2, f3 = st.columns([2, 1.4, 1.4])
with f1:
    selected_companies = company_multiselector(companies, available_ids, key="selected_companies")
with f2:
    categories = sorted(risks["risk_category_l1"].dropna().unique().tolist())
    selected_categories = st.multiselect("Nhóm rủi ro", categories, default=categories)
with f3:
    statuses = sorted(risks["status_rag"].dropna().unique().tolist())
    selected_statuses = st.multiselect("Trạng thái RAG", statuses, default=statuses)

filtered = risks[
    risks["company_id"].isin(selected_companies)
    & risks["risk_category_l1"].isin(selected_categories)
    & risks["status_rag"].isin(selected_statuses)
]

st.markdown(f"**{len(filtered)} / {len(risks)} rủi ro** khớp bộ lọc")

table_cols = [
    c for c in [
        "risk_id", "company_id", "risk_category_l1", "risk_event_l3",
        "inherent_score", "residual_score", "status_rag", "risk_owner",
    ] if c in filtered.columns
]
sort_col = "residual_score" if filtered["residual_score"].notna().any() else "inherent_score"
table = filtered[table_cols].sort_values(sort_col, ascending=False, na_position="last")

display_table = table.copy()
for c in ("inherent_score", "residual_score"):
    if c in display_table.columns:
        display_table[c] = display_table[c].apply(lambda v: "—" if pd.isna(v) else f"{int(v)}")
for c in ("risk_owner",):
    if c in display_table.columns:
        display_table[c] = display_table[c].fillna("—")


def _highlight_rag(val):
    color = RAG_COLORS.get(val)
    return f"background-color: {color}33; color: {color}; font-weight: 600" if color else ""


display_table = vi(display_table)
styler = display_table.style
if "Trạng thái" in display_table.columns:
    styler = styler.map(_highlight_rag, subset=["Trạng thái"])

st.dataframe(styler, width="stretch", hide_index=True, height=320)

st.divider()

col_heat, col_mig = st.columns(2)

with col_heat:
    st.subheader("Ma trận Likelihood × Impact")
    mode_label = st.radio("Chế độ", ["Inherent", "Residual"], horizontal=True, key="heatmap_mode")
    mode = mode_label.lower()
    n_plotted = int(filtered[f"{mode}_score"].notna().sum())
    heat_fig = build_risk_heatmap(filtered, mode=mode)
    heat_fig.update_layout(height=380)
    st.plotly_chart(heat_fig, width="stretch", config=chart_config())
    st.caption(
        f"Đang vẽ **{n_plotted}/{len(filtered)}** rủi ro có đủ điểm ở chế độ {mode_label}. "
        "Nền ô cố định theo vùng chấp nhận: xanh (≤ 6), cam (7–12), đỏ (> 12)."
    )

with col_mig:
    st.subheader("Risk migration — trước → sau kiểm soát")
    mig_fig = build_risk_migration_chart(filtered)
    mig_fig.update_layout(height=380 + 42)
    st.plotly_chart(mig_fig, width="stretch", config=chart_config())
    st.caption(
        "● điểm trước kiểm soát, ◆ sau kiểm soát, màu theo trạng thái RAG. "
        "Mũi tên đi xuống-trái = kiểm soát hiệu quả; đi lên-phải = rủi ro tăng sau kiểm soát."
    )

not_assessed = filtered[filtered["residual_score"].isna()]
if not not_assessed.empty:
    with st.expander(f"{len(not_assessed)} rủi ro chưa có điểm sau kiểm soát"):
        st.dataframe(
            vi(not_assessed[[c for c in table_cols if c != "residual_score"]]),
            width="stretch", hide_index=True,
        )

confirmed = event_store.list_confirmed_risks()
if confirmed:
    st.divider()
    with st.container(border=True):
        st.markdown("### 🏷️ Rủi ro đã xác nhận từ Sự kiện rủi ro")
        st.caption(
            "Rủi ro đã có sẵn trong Risk Register, được đánh dấu là liên quan tới 1 sự kiện cụ "
            "thể ở trang Sự kiện rủi ro — dữ liệu rủi ro vẫn lấy sống từ Excel, chỉ thêm nhãn liên kết."
        )
        rows = []
        for c in confirmed:
            match = risks[risks["risk_id"] == c["risk_id"]]
            if match.empty:
                desc, company, triggered = "(không còn thấy trong Risk Register)", "—", []
            else:
                r = match.iloc[0]
                desc, company = nz(r.get("risk_event_l3")), nz(r.get("company_id"))
                triggered = repository.risks_triggered_by(c["risk_id"], taxonomy, trigger_edges)
            rows.append({
                "Mã rủi ro": c["risk_id"],
                "Mô tả": desc,
                "Công ty": company,
                "Sự kiện gốc": c["event_description"],
                "Có thể kích hoạt": " · ".join(triggered) if triggered else "—",
                "Ngày xác nhận": c["confirmed_at"].strftime("%d/%m/%Y %H:%M"),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

drafts = event_store.list_draft_risks()
if drafts:
    st.divider()
    with st.container(border=True):
        st.markdown("### 📝 Rủi ro nháp chờ chính thức hoá")
        st.caption(
            "Đây là rủi ro nháp do hệ thống tạo khi xác nhận từ 1 sự kiện ở trang Sự kiện rủi ro "
            "— **CHƯA có trong Risk Register chính thức**. Cán bộ cần tự thêm vào Excel nếu xác "
            "nhận đây là rủi ro thật."
        )
        rows = []
        for d in drafts:
            triggered = (
                repository.risks_triggered_by_category(d["trigger_category"], trigger_edges)
                if d.get("trigger_category") else []
            )
            loai = nz(d.get("category_l1"), "—")
            if d.get("category_l2"):
                loai += f" · {d['category_l2']}"
            rows.append({
                "": "NHÁP",
                "Mô tả": d["description"],
                "Loại rủi ro": loai,
                "Hoạt động nguồn": d["vc_node_id"],
                "Công ty": d["company_id"],
                "Có thể kích hoạt": " · ".join(triggered) if triggered else "—",
                "Ngày tạo": d["created_at"].strftime("%d/%m/%Y %H:%M"),
            })
        draft_df = pd.DataFrame(rows)
        amber = risk_palette()["low"]
        styler = draft_df.style.map(lambda v: f"color:{amber};font-weight:700", subset=[""])
        st.dataframe(styler, width="stretch", hide_index=True)
