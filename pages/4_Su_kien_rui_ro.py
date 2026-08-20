import pandas as pd
import streamlit as st

from src import insights_event
from src.data import event_store, loader, repository
from src.theme import nz, risk_palette

st.title("🌐 Sự kiện rủi ro")
st.caption(
    "Nhập diễn giải 1 sự kiện thời sự/vĩ mô, hệ thống dò từ khóa trực tiếp trong Risk Register, "
    "Chuỗi giá trị và Chuỗi cung ứng hiện có — chỉ ra chỗ nào **đã có dữ liệu** liên quan, kèm "
    "trích đoạn để thấy rõ vì sao khớp. Không dùng AI, không tự suy diễn thêm rủi ro mới — nếu từ "
    "khóa không có trong dữ liệu, hệ thống sẽ nói thẳng thay vì đoán."
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
value_chain = repository.get_value_chain(workbook_bytes)
supply_chain = repository.get_supply_chain(workbook_bytes)
risks = repository.get_risks(workbook_bytes)
taxonomy = repository.get_risk_taxonomy(workbook_bytes)
vc2 = repository.get_value_chain_v2(workbook_bytes)
trigger_edges = repository.get_risk_trigger_edges(workbook_bytes)
member_company_ids = set(companies["company_id"].dropna().astype(str))

_CATEGORY_L1_OPTIONS = sorted(risks["risk_category_l1"].dropna().unique().tolist())

# Danh sach hoat dong Chuoi gia tri (Sheet1) de chon lam "hoat dong lien quan" khi tao rui
# ro nhap - dung de tra risks_triggered_by_vc2 (thay the danh muc risk_category_l2 cu).
_vc2_options_df = vc2.drop_duplicates(subset=["vc2_id"]).sort_values(["vc1_name", "vc2_name"])
_TRIGGER_ACTIVITY_OPTIONS = ["— Không chọn —"] + _vc2_options_df["vc2_id"].tolist()
_TRIGGER_ACTIVITY_LABELS = {
    row.vc2_id: f"{row.vc1_name} — {row.vc2_name} ({row.vc2_id})" for row in _vc2_options_df.itertuples()
}


def _render_trigger_list(triggered: list[dict]) -> None:
    """Hien danh sach rui ro co the bi kich hoat (tu Risk_Linkages) - dung chung cho ca the
    rui ro va preview trong form rui ro nhap. Rong -> khong hien gi (im lang bo qua)."""
    if not triggered:
        return
    parts = []
    for t in triggered:
        extra = f" (mức ảnh hưởng: {t['impact_level']})" if t.get("impact_level") else ""
        parts.append(f"<b>{nz(t.get('target_risk_name'))}</b>{extra}")
    st.markdown(
        f"<div style='font-size:0.85rem;background:{risk_palette()['low']}22;"
        f"border-radius:6px;padding:6px 10px;margin-top:4px'>"
        f"🔗 <b>Có thể kích hoạt:</b> {' · '.join(parts)}</div>",
        unsafe_allow_html=True,
    )

def _gkey(g: dict) -> str:
    """Khoa duy nhat cho 1 nhom (vd RR.0056 xuat hien o CA CADIVI lan EMIC la 2 nhom khac
    nhau - chi dung ref_id lam key se trung, tung gay StreamlitDuplicateElementKey that."""
    return f"{g['ref_id']}__{g['company_id']}"


_SOURCE_META = {
    "risk": ("🛑", "Rủi ro trong Risk Register"),
    "value_chain": ("⛓️", "Hoạt động trong Chuỗi giá trị"),
    "supply_chain": ("🔗", "Liên kết trong Chuỗi cung ứng"),
}


def _ensure_saved(result: dict) -> int:
    if result.get("saved_event_id") is None:
        counts = {
            "risks": len(result["risk_matches"]),
            "value_chain": len(result["vc_matches"]),
            "supply_chain": len(result["sc_matches"]),
        }
        result["saved_event_id"] = event_store.save_event(result["description"], result["keywords"], counts)
    return result["saved_event_id"]


def _render_risk_group(g: dict, key_prefix: str) -> str:
    """Ve 1 the rui ro (Risk Register) + dong 'co the kich hoat' + checkbox xac nhan.
    Tra ve key cua checkbox de ham goi biet doc session_state key nao."""
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

        triggered = repository.risks_triggered_by(g["ref_id"], taxonomy, vc2, trigger_edges)
        _render_trigger_list(triggered)

        ck_key = f"confirm_risk_{key_prefix}_{_gkey(g)}"
        st.checkbox(
            "Xác nhận rủi ro này liên quan đến sự kiện — sẽ hiện thêm trên trang Danh mục rủi ro",
            key=ck_key,
        )
    return ck_key


def _render_vc_group(g: dict, key_prefix: str, description: str) -> dict:
    """Ve 1 the hoat dong (Chuoi gia tri) + checkbox + form nhap khi tich chon. Tra ve cac
    key session_state lien quan de ham goi doc lai luc xac nhan."""
    gk = _gkey(g)
    keys = {
        "checkbox": f"confirm_vc_{key_prefix}_{gk}",
        "desc": f"draft_desc_{key_prefix}_{gk}",
        "cat1": f"draft_cat1_{key_prefix}_{gk}",
        "cat2": f"draft_cat2_{key_prefix}_{gk}",
        "trigger": f"draft_trigger_{key_prefix}_{gk}",
    }
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

        st.checkbox("Chọn hoạt động này để tạo rủi ro nháp gắn với nó", key=keys["checkbox"])
        if st.session_state.get(keys["checkbox"]):
            st.session_state.setdefault(keys["desc"], f"{description} — ảnh hưởng tới hoạt động {g['label']}")
            with st.container(border=False):
                st.text_input("Mô tả rủi ro", key=keys["desc"])
                fc1, fc2 = st.columns(2)
                with fc1:
                    st.selectbox("Loại rủi ro cấp 1", _CATEGORY_L1_OPTIONS, key=keys["cat1"])
                with fc2:
                    st.text_input("Loại rủi ro cấp 2 (tuỳ chọn)", key=keys["cat2"])
                st.selectbox(
                    "Hoạt động Chuỗi giá trị liên quan (theo Sheet1, tuỳ chọn — để tra rủi ro có thể kích hoạt)",
                    _TRIGGER_ACTIVITY_OPTIONS,
                    format_func=lambda v: _TRIGGER_ACTIVITY_LABELS.get(v, v),
                    key=keys["trigger"],
                )
                chosen_trigger = st.session_state.get(keys["trigger"])
                if chosen_trigger and chosen_trigger != "— Không chọn —":
                    preview = repository.risks_triggered_by_vc2(chosen_trigger, vc2, trigger_edges)
                    _render_trigger_list(preview)
    return keys


def _handle_confirm(risk_groups: list[dict], vc_groups: list[dict], key_prefix: str, result: dict) -> None:
    if st.button("✅ Xác nhận & đưa vào Danh mục rủi ro", key=f"confirm_btn_{key_prefix}"):
        event_id = _ensure_saved(result)
        n_risk, n_draft, errors = 0, 0, []

        for g in risk_groups:
            gk = _gkey(g)
            if st.session_state.get(f"confirm_risk_{key_prefix}_{gk}"):
                event_store.confirm_risk(event_id, g["ref_id"])
                n_risk += 1

        for g in vc_groups:
            gk = _gkey(g)
            if not st.session_state.get(f"confirm_vc_{key_prefix}_{gk}"):
                continue
            desc = st.session_state.get(f"draft_desc_{key_prefix}_{gk}", "").strip()
            if not desc:
                errors.append(g["label"])
                continue
            trigger_cat = st.session_state.get(f"draft_trigger_{key_prefix}_{gk}")
            event_store.save_draft_risk(
                event_id,
                vc_node_id=g["ref_id"],
                company_id=g["company_id"],
                description=desc,
                category_l1=st.session_state.get(f"draft_cat1_{key_prefix}_{gk}"),
                category_l2=(st.session_state.get(f"draft_cat2_{key_prefix}_{gk}") or "").strip() or None,
                trigger_category=None if trigger_cat in (None, "— Không chọn —") else trigger_cat,
            )
            n_draft += 1

        if errors:
            st.error(f"Cần nhập mô tả rủi ro cho: {', '.join(errors)} — chưa tạo rủi ro nháp cho các hoạt động này.")
        if n_risk or n_draft:
            st.success(f"Đã xác nhận {n_risk} rủi ro, tạo {n_draft} rủi ro nháp ✓")
        elif not errors:
            st.info("Chưa chọn mục nào để xác nhận.")


def _render_matches(result: dict, key_prefix: str) -> None:
    risk_matches, vc_matches, sc_matches = result["risk_matches"], result["vc_matches"], result["sc_matches"]
    total = len(risk_matches) + len(vc_matches) + len(sc_matches)
    if total == 0:
        st.info(
            "🔍 Không tìm thấy dữ liệu nào chứa các từ khóa đã nhập. Hệ thống chỉ dò chữ có sẵn, "
            "không tự suy luận quan hệ gián tiếp — hãy thử từ khóa cụ thể hơn với ngành (ví dụ "
            "\"logistics\", \"nhà cung cấp\", \"giá nguyên liệu\") thay vì từ khóa quá vĩ mô."
        )
        return

    risk_groups = insights_event.group_matches(risk_matches)
    vc_groups = insights_event.group_matches(vc_matches)
    sc_groups = insights_event.group_matches(sc_matches)

    st.caption(f"**{total} mục khớp**")

    if risk_groups:
        icon, title = _SOURCE_META["risk"]
        st.markdown(f"**{icon} {title} ({len(risk_groups)})**")
        for g in risk_groups:
            _render_risk_group(g, key_prefix)

    if vc_groups:
        icon, title = _SOURCE_META["value_chain"]
        st.markdown(f"**{icon} {title} ({len(vc_groups)})**")
        for g in vc_groups:
            _render_vc_group(g, key_prefix, result["description"])

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

    if risk_groups or vc_groups:
        _handle_confirm(risk_groups, vc_groups, key_prefix, result)


def _run_scan(description: str, keywords: list[str]) -> dict:
    matched = insights_event.scan_all(risks, value_chain, supply_chain, keywords, member_company_ids)
    return {
        "description": description,
        "keywords": keywords,
        "risk_matches": matched["risk"],
        "vc_matches": matched["value_chain"],
        "sc_matches": matched["supply_chain"],
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
            "Chuỗi giá trị": e["match_counts"].get("value_chain", 0),
            "Chuỗi cung ứng": e["match_counts"].get("supply_chain", 0),
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
