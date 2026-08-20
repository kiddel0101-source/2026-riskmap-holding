import pandas as pd
import streamlit as st

from src.theme import nz, risk_palette

# RAG dung chung 1 bang mau voi risk_palette() (theo theme sang/toi), khong dung
# RAG_COLORS tinh vi config.py vi bang do khong tu doi mau theo theme toi.
_RAG_KEY = {"Green": "none", "Amber": "low", "Red": "high"}


def _rag_color(status) -> str:
    palette = risk_palette()
    return palette.get(_RAG_KEY.get(str(status), ""), palette["grey"])


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
    edges: pd.DataFrame | None = None,
) -> None:
    """Hop thoai RUT GON cho 1 hoat dong trong mo hinh Chuoi gia tri Sheet1 (Phan 3) - khac
    show_risk_profile() vi Sheet1 khong co diem so/RAG/chu tri/kiem soat nhu Risk Register,
    chi co ma rui ro + ten + Problem/Details. `activity_risks` la cac dong Sheet1 (tu
    get_value_chain_v2) da loc theo 1 vc2_id; `edges` (tuy chon) la get_risk_trigger_edges()
    de hien "co the kich hoat" ngay duoi tung rui ro cu the (khong gop chung ca hoat dong,
    vi moi rui ro co the co quan he kich hoat khac nhau)."""

    @st.dialog(subject_label)
    def _dialog() -> None:
        if subject_sub:
            st.caption(subject_sub)

        risk_rows = activity_risks.dropna(subset=["risk_id"])
        if risk_rows.empty:
            st.info("Chưa có rủi ro nào gắn với hoạt động này.")
            return

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

    _dialog()
