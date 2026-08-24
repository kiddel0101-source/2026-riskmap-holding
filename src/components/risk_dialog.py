import pandas as pd
import streamlit as st

from src.theme import nz, risk_palette

# RAG dung chung 1 bang mau voi risk_palette() (theo theme sang/toi), khong dung
# RAG_COLORS tinh vi config.py vi bang do khong tu doi mau theo theme toi.
_RAG_KEY = {"Green": "none", "Amber": "low", "Red": "high"}


def _rag_color(status) -> str:
    palette = risk_palette()
    return palette.get(_RAG_KEY.get(str(status), ""), palette["grey"])


# Mau + emoji cho 1 cap kiem soat 7_RCM (Entity/Transaction Level), theo quy tac da chot voi
# nguoi dung: Co hieu luc + Co hieu qua = xanh; Co hieu luc + Khong hieu qua = cam; Khong hieu
# luc + Khong hieu qua = do. To hop khac (vd Khong hieu luc nhung Co hieu qua) hoac thieu du
# lieu = mau ghi (khong doan).
_EFF_EMOJI = {"none": "🟢", "low": "🟠", "high": "🔴", "grey": "⚪"}


def _rcm_effectiveness_key(valid, effective) -> str:
    if valid == "Có" and effective == "Có":
        return "none"
    if valid == "Có" and effective == "Không":
        return "low"
    if valid == "Không" and effective == "Không":
        return "high"
    return "grey"


def _score_parts(row: pd.Series, prefix: str) -> tuple[str, str | None]:
    """Tach rieng so diem (ngan, hien to) va chi tiet KN/TD (dai, hien nho) - dung
    st.metric truc tiep voi ca cau "20 (KN 5 x TD 4)" se bi cat chu vi qua dai."""
    score = row.get(f"{prefix}_score")
    if pd.isna(score):
        return "Chưa chấm điểm", None
    likelihood, impact = row.get(f"{prefix}_likelihood"), row.get(f"{prefix}_impact")
    detail = f"KN {likelihood:.0f} × TĐ {impact:.0f}" if pd.notna(likelihood) and pd.notna(impact) else None
    return f"{score:.0f}", detail


def show_risk_profile(risks: pd.DataFrame, subject_label: str, subject_sub: str = "") -> None:
    """Mo hop thoai hien day du ho so cac rui ro gan voi 1 hoat dong/lien ket duoc click.

    `title` cua st.dialog phai dat luc trang tri nen ham dialog thuc su duoc dinh nghia
    (va trang tri) o BEN TRONG day, moi lan goi, de tieu de doi theo o duoc click.
    """

    @st.dialog(subject_label)
    def _dialog() -> None:
        if subject_sub:
            st.caption(subject_sub)

        if risks.empty:
            st.info("Chưa có rủi ro nào gắn với hoạt động/liên kết này.")
            return

        for _, r in risks.iterrows():
            with st.container(border=True):
                head_l, head_r = st.columns([3, 1])
                head_l.markdown(f"**{r['risk_id']}**")
                color = _rag_color(r.get("status_rag"))
                head_r.markdown(
                    f"<div style='text-align:right;color:{color};font-weight:700;"
                    f"font-size:0.85rem'>{nz(r.get('status_rag'))}</div>",
                    unsafe_allow_html=True,
                )

                st.caption(f"{nz(r.get('risk_category_l1'))} · {nz(r.get('risk_category_l2'))}")
                st.write(f"**Sự kiện rủi ro:** {nz(r.get('risk_event_l3'))}")
                st.write(f"**Nguyên nhân gốc:** {nz(r.get('root_cause'))}")
                st.write(f"**Mô tả tác động:** {nz(r.get('impact_description'))}")
                st.caption(f"Phạm vi tác động: {nz(r.get('impact_area'))}")

                s1, s2 = st.columns(2)
                for col, prefix, label in ((s1, "inherent", "Điểm gộp (inherent)"), (s2, "residual", "Điểm còn lại (residual)")):
                    value, detail = _score_parts(r, prefix)
                    with col:
                        st.caption(label)
                        st.markdown(f"#### {value}")
                        if detail:
                            st.caption(detail)

                st.write(f"**Kiểm soát hiện có:** {nz(r.get('existing_controls'))}")
                o1, o2 = st.columns(2)
                o1.write(f"**Người phụ trách:** {nz(r.get('risk_owner'))}")
                o2.write(f"**Kỳ rà soát:** {nz(r.get('review_cycle'))}")

    _dialog()


