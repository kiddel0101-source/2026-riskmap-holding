import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.config import RAG_COLORS, GREY
from src.theme import plotly_template

GREEN = RAG_COLORS["Green"]
AMBER = RAG_COLORS["Amber"]
RED = RAG_COLORS["Red"]

_BAND_COLORSCALE = [
    [0.0, GREEN], [0.49, GREEN],
    [0.50, AMBER], [0.99, AMBER],
    [1.0, RED],
]


def _score_band(likelihood: int, impact: int) -> int:
    score = likelihood * impact
    if score <= 6:
        return 0
    if score <= 12:
        return 1
    return 2


def build_risk_heatmap(risks: pd.DataFrame, mode: str = "inherent") -> go.Figure:
    """Luoi 5x5 Likelihood x Impact: nen o to theo band co dinh (xanh/amber/do),
    so trong o = so rui ro thuc te roi vao o do."""
    lik_col, imp_col = f"{mode}_likelihood", f"{mode}_impact"
    sub = risks.dropna(subset=[lik_col, imp_col])

    counts = np.zeros((5, 5), dtype=int)
    band = np.zeros((5, 5), dtype=int)
    for impact in range(1, 6):
        for likelihood in range(1, 6):
            band[impact - 1, likelihood - 1] = _score_band(likelihood, impact)
    for _, row in sub.iterrows():
        likelihood, impact = int(row[lik_col]), int(row[imp_col])
        counts[impact - 1, likelihood - 1] += 1

    text = np.where(counts > 0, counts.astype(str), "")

    fig = go.Figure(
        go.Heatmap(
            z=band,
            x=list(range(1, 6)),
            y=list(range(1, 6)),
            colorscale=_BAND_COLORSCALE,
            zmin=0,
            zmax=2,
            showscale=False,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=17, color="white"),
            customdata=counts,
            hovertemplate="Likelihood %{x} × Impact %{y}<br>Số rủi ro: %{customdata}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(title="Likelihood", dtick=1, range=[0.5, 5.5]),
        yaxis=dict(title="Impact", dtick=1, range=[0.5, 5.5]),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def build_risk_migration_chart(risks: pd.DataFrame) -> go.Figure:
    """Moi rui ro co du 2 diem (inherent & residual) ve 1 mui ten the hien hieu qua kiem soat."""
    sub = risks.dropna(
        subset=["inherent_likelihood", "inherent_impact", "residual_likelihood", "residual_impact"]
    ).copy()

    fig = go.Figure()
    if sub.empty:
        fig.update_layout(template=plotly_template())
        return fig

    rag_color = sub["status_rag"].map(RAG_COLORS).fillna(GREY)
    for (_, row), color in zip(sub.iterrows(), rag_color):
        fig.add_annotation(
            x=row["residual_likelihood"], y=row["residual_impact"],
            ax=row["inherent_likelihood"], ay=row["inherent_impact"],
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.6,
            arrowcolor=color, opacity=0.85,
        )

    fig.add_trace(
        go.Scatter(
            x=sub["inherent_likelihood"], y=sub["inherent_impact"],
            mode="markers", name="Inherent",
            marker=dict(symbol="circle", size=10, color=GREY, line=dict(width=1, color="white")),
            customdata=sub[["risk_id", "inherent_score"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Inherent — L%{x} × I%{y} = %{customdata[1]}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["residual_likelihood"], y=sub["residual_impact"],
            mode="markers", name="Residual",
            marker=dict(symbol="diamond", size=10, color=rag_color, line=dict(width=1, color="white")),
            customdata=sub[["risk_id", "residual_score"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Residual — L%{x} × I%{y} = %{customdata[1]}<extra></extra>",
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(title="Likelihood", range=[0.5, 5.5], dtick=1),
        yaxis=dict(title="Impact", range=[0.5, 5.5], dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig
