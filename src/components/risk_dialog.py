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


def rcm_block_health_color(vc1_id: str, rcm_risks: pd.DataFrame) -> str | None:
    """Mau gop cho 1 KHOI chuc nang (vd "MS") tren trang Chuoi gia tri, theo NGUONG SO KIEM
    SOAT "do" (Khong hieu luc VA Khong hieu qua - ca Entity lan Transaction Level, moi cap
    tinh rieng 1 lan) tren toan bo rui ro CADIVI_RCM gan voi khoi do (TAT CA nhom nho con
    trong khoi, khong phai tung nhom rieng le - xem `rcm_group_health_color` cho cap nho hon),
    KHONG dem theo so luong rui ro, chi dem do: >=7 do -> do; >=5 do -> cam; >=3 do -> vang;
    con lai (ke ca 0 do) -> xanh.

    Tra ve None neu khoi khong co hoat dong nao co du lieu CADIVI_RCM."""
    rows = rcm_risks[rcm_risks["vc1_id"] == vc1_id]
    if rows.empty:
        return None
    return _color_by_red_count(_count_red(rows))


def rcm_group_health_color(group_id: str, rcm_risks: pd.DataFrame) -> str | None:
    """Nhu rcm_block_health_color nhung o CAP NHOM NHO (vd "FI-02", xem CLAUDE.md Muc 11.6) -
    day la cap dung KHOP THAT SU voi "vc2_id" cua chinh sheet CADIVI_RCM (da xac minh 10/10 ma
    khop, khac voi cap hoat dong cu the VC3 ma sheet nay KHONG khop toi). Tra ve None neu nhom
    khong co du lieu CADIVI_RCM nao."""
    rows = rcm_risks[rcm_risks["vc2_id"] == group_id]
    if rows.empty:
        return None
    return _color_by_red_count(_count_red(rows))


def _count_red(rows: pd.DataFrame) -> int:
    red_count = 0
    for _, r in rows.iterrows():
        if _rcm_effectiveness_key(r.get("ent_valid"), r.get("ent_effective")) == "high":
            red_count += 1
        if _rcm_effectiveness_key(r.get("tx_valid"), r.get("tx_effective")) == "high":
            red_count += 1
    return red_count


def _color_by_red_count(red_count: int) -> str:
    palette = risk_palette()
    if red_count >= 7:
        return palette["high"]
    if red_count >= 5:
        return palette["low"]
    if red_count >= 3:
        return palette["yellow"]
    return palette["none"]


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


def _rcm_legend() -> None:
    st.caption(
        "🟢 Có hiệu lực & hiệu quả · 🟠 Có hiệu lực, không hiệu quả · "
        "🔴 Không hiệu lực & không hiệu quả · ⚪ Chưa xác định / thiếu dữ liệu"
    )


def _render_rcm_card(r: pd.Series) -> None:
    """Ve 1 the rui ro CADIVI_RCM (mo ta + danh muc + cong ty, 2 khung mo rong Entity/Transaction
    Level) - dung chung giua show_activity_risks() (cap hoat dong VC3) va show_group_rcm_risks()
    (cap nhom nho VC2). Moi khung co them 2 dong "Danh gia hieu luc"/"Danh gia hieu qua" (chinh la
    2 gia tri dung de tinh mau emoji qua _rcm_effectiveness_key, truoc day chi an sau mau, gio hien
    tuong minh - nguoi dung yeu cau khi xem mockup)."""
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
                ("Đánh giá hiệu lực", "ent_valid"), ("Đánh giá hiệu quả", "ent_effective"),
            ]:
                st.caption(label)
                st.write(nz(r.get(col)))
        with c2.expander(f"{_EFF_EMOJI[tx_key]} Transaction Level"):
            for label, col in [
                ("Mô tả kiểm soát", "tx_control_desc"), ("Người soát xét", "tx_reviewer"),
                ("Người phê duyệt", "tx_approver"), ("Tần suất thực hiện", "tx_frequency"),
                ("Hình thức kiểm soát", "tx_form"), ("Nền tảng thực hiện", "tx_platform"),
                ("Đánh giá hiệu lực", "tx_valid"), ("Đánh giá hiệu quả", "tx_effective"),
            ]:
                st.caption(label)
                st.write(nz(r.get(col)))


def show_group_rcm_risks(rcm_risks: pd.DataFrame, subject_label: str, subject_sub: str = "") -> None:
    """Hop thoai hien TOAN BO rui ro CADIVI_RCM cua 1 nhom nho (VC2, vd "OP-02") - dung khi bam
    nut "Xem rui ro va kiem soat" tren luoi nhom trong pages/2_Chuoi_gia_tri.py.

    Day la hop thoai DUY NHAT hien chi tiet rui ro tren trang Chuoi gia tri (rui ro Sheet1
    2_VC_Master khong con dung nua - xem CLAUDE.md Muc 11.9), chi hien danh sach rui ro
    CADIVI_RCM + chi tiet kiem soat Entity/Transaction Level qua _render_rcm_card()."""

    @st.dialog(subject_label)
    def _dialog() -> None:
        if subject_sub:
            st.caption(subject_sub)

        if rcm_risks.empty:
            st.info("Chưa có rủi ro nào trong CADIVI_RCM gắn với nhóm này.")
            return

        _rcm_legend()
        for _, r in rcm_risks.iterrows():
            _render_rcm_card(r)

    _dialog()
