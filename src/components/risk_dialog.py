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
