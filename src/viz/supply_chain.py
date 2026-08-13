import pandas as pd
import plotly.graph_objects as go

from src.config import ACCENT
from src.theme import hex_to_rgba, nz, plotly_template, risk_palette, wrap_text

HARD_SUBSTITUTE = ("Khó", "Không thể thay thế trong ngắn hạn")


def _dependency_level(row: pd.Series) -> str:
    """'high' = phu thuoc mot nguon / kho thay the; 'medium' = can xac nhan; 'low' = con lai."""
    single = str(row.get("single_source_flag", "") or "")
    subst = str(row.get("substitutability", "") or "")
    if single.startswith("Có") or subst in HARD_SUBSTITUTE:
        return "high"
    if "ần xác nhận" in single or subst == "Trung bình":
        return "medium"
    return "low"


def _edge_style(level: str, palette: dict) -> tuple[str, float, str]:
    return {
        "high": (palette["high"], 2.6, "dash"),
        "medium": (palette["low"], 2.0, "dot"),
        "low": (palette["grey"], 1.4, "solid"),
    }[level]


def _y_positions(n: int) -> list[float]:
    if n <= 0:
        return []
    if n == 1:
        return [0.5]
    return [1 - (i + 0.5) / n for i in range(n)]


def _add_box(fig, cx, cy, w, h, color, title, lines, *, bold_border=False, fill_alpha=0.14):
    """Ve 1 o co vien + tieu de + cac dong phu, chia deu theo chieu cao o de chu
    khong bao gio tran ra ngoai khung."""
    lines = [ln for ln in (lines or []) if ln]
    fig.add_shape(
        type="rect", x0=cx - w / 2, x1=cx + w / 2, y0=cy - h / 2, y1=cy + h / 2,
        line=dict(color=color, width=3 if bold_border else 1.6),
        fillcolor=hex_to_rgba(color, fill_alpha), layer="below",
    )
    slots = 1 + len(lines)
    step = h / (slots + 0.7)
    y = cy + h / 2 - step * 0.85
    fig.add_annotation(
        x=cx, y=y, text=f"<b>{title}</b>", showarrow=False,
        font=dict(size=10.5, color=color), align="center",
    )
    for i, ln in enumerate(lines):
        fig.add_annotation(
            x=cx, y=y - step * (i + 1), text=ln, showarrow=False,
            font=dict(size=8.8, color=color), opacity=0.92, align="center",
        )


