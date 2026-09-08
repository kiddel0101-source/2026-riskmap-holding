import pandas as pd
import plotly.graph_objects as go

from src.theme import plotly_template, risk_palette


def _risk_color(count: int, palette: dict) -> str:
    if count == 0:
        return palette["none"]
    if count == 1:
        return palette["low"]
    return palette["high"]


def build_risk_by_function_bar_v2(vc2: pd.DataFrame) -> go.Figure | None:
    """Nhu build_risk_by_function_bar nhung theo Sheet1 - dem so rui ro DUY NHAT (risk_id)
    gan truc tiep theo tung khoi vc1_name, khong can join qua Risk Register."""
    palette = risk_palette()
    if vc2.empty:
        return None

    with_risk = vc2.dropna(subset=["risk_id"])
    counts = with_risk.groupby("vc1_name")["risk_id"].nunique() if not with_risk.empty else pd.Series(dtype=int)
    all_fns = list(dict.fromkeys(vc2["vc1_name"].fillna("Khác")))
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
