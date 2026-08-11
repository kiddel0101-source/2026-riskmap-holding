import pandas as pd
import plotly.graph_objects as go

from src.theme import hex_to_rgba, plotly_template, risk_palette, wrap_text


def _risk_color(count: int, palette: dict) -> str:
    if count == 0:
        return palette["none"]
    if count == 1:
        return palette["low"]
    return palette["high"]


def build_value_chain_map(
    vc: pd.DataFrame,
    risk_counts: pd.Series,
    company_id: str,
    *,
    categories: set[str] | None = None,
) -> go.Figure | None:
    """Ban do chuoi gia tri dang o chu nhat doc duoc: moi cot la 1 khoi chuc nang
    (vc_function), moi o la 1 hoat dong ghi ro TEN hoat dong (khong phai ma).

    Luu y ve du lieu: sheet Value_Chain_Master KHONG co cot the hien hoat dong nao noi
    tiep hoat dong nao, nen o day khong ve mui ten luong quy trinh (tranh bia ra quan he
    khong co trong du lieu). Cau truc that ma du lieu cung cap la: nhom theo khoi chuc
    nang + phan loai Primary/Support.
    """
    palette = risk_palette()
    rows = vc[vc["company_id"] == company_id]
    if categories:
        rows = rows[rows["vc_category"].isin(categories)]
    rows = rows.reset_index(drop=True)
    if rows.empty:
        return None

    functions = list(dict.fromkeys(rows["vc_function"].fillna("Khác")))
    n_cols = len(functions)
    by_fn = {fn: rows[rows["vc_function"].fillna("Khác") == fn].reset_index(drop=True) for fn in functions}
    max_rows = max(len(df) for df in by_fn.values())

    col_w = 1.0 / n_cols
    row_h = 1.0 / max_rows
    box_w, box_h = col_w * 0.90, row_h * 0.74

    fig = go.Figure()
    hov_x, hov_y, hov_text = [], [], []

    for ci, fn in enumerate(functions):
        cx = (ci + 0.5) * col_w
        df = by_fn[fn]

        fig.add_annotation(
            x=cx, y=1.045, xref="x", yref="y", text=f"<b>{fn.upper()}</b>",
            showarrow=False, font=dict(size=10), opacity=0.75,
        )
        # dai nen cho ca cot de mat nhin theo khoi, giam cam giac "chấm roi rac"
        fig.add_shape(
            type="rect", x0=cx - col_w * 0.47, x1=cx + col_w * 0.47, y0=-0.02, y1=1.01,
            line=dict(width=0), fillcolor=hex_to_rgba(palette["grey"], 0.07), layer="below",
        )

        for ri, r in df.iterrows():
            cy = 1 - (ri + 0.5) * row_h
            count = int(risk_counts.get(r["vc_node_id"], 0))
            color = _risk_color(count, palette)
            is_support = r.get("vc_category") == "Support"

            fig.add_shape(
                type="rect",
                x0=cx - box_w / 2, x1=cx + box_w / 2,
                y0=cy - box_h / 2, y1=cy + box_h / 2,
                line=dict(color=color, width=1.6, dash="dot" if is_support else "solid"),
                fillcolor=hex_to_rgba(color, 0.14),
                layer="below",
            )
            label = wrap_text(r.get("vc_sub_function") or r["vc_node_id"], width=22, max_lines=2)
            fig.add_annotation(
                x=cx, y=cy + box_h * 0.06, xref="x", yref="y", text=label,
                showarrow=False, font=dict(size=10.5, color=color), align="center",
            )
            badge = f"{r['vc_node_id']}"
            if count:
                badge += f"  ·  {count} rủi ro"
            fig.add_annotation(
                x=cx, y=cy - box_h * 0.30, xref="x", yref="y", text=badge,
                showarrow=False, font=dict(size=8.5, color=color), opacity=0.85,
            )

            hov_x.append(cx)
            hov_y.append(cy)
            hov_text.append(
                f"<b>{r['vc_node_id']} — {r.get('vc_sub_function') or ''}</b><br>"
                f"{r.get('vc_category')} · {fn}<br>"
                f"{r.get('activity_description') or '—'}<br>"
                f"Chủ trì: {r.get('process_owner') or '—'}<br>"
                f"Rủi ro liên kết: {count}"
                + (f"<br>⚠ {r['dependency_note']}" if pd.notna(r.get("dependency_note")) else "")
            )

    fig.add_trace(
        go.Scatter(
            x=hov_x, y=hov_y, mode="markers",
            marker=dict(size=1, opacity=0),
            hovertext=hov_text, hoverinfo="text", showlegend=False,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(visible=False, range=[0, 1], fixedrange=False),
        yaxis=dict(visible=False, range=[-0.04, 1.09]),
        margin=dict(l=6, r=6, t=6, b=6),
        hoverlabel=dict(align="left"),
    )
    return fig


def build_risk_by_function_bar(
    vc: pd.DataFrame, risks_exploded: pd.DataFrame, company_id: str
) -> go.Figure | None:
    """Xep hang khoi chuc nang theo so rui ro -> chi ro diem nong can uu tien."""
    palette = risk_palette()
    nodes = vc[vc["company_id"] == company_id]
    if nodes.empty:
        return None

    joined = risks_exploded.merge(nodes[["vc_node_id", "vc_function"]], on="vc_node_id")
    counts = (
        joined.groupby("vc_function")["risk_id"].nunique()
        if not joined.empty
        else pd.Series(dtype=int)
    )
    all_fns = list(dict.fromkeys(nodes["vc_function"].fillna("Khác")))
    counts = counts.reindex(all_fns, fill_value=0).sort_values()

    colors = [_risk_color(int(v), palette) for v in counts.values]
    fig = go.Figure(
        go.Bar(
            x=counts.values, y=counts.index, orientation="h",
            marker=dict(color=colors),
            text=[str(int(v)) for v in counts.values], textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} rủi ro<extra></extra>",
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(title="Số rủi ro", dtick=1, range=[0, max(1, int(counts.max())) * 1.25]),
        yaxis=dict(title=None),
        margin=dict(l=6, r=6, t=6, b=6),
        showlegend=False,
    )
    return fig