def show_activity_risks(
    activity_risks: pd.DataFrame, subject_label: str, subject_sub: str = "",
    edges: pd.DataFrame | None = None, rcm_risks: pd.DataFrame | None = None,
) -> None:
    """Hop thoai RUT GON cho 1 hoat dong trong mo hinh Chuoi gia tri Sheet1 (Phan 3) - khac
    show_risk_profile() vi Sheet1 khong co diem so/RAG/chu tri/kiem soat nhu Risk Register,
    chi co ma rui ro + ten + Problem/Details. `activity_risks` la cac dong Sheet1 (tu
    get_value_chain_v2) da loc theo 1 vc2_id; `edges` (tuy chon) la get_risk_trigger_edges()
    de hien "co the kich hoat" ngay duoi tung rui ro cu the (khong gop chung ca hoat dong,
    vi moi rui ro co the co quan he kich hoat khac nhau).

    `rcm_risks` (tuy chon, xem CLAUDE.md Muc 11.4) la cac dong tu get_rcm_risks() da loc theo
    1 vc2_id - nguon rui ro THU 3, hien o 1 muc RIENG ben duoi muc Sheet1, LUON hien (ke ca khi
    Sheet1 rong) vi 2 nguon la doc lap. Moi rui ro RCM co 2 nut bam-mo-rong "Entity Level" /
    "Transaction Level" (mau emoji theo _rcm_effectiveness_key), bam vao moi hien chi tiet kiem
    soat tuong ung (cot I-N / R-W cua sheet 7_RCM) - khong hien san de tranh hop thoai qua dai."""

    @st.dialog(subject_label)
    def _dialog() -> None:
        if subject_sub:
            st.caption(subject_sub)

        risk_rows = activity_risks.dropna(subset=["risk_id"])
        has_rcm = rcm_risks is not None and not rcm_risks.empty

        if risk_rows.empty and not has_rcm:
            st.info("Chưa có rủi ro nào gắn với hoạt động này.")
            return

        if has_rcm:
            st.markdown("**📋 Từ Sheet1**")
        if risk_rows.empty:
            st.caption("Chưa có rủi ro nào trong Sheet1 gắn với hoạt động này.")
        for _, r in risk_rows.iterrows():
            with st.container(border=True):
                st.markdown(f"**{r['risk_id']}** — {nz(r.get('risk_name'))}")
                if pd.notna(r.get("problem")):
                    st.caption(f"Vấn đề: {r['problem']}")
                if pd.notna(r.get("details")):
                    st.write(nz(r.get("details")))

                if edges is not None and not edges.empty:
                    hits = edges[edges["source_risk_id"] == r["risk_id"]]
                    for _, e in hits.iterrows():
                        extra = f" (mức ảnh hưởng: {e['impact_level']})" if pd.notna(e.get("impact_level")) else ""
                        mechanism = f"<br><span style='opacity:0.85'>{e['mechanism']}</span>" if pd.notna(e.get("mechanism")) else ""
                        st.markdown(
                            f"<div style='font-size:0.85rem;background:{risk_palette()['low']}22;"
                            f"border-radius:6px;padding:6px 10px;margin-top:6px'>"
                            f"🔗 <b>Có thể kích hoạt:</b> {nz(e.get('target_risk_name'))}{extra}{mechanism}</div>",
                            unsafe_allow_html=True,
                        )

        if has_rcm:
            st.divider()
            st.markdown("**🗂️ Từ Ma trận kiểm soát rủi ro (7_RCM)**")
            st.caption(
                "🟢 Có hiệu lực & hiệu quả · 🟠 Có hiệu lực, không hiệu quả · "
                "🔴 Không hiệu lực & không hiệu quả · ⚪ Chưa xác định / thiếu dữ liệu"
            )
            for _, r in rcm_risks.iterrows():
                with st.container(border=True):
                    head_l, head_r = st.columns([3, 2])
                    head_l.markdown(f"**{nz(r.get('risk_desc'))}**")
                    head_r.markdown(
                        f"<div style='text-align:right;font-size:0.8rem'>"
                        f"<span style='color:{risk_palette()['grey']}'>{nz(r.get('risk_category_id'))}</span> · "
                        f"<span style='color:{risk_palette().get('low', '')}'>{nz(r.get('company_id'))}</span></div>",
                        unsafe_allow_html=True,
                    )
                    if pd.notna(r.get("risk_details")):
                        st.write(nz(r.get("risk_details")))

                    ent_key = _rcm_effectiveness_key(r.get("ent_valid"), r.get("ent_effective"))
                    tx_key = _rcm_effectiveness_key(r.get("tx_valid"), r.get("tx_effective"))
                    c1, c2 = st.columns(2)
                    with c1.expander(f"{_EFF_EMOJI[ent_key]} Entity Level"):
                        for label, col in [
                            ("Mô tả kiểm soát", "ent_control_desc"), ("Đầu mối xây dựng", "ent_owner"),
                            ("Cấp phê duyệt", "ent_approval"), ("Mức độ bao phủ của kiểm soát", "ent_coverage"),
                            ("Mức độ định lượng của kiểm soát", "ent_quant"), ("Tần suất cập nhật kiểm soát", "ent_frequency"),
                        ]:
                            st.caption(label)
                            st.write(nz(r.get(col)))
                    with c2.expander(f"{_EFF_EMOJI[tx_key]} Transaction Level"):
                        for label, col in [
                            ("Mô tả kiểm soát", "tx_control_desc"), ("Người soát xét", "tx_reviewer"),
                            ("Người phê duyệt", "tx_approver"), ("Tần suất thực hiện", "tx_frequency"),
                            ("Hình thức kiểm soát", "tx_form"), ("Nền tảng thực hiện", "tx_platform"),
                        ]:
                            st.caption(label)
                            st.write(nz(r.get(col)))

    _dialog()
