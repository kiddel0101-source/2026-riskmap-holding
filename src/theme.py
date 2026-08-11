import streamlit as st

# Bang mau rui ro rieng cho tung theme: ban dark sang hon de doc duoc tren nen toi
RISK_PALETTE_LIGHT = {"none": "#2E7D5B", "low": "#B7860B", "high": "#C0392B", "grey": "#6B7280"}
RISK_PALETTE_DARK = {"none": "#5BBE90", "low": "#E0B85B", "high": "#E8705E", "grey": "#9CA3AF"}


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def risk_palette() -> dict:
    return RISK_PALETTE_DARK if is_dark() else RISK_PALETTE_LIGHT


def plotly_template() -> str:
    """Chon template Plotly khop voi theme sang/toi hien tai cua Streamlit."""
    return "plotly_dark" if is_dark() else "plotly_white"


def chart_config() -> dict:
    """Cau hinh modebar Plotly dung chung: giu cac nut hover/zoom/pan huu ich, an bot nut thua."""
    return {
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def wrap_text(text: str, width: int = 20, max_lines: int = 3) -> str:
    """Ngat dong theo tu de nhan vua trong o, cat bot neu qua dai."""
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        candidate = f"{cur} {w}".strip()
        if len(candidate) <= width:
            cur = candidate
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (len(words) > sum(len(x.split()) for x in lines)):
        lines[-1] = lines[-1][: width - 1] + "…"
    return "<br>".join(lines)
