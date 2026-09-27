import pandas as pd
import streamlit as st

from src import insights_event
from src.data import event_store, loader, repository
from src.theme import risk_palette

st.title("🌐 Sự kiện rủi ro")
st.caption(
    "Nhập diễn giải 1 sự kiện thời sự/vĩ mô, hệ thống dò từ khóa trực tiếp trong Risk Register, "
    "Chuỗi cung ứng và Thư viện yếu tố dẫn phát hiện có — chỉ ra chỗ nào **đã có dữ liệu** liên "
    "quan, kèm trích đoạn để thấy rõ vì sao khớp. Không dùng AI, không tự suy diễn thêm rủi ro "
    "mới — nếu từ khóa không có trong dữ liệu, hệ thống sẽ nói thẳng thay vì đoán."
)

if event_store.is_using_default_storage():
    st.warning(
        "⚠️ **Lưu ý hạ tầng:** lịch sử sự kiện đang lưu tạm trên máy chủ (SQLite). Nếu server "
        "deploy lại mà không gắn ổ lưu trữ riêng, lịch sử sẽ mất — đang chờ IT xác nhận có "
        "database dùng chung (Postgres) hay không."
    )

try:
    workbook_bytes, fetched_at = loader.fetch_workbook()
except loader.WorkbookFetchError as exc:
    st.error(str(exc))
    st.stop()

