import pandas as pd
import plotly.graph_objects as go

from src.theme import plotly_template, risk_palette


def _risk_color(count: int, palette: dict) -> str:
    if count == 0:
        return palette["none"]
    if count == 1:
        return palette["low"]
    return palette["high"]


def build_risk_by_function_bar_v2(counts_by_name: pd.Series) -> go.Figure | None:
    """Bieu do so rui ro CADIVI_RCM theo tung khoi chuc nang (vc1_name) - nhan thang 1 Series
    da dem san (index = ten khoi, value = so rui ro), do trang tu tinh tu rcm.groupby("vc1_id")
    roi map sang ten. Truoc day ham nay dem theo risk_id cua Sheet1 (2_VC_Master) - da bo vi
    du lieu rui ro Sheet1 khong con dung nua (xem CLAUDE.md Muc 11.9), nay tach han khoi Sheet1."""
    palette = risk_palette()
    if counts_by_name.empty:
        return None

    counts = counts_by_name.sort_values()
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