def build_supply_chain_network(
    sc: pd.DataFrame,
    company_id: str,
    *,
    risk_counts: pd.Series | None = None,
    entity_types: set[str] | None = None,
) -> go.Figure | None:
    """So do 3 cot cho 1 cong ty: doi tac thuong nguon (trai) -> cong ty (giua) ->
    ben ha nguon (phai). Moi o ghi ro TEN doi tac + DAU VAO/RA thuc te, mau vien theo
    muc do phu thuoc (do = mot nguon/kho thay the)."""
    palette = risk_palette()
    risk_counts = risk_counts if risk_counts is not None else pd.Series(dtype=int)

    rows = sc[(sc["upstream_entity_id"] == company_id) | (sc["downstream_entity_id"] == company_id)]
    if entity_types:
        keep = rows["upstream_entity_type"].isin(entity_types) | (rows["upstream_entity_id"] == company_id)
        rows = rows[keep]
    if rows.empty:
        return None

    up_rows = rows[rows["downstream_entity_id"] == company_id].reset_index(drop=True)
    down_rows = rows[rows["upstream_entity_id"] == company_id].reset_index(drop=True)

    fig = go.Figure()
    box_w = 0.30
    hov_x, hov_y, hov_text, hov_ids = [], [], [], []

    def draw_side(side_rows: pd.DataFrame, cx: float, is_upstream: bool) -> None:
        n = len(side_rows)
        if not n:
            return
        h = min(0.30, 0.92 / n)
        for i, y in enumerate(_y_positions(n)):
            r = side_rows.iloc[i]
            entity = r["upstream_entity_id"] if is_upstream else r["downstream_entity_id"]
            level = _dependency_level(r)
            color, width, dash = _edge_style(level, palette)
            n_risk = int(risk_counts.get(r.get("sc_link_id"), 0))

            lines = [wrap_text(nz(r.get("input_output_type")), width=36, max_lines=1)]
            if n_risk:
                lines.append(f"⚠ {n_risk} rủi ro")
            _add_box(fig, cx, y, box_w, h * 0.82, color, wrap_text(entity, 36, 1), lines)

            x_from = cx + box_w / 2 if is_upstream else 0.5 + box_w / 2
            x_to = 0.5 - box_w / 2 if is_upstream else cx - box_w / 2
            y_from, y_to = (y, 0.5) if is_upstream else (0.5, y)
            fig.add_annotation(
                x=x_to, y=y_to, ax=x_from, ay=y_from, xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=width, arrowcolor=color,
            )
            fig.add_shape(
                type="line", x0=x_from, y0=y_from, x1=x_to, y1=y_to,
                line=dict(color=color, width=width, dash=dash),
            )

            hov_x.append(cx)
            hov_y.append(y)
            hov_ids.append(r.get("sc_link_id"))
            lead = r.get("lead_time_days")
            lead_txt = f"{lead:.0f} ngày" if pd.notna(lead) else "—"
            hov_text.append(
                f"<b>{nz(r.get('sc_link_id'))}</b> · {entity}<br>"
                f"{nz(r.get('input_output_type'))}<br>"
                f"Loại đối tác: {nz(r.get('upstream_entity_type'))}<br>"
                f"Nguồn gốc: {nz(r.get('geographic_origin'))} · Lead time: {lead_txt}<br>"
                f"Hợp đồng: {nz(r.get('contract_type'))}<br>"
                f"Mức độ tập trung: {nz(r.get('single_source_flag'))}<br>"
                f"Khả năng thay thế: {nz(r.get('substitutability'))}<br>"
                f"Rủi ro gắn với liên kết: {n_risk}"
            )

    draw_side(up_rows, 0.15, True)
    draw_side(down_rows, 0.85, False)

    _add_box(
        fig, 0.5, 0.5, box_w, 0.20, ACCENT, company_id,
        [f"{len(up_rows)} đầu vào · {len(down_rows)} đầu ra"], bold_border=True, fill_alpha=0.18,
    )

    fig.add_annotation(x=0.15, y=1.06, text="<b>THƯỢNG NGUỒN</b>", showarrow=False, font=dict(size=9.5), opacity=0.7)
    fig.add_annotation(x=0.5, y=1.06, text="<b>CÔNG TY</b>", showarrow=False, font=dict(size=9.5), opacity=0.7)
    fig.add_annotation(x=0.85, y=1.06, text="<b>HẠ NGUỒN</b>", showarrow=False, font=dict(size=9.5), opacity=0.7)

    fig.add_trace(
        go.Scatter(
            x=hov_x, y=hov_y, mode="markers", marker=dict(size=42, opacity=0),
            customdata=hov_ids,
            hovertext=hov_text, hoverinfo="text", showlegend=False,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(visible=False, range=[-0.02, 1.02]),
        yaxis=dict(visible=False, range=[-0.06, 1.12]),
        margin=dict(l=6, r=6, t=6, b=6),
        hoverlabel=dict(align="left"),
        clickmode="event+select",
    )
    return fig


def build_group_supply_map(sc: pd.DataFrame, companies: pd.DataFrame, shared: pd.DataFrame) -> go.Figure | None:
    """So do toan he thong: gop tat ca cong ty thanh vien vao 1 khung de lo ra nhung
    doi tac thuong nguon dung chung cho nhieu cong ty (rui ro tap trung cap tap doan)
    — dieu ma so do theo tung cong ty rieng le khong the hien duoc."""
    palette = risk_palette()
    member_ids = set(companies["company_id"].dropna().astype(str))
    rows = sc[sc["downstream_entity_id"].isin(member_ids)]
    if rows.empty:
        return None

    shared_ids = set(shared["upstream_entity_id"]) if not shared.empty else set()
    center_ids = list(dict.fromkeys(rows["downstream_entity_id"]))
    center_rank = {c: i for i, c in enumerate(center_ids)}

    # Xep doi tac dung chung len dau, phan con lai gom theo cong ty ma no phuc vu
    # -> giam toi da so duong noi cat cheo nhau
    def _order_key(entity: str):
        served = rows.loc[rows["upstream_entity_id"] == entity, "downstream_entity_id"]
        return (entity not in shared_ids, min(center_rank[c] for c in served), entity)

    upstream_ids = sorted(dict.fromkeys(rows["upstream_entity_id"]), key=_order_key)

    fig = go.Figure()
    box_w = 0.34
    center_box_w = box_w * 0.7
    up_y = dict(zip(upstream_ids, _y_positions(len(upstream_ids))))
    ct_y = dict(zip(center_ids, _y_positions(len(center_ids))))
    x_from, x_to = 0.20 + box_w / 2, 0.80 - center_box_w / 2

    for _, r in rows.iterrows():
        src, dst = r["upstream_entity_id"], r["downstream_entity_id"]
        is_shared = src in shared_ids
        level = _dependency_level(r)
        color, width, dash = _edge_style(level, palette)
        if is_shared:
            color, width, dash = palette["high"], 3.0, "dash"
        fig.add_shape(
            type="line", x0=x_from, y0=up_y[src], x1=x_to, y1=ct_y[dst],
            line=dict(color=color, width=width, dash=dash),
        )
        fig.add_annotation(
            x=x_to, y=ct_y[dst], ax=x_from, ay=up_y[src], xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=width, arrowcolor=color,
        )

    hov_x, hov_y, hov_text = [], [], []
    h_up = min(0.24, 0.94 / max(1, len(upstream_ids)))
    for e in upstream_ids:
        is_shared = e in shared_ids
        color = palette["high"] if is_shared else palette["grey"]
        sub_rows = rows[rows["upstream_entity_id"] == e]
        serves = sorted(set(sub_rows["downstream_entity_id"]))
        lines = [wrap_text(" · ".join(sorted(set(sub_rows["input_output_type"]))), 44, 1)]
        if is_shared:
            lines.append(f"⚠ dùng chung: {', '.join(serves)}")
        _add_box(fig, 0.20, up_y[e], box_w, h_up * 0.84, color, wrap_text(e, 40, 1), lines,
                 bold_border=is_shared)
        hov_x.append(0.20)
        hov_y.append(up_y[e])
        hov_text.append(
            f"<b>{e}</b><br>Cung cấp cho: {', '.join(serves)}<br>"
            f"Đầu vào: {' · '.join(sorted({nz(v) for v in sub_rows['input_output_type']}))}<br>"
            f"Khả năng thay thế: {' · '.join(sorted({nz(v) for v in sub_rows['substitutability']}))}"
        )

    h_ct = min(0.26, 0.94 / max(1, len(center_ids)))
    for c in center_ids:
        sub = rows[rows["downstream_entity_id"] == c]
        n_up = sub["upstream_entity_id"].nunique()
        n_shared = sub["upstream_entity_id"].isin(shared_ids).sum()
        lines = [f"{n_up} đối tác thượng nguồn"]
        if n_shared:
            lines.append(f"⚠ {n_shared} đối tác dùng chung")
        _add_box(fig, 0.80, ct_y[c], center_box_w, h_ct * 0.8, ACCENT, c, lines,
                 bold_border=True, fill_alpha=0.18)

    fig.add_annotation(x=0.20, y=1.07, text="<b>ĐỐI TÁC THƯỢNG NGUỒN</b>", showarrow=False, font=dict(size=9.5), opacity=0.7)
    fig.add_annotation(x=0.80, y=1.07, text="<b>CÔNG TY THÀNH VIÊN</b>", showarrow=False, font=dict(size=9.5), opacity=0.7)

    fig.add_trace(
        go.Scatter(
            x=hov_x, y=hov_y, mode="markers", marker=dict(size=1, opacity=0),
            hovertext=hov_text, hoverinfo="text", showlegend=False,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(visible=False, range=[-0.02, 1.02]),
        yaxis=dict(visible=False, range=[-0.06, 1.13]),
        margin=dict(l=6, r=6, t=6, b=6),
        hoverlabel=dict(align="left"),
    )
    return fig