companies = repository.get_companies(workbook_bytes)
supply_chain = repository.get_supply_chain(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
drivers = repository.get_risk_drivers(workbook_bytes)
member_company_ids = set(companies["company_id"].dropna().astype(str))


def _gkey(g: dict) -> str:
    """Khoa duy nhat cho 1 nhom (vd RR.0056 xuat hien o CA CADIVI lan EMIC la 2 nhom khac
    nhau - chi dung ref_id lam key se trung, tung gay StreamlitDuplicateElementKey that."""
    return f"{g['ref_id']}__{g['company_id']}"


_SOURCE_META = {
    "risk": ("🛑", "Rủi ro trong Risk Register"),
    "supply_chain": ("🔗", "Liên kết trong Chuỗi cung ứng"),
    "driver": ("🧭", "Yếu tố dẫn phát"),
}


def _ensure_saved(result: dict) -> int:
    if result.get("saved_event_id") is None:
        counts = {
            "risks": len(result["risk_matches"]),
            "supply_chain": len(result["sc_matches"]),
            "drivers": len(result["driver_matches"]),
        }
        result["saved_event_id"] = event_store.save_event(result["description"], result["keywords"], counts)
    return result["saved_event_id"]


def _render_risk_group(g: dict, key_prefix: str) -> str:
    """Ve 1 the rui ro (Risk Register) + checkbox xac nhan. Tra ve key cua checkbox de ham
    goi biet doc session_state key nao."""
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{g['label']}**")
        c2.markdown(
            f"<div style='text-align:right;color:{risk_palette()['grey']};font-size:0.85rem'>{g['company_id']}</div>",
            unsafe_allow_html=True,
        )
        for m in g["items"]:
            st.markdown(f"<div style='font-size:0.9rem'>{m.snippet_html}</div>", unsafe_allow_html=True)
            why = f"Khớp từ khóa **{m.keyword}** trong cột **{m.field_label}**"
            if not m.is_exact:
                why += " · ⚠️ khớp gần đúng (không phân biệt dấu) — có thể khác nghĩa, hãy đọc kỹ trích đoạn"
            st.caption(why)

        ck_key = f"confirm_risk_{key_prefix}_{_gkey(g)}"
        st.checkbox(
            "Xác nhận rủi ro này liên quan đến sự kiện — sẽ hiện thêm trên trang Danh mục rủi ro",
            key=ck_key,
        )
    return ck_key


_DRIVER_CATEGORY_LABEL = {
    "Politics": "POLITICS", "Economics": "ECONOMICS", "Social": "SOCIAL",
    "Technological": "TECHNOLOGICAL", "Environment": "ENVIRONMENT", "Legal": "LEGAL",
}


def _render_driver_group(g: dict) -> None:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{g['driver_name']}**")
        badge = _DRIVER_CATEGORY_LABEL.get(g["driver_category"], g["driver_category"] or "—")
        c2.markdown(
            f"<div style='text-align:right;color:{risk_palette()['grey']};font-size:0.8rem;"
            f"font-weight:700'>{badge}</div>",
            unsafe_allow_html=True,
        )
        for m in g["items"]:
            st.markdown(f"<div style='font-size:0.9rem'>{m.snippet_html}</div>", unsafe_allow_html=True)
            why = f"Khớp từ khóa **{m.keyword}** trong cột **{m.field_label}**"
            if not m.is_exact:
                why += " · ⚠️ khớp gần đúng (không phân biệt dấu) — có thể khác nghĩa, hãy đọc kỹ trích đoạn"
            st.caption(why)

        if g["industries"]:
            st.caption("**Ngành liên quan:** " + " · ".join(g["industries"]))

        if g["risk_links"]:
            st.markdown(f"**Danh mục rủi ro liên quan ({len(g['risk_links'])})**")
            for link in g["risk_links"]:
                cat_id = link.get("risk_category_id") or "—"
                cat_l2 = link.get("risk_category_l2") or "—"
                st.markdown(
                    f"<div style='border-left:3px solid {risk_palette()['low']};padding:4px 0 4px 10px;"
                    f"margin-top:4px;font-size:0.85rem'><b>{cat_id} — {cat_l2}</b><br>"
                    f"<span style='color:{risk_palette()['grey']}'>{link.get('mechanism') or ''}</span></div>",
                    unsafe_allow_html=True,
                )

        if g["source_url"]:
            st.markdown(f"[🔗 Nguồn tham khảo]({g['source_url']})")


def _handle_confirm(risk_groups: list[dict], key_prefix: str, result: dict) -> None:
    if st.button("✅ Xác nhận & đưa vào Danh mục rủi ro", key=f"confirm_btn_{key_prefix}"):
        event_id = _ensure_saved(result)
        n_risk = 0

        for g in risk_groups:
            gk = _gkey(g)
            if st.session_state.get(f"confirm_risk_{key_prefix}_{gk}"):
                event_store.confirm_risk(event_id, g["ref_id"])
                n_risk += 1

        if n_risk:
            st.success(f"Đã xác nhận {n_risk} rủi ro ✓")
        else:
            st.info("Chưa chọn mục nào để xác nhận.")


def _render_matches(result: dict, key_prefix: str) -> None:
    risk_matches, sc_matches = result["risk_matches"], result["sc_matches"]
    driver_matches = result["driver_matches"]
    total = len(risk_matches) + len(sc_matches) + len(driver_matches)
    if total == 0:
        st.info(
            "🔍 Không tìm thấy dữ liệu nào chứa các từ khóa đã nhập. Hệ thống chỉ dò chữ có sẵn, "
            "không tự suy luận quan hệ gián tiếp — hãy thử từ khóa cụ thể hơn với ngành (ví dụ "
            "\"logistics\", \"nhà cung cấp\", \"giá nguyên liệu\") thay vì từ khóa quá vĩ mô."
        )
        return

    risk_groups = insights_event.group_matches(risk_matches)
    sc_groups = insights_event.group_matches(sc_matches)
    driver_groups = insights_event.group_driver_matches(driver_matches)

    st.caption(f"**{total} mục khớp**")

    if driver_groups:
        icon, title = _SOURCE_META["driver"]
        st.markdown(f"**{icon} {title} ({len(driver_groups)})**")
        for g in driver_groups:
            _render_driver_group(g)

    if risk_groups:
        icon, title = _SOURCE_META["risk"]
        st.markdown(f"**{icon} {title} ({len(risk_groups)})**")
        for g in risk_groups:
            _render_risk_group(g, key_prefix)

    if sc_groups:
        icon, title = _SOURCE_META["supply_chain"]
        st.markdown(f"**{icon} {title} ({len(sc_groups)})**")
        for g in sc_groups:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{g['label']}**")
                c2.markdown(
                    f"<div style='text-align:right;color:{risk_palette()['grey']};font-size:0.85rem'>{g['company_id']}</div>",
                    unsafe_allow_html=True,
                )
                for m in g["items"]:
                    st.markdown(f"<div style='font-size:0.9rem'>{m.snippet_html}</div>", unsafe_allow_html=True)
                    why = f"Khớp từ khóa **{m.keyword}** trong cột **{m.field_label}**"
                    if not m.is_exact:
                        why += " · ⚠️ khớp gần đúng (không phân biệt dấu) — có thể khác nghĩa, hãy đọc kỹ trích đoạn"
                    st.caption(why)

    if risk_groups:
        _handle_confirm(risk_groups, key_prefix, result)


def _run_scan(description: str, keywords: list[str]) -> dict:
    matched = insights_event.scan_all(risks, supply_chain, keywords, member_company_ids)
    return {
        "description": description,
        "keywords": keywords,
        "risk_matches": matched["risk"],
        "sc_matches": matched["supply_chain"],
        "driver_matches": insights_event.scan_drivers_all(drivers, keywords),
        "saved_event_id": None,
    }


with st.container(border=True):
    description = st.text_area(
        "Diễn giải sự kiện", key="event_desc", height=80,
        placeholder="Ví dụ: Mỹ chiến tranh Iran, làm tăng giá dầu và chậm giao hàng",
    )
    if st.button("💡 Gợi ý từ khóa từ mô tả"):
        st.session_state["event_keywords"] = insights_event.suggest_keywords(description)
    st.text_input(
        "Từ khóa (phân tách bằng dấu phẩy — có thể sửa lại trước khi tìm)",
        key="event_keywords",
        placeholder="Ví dụ: giá đồng, nguyên liệu đầu vào",
    )

    if st.button("🔍 Tìm rủi ro liên quan", type="primary"):
        kws = insights_event.parse_keywords(st.session_state.get("event_keywords", ""))
        if not kws:
            st.error("Nhập ít nhất 1 từ khóa trước khi tìm.")
        else:
            st.session_state["event_last_search"] = _run_scan(description, kws)

result = st.session_state.get("event_last_search")
if result:
    st.divider()
    _render_matches(result, key_prefix="search")

    if st.button("💾 Lưu vào lịch sử"):
        _ensure_saved(result)
        st.success("Đã lưu vào lịch sử ✓")

st.divider()
st.subheader("Lịch sử sự kiện đã nhập")

events = event_store.list_events()
if not events:
    st.caption("Chưa có sự kiện nào được lưu.")
else:
    hist_df = pd.DataFrame([
        {
            "Thời điểm": e["created_at"].strftime("%d/%m/%Y %H:%M"),
            "Diễn giải": e["description"],
            "Từ khóa": ", ".join(e["keywords"]),
            "Rủi ro": e["match_counts"].get("risks", 0),
            "Chuỗi cung ứng": e["match_counts"].get("supply_chain", 0),
            "Yếu tố dẫn phát": e["match_counts"].get("drivers", 0),
        }
        for e in events
    ])
    selection = st.dataframe(
        hist_df, width="stretch", hide_index=True,
        on_select="rerun", selection_mode="single-row", key="event_history_table",
    )
    st.caption("Bấm 1 dòng để tính lại kết quả khớp theo dữ liệu hiện tại (dữ liệu có thể đã thay đổi từ lúc nhập).")

    selected_rows = (selection or {}).get("selection", {}).get("rows", [])
    if selected_rows:
        chosen = events[selected_rows[0]]
        st.markdown(f"**Kết quả khớp hiện tại cho:** _{chosen['description']}_")
        replay = _run_scan(chosen["description"], chosen["keywords"])
        replay["saved_event_id"] = chosen["id"]
        _render_matches(replay, key_prefix=f"hist{chosen['id']}")
