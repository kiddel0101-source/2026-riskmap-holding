"""Phat hien tu dong cac diem dang chu y trong du lieu, de hien thi thanh canh bao
tren tung trang thay vi bat nguoi dung tu do trong bang."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Insight:
    level: str  # "warning" | "info"
    text: str


def _fmt_list(items, limit: int = 4) -> str:
    items = list(items)
    head = ", ".join(str(i) for i in items[:limit])
    return head if len(items) <= limit else f"{head} … (+{len(items) - limit})"


def shared_upstream_entities(sc: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    """Nha cung cap/doi tac thuong nguon phuc vu tu 2 cong ty thanh vien tro len.
    Day la rui ro tap trung cap tap doan ma so do theo tung cong ty khong the hien duoc."""
    member_ids = set(companies["company_id"].dropna().astype(str))
    rows = sc[sc["downstream_entity_id"].isin(member_ids)]
    if rows.empty:
        return rows.iloc[0:0]
    grouped = (
        rows.groupby("upstream_entity_id")
        .agg(
            so_cong_ty=("downstream_entity_id", "nunique"),
            cong_ty=("downstream_entity_id", lambda s: ", ".join(sorted(set(s)))),
            dau_vao=("input_output_type", lambda s: " · ".join(sorted(set(s)))),
            kho_thay_the=("substitutability", lambda s: any(
                str(v) in ("Khó", "Không thể thay thế trong ngắn hạn") for v in s
            )),
        )
        .reset_index()
    )
    return grouped[grouped["so_cong_ty"] >= 2].sort_values("so_cong_ty", ascending=False)


def risk_data_gaps(risks: pd.DataFrame) -> list[Insight]:
    out: list[Insight] = []
    total = len(risks)
    if not total:
        return out

    unscored = risks["inherent_score"].isna().sum()
    if unscored:
        out.append(
            Insight(
                "warning",
                f"**{unscored}/{total} rủi ro chưa được chấm điểm** (thiếu Likelihood/Impact) — "
                f"heatmap và biểu đồ dưới đây chỉ phản ánh {total - unscored} rủi ro đã đánh giá.",
            )
        )

    no_residual = risks["inherent_score"].notna() & risks["residual_score"].isna()
    if no_residual.any():
        out.append(
            Insight(
                "info",
                f"{int(no_residual.sum())} rủi ro có điểm gộp (inherent) nhưng chưa chấm lại sau kiểm soát "
                f"(residual): {_fmt_list(risks.loc[no_residual, 'risk_id'])}.",
            )
        )

    no_control = risks["existing_controls"].isna().sum()
    if no_control:
        out.append(Insight("info", f"{no_control} rủi ro chưa ghi nhận biện pháp kiểm soát hiện có."))
    return out


def control_effectiveness_anomalies(risks: pd.DataFrame) -> list[Insight]:
    """Rui ro co diem residual >= inherent: kiem soat khong lam giam (hoac lam tang) rui ro."""
    out: list[Insight] = []
    both = risks.dropna(subset=["inherent_score", "residual_score"])
    if both.empty:
        return out

    worse = both[both["residual_score"] > both["inherent_score"]]
    for _, r in worse.iterrows():
        out.append(
            Insight(
                "warning",
                f"**{r['risk_id']}** — điểm sau kiểm soát *cao hơn* trước kiểm soát "
                f"({r['inherent_score']:.0f} → {r['residual_score']:.0f}). "
                f"Kiểm soát hiện tại chưa có tác dụng giảm rủi ro: _{r['risk_event_l3']}_",
            )
        )

    flat = both[both["residual_score"] == both["inherent_score"]]
    if not flat.empty:
        out.append(
            Insight(
                "info",
                f"{len(flat)} rủi ro có điểm không đổi sau kiểm soát ({_fmt_list(flat['risk_id'])}) — "
                "cần rà lại hiệu lực của biện pháp đang áp dụng.",
            )
        )

    # RAG khong nhat quan: cung diem residual nhung khac nhan mau
    rag_by_score = both.groupby("residual_score")["status_rag"].nunique()
    inconsistent = rag_by_score[rag_by_score > 1]
    for score in inconsistent.index:
        sub = both[both["residual_score"] == score]
        pairs = ", ".join(f"{r.risk_id}={r.status_rag}" for r in sub.itertuples())
        out.append(
            Insight(
                "warning",
                f"Cùng điểm residual = {score:.0f} nhưng gắn nhãn RAG khác nhau ({pairs}) — "
                "ngưỡng phân loại RAG chưa áp dụng thống nhất.",
            )
        )
    return out


def supply_chain_alerts(sc: pd.DataFrame, company_id: str, risk_counts: pd.Series) -> list[Insight]:
    out: list[Insight] = []
    rows = sc[(sc["upstream_entity_id"] == company_id) | (sc["downstream_entity_id"] == company_id)]
    if rows.empty:
        return out

    single = rows[rows["single_source_flag"].astype(str).str.startswith("Có")]
    if not single.empty:
        out.append(
            Insight(
                "warning",
                f"**{len(single)}/{len(rows)} liên kết phụ thuộc một nguồn duy nhất**: "
                f"{_fmt_list(single['input_output_type'])}.",
            )
        )

    hard = rows[rows["substitutability"].isin(["Khó", "Không thể thay thế trong ngắn hạn"])]
    if not hard.empty:
        out.append(
            Insight(
                "warning",
                f"{len(hard)} liên kết khó/không thể thay thế trong ngắn hạn: "
                f"{_fmt_list(hard['input_output_type'])}.",
            )
        )

    unconfirmed = rows[rows["single_source_flag"].astype(str).str.contains("cần xác nhận", case=False)]
    if not unconfirmed.empty:
        out.append(
            Insight("info", f"{len(unconfirmed)} liên kết còn ghi 'cần xác nhận' — dữ liệu chưa được chốt.")
        )

    linked = rows[rows["sc_link_id"].map(lambda x: int(risk_counts.get(x, 0)) > 0)]
    if not linked.empty:
        out.append(
            Insight("info", f"{len(linked)} liên kết đã được gắn rủi ro trong Risk Register.")
        )
    return out


def value_chain_hotspots(vc: pd.DataFrame, risks: pd.DataFrame, company_id: str) -> list[Insight]:
    from src.data.repository import risks_exploded_by_vc_node

    out: list[Insight] = []
    nodes = vc[vc["company_id"] == company_id]
    if nodes.empty:
        return out

    exploded = risks_exploded_by_vc_node(risks)
    joined = exploded.merge(nodes[["vc_node_id", "vc_function"]], on="vc_node_id")
    covered = joined["vc_node_id"].nunique()
    if covered < len(nodes):
        out.append(
            Insight(
                "info",
                f"{len(nodes) - covered}/{len(nodes)} hoạt động chưa gắn rủi ro nào — "
                "có thể do chưa nhận diện, không hẳn là không có rủi ro.",
            )
        )

    if not joined.empty:
        by_fn = joined.groupby("vc_function")["risk_id"].nunique().sort_values(ascending=False)
        top_fn, top_n = by_fn.index[0], int(by_fn.iloc[0])
        out.append(
            Insight(
                "warning",
                f"Khối **{top_fn}** tập trung nhiều rủi ro nhất ({top_n} rủi ro) — điểm nóng cần ưu tiên rà soát.",
            )
        )
    return out


def render(items: list[Insight], st, *, max_warnings: int = 3) -> None:
    """Hien thi gon trong 1 khung thay vi nhieu hop canh bao lon chiem het man hinh:
    canh bao quan trong hien truc tiep (toi da `max_warnings`), phan con lai gap vao expander."""
    if not items:
        return

    warnings = [i for i in items if i.level == "warning"]
    infos = [i for i in items if i.level != "warning"]
    shown, overflow = warnings[:max_warnings], warnings[max_warnings:] + infos

    with st.container(border=True):
        st.markdown("**Điểm cần chú ý**")
        for ins in shown:
            st.markdown(f"⚠️ {ins.text}")
        if overflow:
            with st.expander(f"Thêm {len(overflow)} ghi chú về dữ liệu"):
                for ins in overflow:
                    st.markdown(f"· {ins.text}")
