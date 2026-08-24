import pandas as pd
import plotly.graph_objects as go

from src.theme import hex_to_rgba, nz, plotly_template, risk_palette, wrap_text

# Thu tu chuan Porter's Value Chain (da chot voi nguoi dung): hoat dong chinh theo dong
# chay Inbound -> Operations -> Outbound -> Marketing & Sales -> Service, 2 hoat dong ho
# tro (Procurement, Technology Development) xep cuoi. Ap dung co dinh cho moi cong ty,
# khong phu thuoc thu tu dong trong sheet Excel nguon.
_FUNCTION_ORDER = [
    "Inbound Logistics", "Operations", "Outbound Logistics", "Marketing & Sales", "Service",
    "Procurement", "Technology Development",
]


def _sort_functions(functions: list[str]) -> list[str]:
    order_index = {name.lower(): i for i, name in enumerate(_FUNCTION_ORDER)}
    return sorted(functions, key=lambda fn: order_index.get(fn.lower(), len(_FUNCTION_ORDER)))


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

    functions = _sort_functions(list(dict.fromkeys(rows["vc_function"].fillna("Khác"))))
    n_cols = len(functions)
    by_fn = {fn: rows[rows["vc_function"].fillna("Khác") == fn].reset_index(drop=True) for fn in functions}
    max_rows = max(len(df) for df in by_fn.values())

    col_w = 1.0 / n_cols
    row_h = 1.0 / max_rows
    box_w, box_h = col_w * 0.90, row_h * 0.74

    fig = go.Figure()
    hov_x, hov_y, hov_text, hov_ids = [], [], [], []

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
            label = wrap_text(nz(r.get("vc_sub_function"), r["vc_node_id"]), width=22, max_lines=2)
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
            hov_ids.append(r["vc_node_id"])
            hov_text.append(
                f"<b>{r['vc_node_id']} — {nz(r.get('vc_sub_function'), '')}</b><br>"
                f"{nz(r.get('vc_category'))} · {fn}<br>"
                f"{nz(r.get('activity_description'))}<br>"
                f"Chủ trì: {nz(r.get('process_owner'))}<br>"
                f"Rủi ro liên kết: {count}"
                + (f"<br>⚠ {r['dependency_note']}" if pd.notna(r.get("dependency_note")) else "")
            )

    fig.add_trace(
        go.Scatter(
            x=hov_x, y=hov_y, mode="markers",
            marker=dict(size=42, opacity=0),
            customdata=hov_ids,
            hovertext=hov_text, hoverinfo="text", showlegend=False,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(visible=False, range=[0, 1], fixedrange=False),
        yaxis=dict(visible=False, range=[-0.04, 1.09]),
        margin=dict(l=6, r=6, t=6, b=6),
        hoverlabel=dict(align="left"),
        clickmode="event+select",
    )
    return fig


# Thu tu 9 khoi Porter day du cho trang Chuoi gia tri (Phan 3), phan loai theo MA khoi
# (vc1_id) chu KHONG theo ten hien thi (vc1_name) - ten hien thi tren SharePoint da bi doi
# it nhat 3 lan ("Vận hành / Sản xuất" -> "Sản xuất", "Marketing & Bán hàng" -> "Bán hàng",
# "Thu mua" -> "Mua hàng"...) trong khi ma (IL/OP/OL/MS/SV/PR/TD/FI/HR, cung la tien to cua
# vc2_id nhu "OP-001") on dinh qua tat ca cac lan doi ten. Rieng cho Phan 3 - KHONG dung
# chung voi _FUNCTION_ORDER/build_value_chain_map o tren (nguon 2_Value_Chain_Master khac,
# cac trang Trang chu/Su kien rui ro van dung ham cu, khong bi anh huong).
_ID_ORDER_V2 = ["IL", "OP", "OL", "MS", "SV", "PR", "TD", "FI", "HR"]
# 5 ma CHINH (Primary) + 4 ma HO TRO (Support) theo dung khung Porter - day la phan loai o
# CAP KHOI, khac voi cot "category" (Phan loai Chinh/Ho tro) trong tung dong du lieu von la
# phan loai o CAP HOAT DONG (vd hoat dong "PR-003" thuoc khoi Ho tro "Mua hàng" nhung ban
# than no van co the duoc gan category="Hỗ trợ" trong du lieu - 2 truc doc lap nhau).
_PRIMARY_IDS_V2 = set(_ID_ORDER_V2[:5])
_SUPPORT_IDS_V2 = set(_ID_ORDER_V2[5:])


def _sort_ids_v2(ids: list[str]) -> list[str]:
    order_index = {code: i for i, code in enumerate(_ID_ORDER_V2)}
    return sorted(ids, key=lambda code: order_index.get(code, len(_ID_ORDER_V2)))


def build_value_chain_blocks(vc2: pd.DataFrame, block_colors: dict[str, str] | None = None) -> go.Figure:
    """Ban do CAP 1 (rut gon) cho trang Chuoi gia tri: moi khoi chuc nang la 1 box duy nhat.
    2 hang dung khung Porter: 5 khoi CHINH o tren, 4 khoi HO TRO o duoi. Bam vao 1 box
    (customdata = ten khoi) de trang boc danh sach hoat dong (sub-value chain) trong khoi do
    ngay ben duoi - KHONG dung hop thoai (da chot voi nguoi dung). Luon co du 9 khoi, khong
    loc theo "Nhóm hoạt động" (bo loc do chi anh huong danh sach hoat dong hien ra sau khi
    bam, khong an bot khoi).

    `block_colors` (tuy chon, xem CLAUDE.md Muc 11.4) la dict {vc1_id: hex_color} tu
    `risk_dialog.rcm_block_health_color()` - khoi KHONG co trong dict (chua co du lieu 7_RCM
    nao) giu mau TRUNG TINH nhu truoc; da chot voi nguoi dung mo rong mau nguong kiem soat tu
    cap hoat dong len ca cap khoi."""
    palette = risk_palette()
    neutral = palette["grey"]
    nodes = vc2.drop_duplicates(subset=["vc2_id"])
    counts_by_id = nodes.groupby("vc1_id").size()
    # 1 vc1_id ung dung 1 vc1_name trong du lieu hien tai - lay ten hien thi de ve, nhung
    # phan loai/sap xep van dua theo ma (xem ghi chu o _ID_ORDER_V2).
    id_to_name = dict(
        nodes.drop_duplicates(subset=["vc1_id"])[["vc1_id", "vc1_name"]].itertuples(index=False)
    )

    all_ids = list(dict.fromkeys(nodes["vc1_id"].fillna("KHÁC")))
    primary_ids = _sort_ids_v2([i for i in all_ids if i in _PRIMARY_IDS_V2])
    # Bat ky ma nao khong khop danh sach Chinh (gom ca "KHÁC" du phong) deu xep vao hang Ho
    # tro, tranh bi RUNG mat khoi bieu do neu du lieu nguon phat sinh ma khoi moi.
    support_ids = _sort_ids_v2([i for i in all_ids if i not in primary_ids])
    bands = []
    if primary_ids:
        bands.append(("HOẠT ĐỘNG CHÍNH", primary_ids))
    if support_ids:
        bands.append(("HOẠT ĐỘNG HỖ TRỢ", support_ids))

    GAP = 0.16
    band_h = (1.0 - GAP * (len(bands) - 1)) / len(bands) if bands else 1.0
    box_h = band_h * 0.60

    fig = go.Figure()
    hov_x, hov_y, hov_text, hov_ids = [], [], [], []

    band_y1 = 1.0
    for band_label, ids in bands:
        n_cols = len(ids)
        col_w = 1.0 / n_cols
        cy = band_y1 - band_h / 2
        if len(bands) > 1:
            fig.add_annotation(
                x=0, y=band_y1 + 0.03, xref="x", yref="y", text=f"<b>{band_label}</b>",
                showarrow=False, font=dict(size=11, color=neutral), opacity=0.95, xanchor="left",
            )
        for ci, code in enumerate(ids):
            fn = id_to_name.get(code, code)
            cx = (ci + 0.5) * col_w
            box_w = col_w * 0.86
            color = (block_colors or {}).get(code) or neutral
            fig.add_shape(
                type="rect", x0=cx - box_w / 2, x1=cx + box_w / 2, y0=cy - box_h / 2, y1=cy + box_h / 2,
                line=dict(color=color, width=1.8), fillcolor=hex_to_rgba(color, 0.10), layer="below",
            )
            label_wrap_width = max(12, min(24, round(box_w * 150)))
            header = wrap_text(fn.upper(), width=label_wrap_width, max_lines=2)
            fig.add_annotation(
                x=cx, y=cy + box_h * 0.18, xref="x", yref="y", text=f"<b>{header}</b>",
                showarrow=False, font=dict(size=11, color=color), align="center",
            )
            n_act = int(counts_by_id.get(code, 0))
            fig.add_annotation(
                x=cx, y=cy - box_h * 0.32, xref="x", yref="y", text=f"{n_act} hoạt động",
                showarrow=False, font=dict(size=9.5, color=color), opacity=0.85,
            )

            hov_x.append(cx)
            hov_y.append(cy)
            hov_ids.append(fn)
            hov_text.append(f"<b>{fn}</b><br>{n_act} hoạt động — bấm để xem danh sách")

        band_y1 -= (band_h + GAP)

    fig.add_trace(
        go.Scatter(
            x=hov_x, y=hov_y, mode="markers",
            marker=dict(size=70, opacity=0),
            customdata=hov_ids,
            hovertext=hov_text, hoverinfo="text", showlegend=False,
        )
    )
    fig.update_layout(
        template=plotly_template(),
        xaxis=dict(visible=False, range=[0, 1], fixedrange=False),
        yaxis=dict(visible=False, range=[-0.04, 1.07]),
        margin=dict(l=6, r=6, t=6, b=6),
        hoverlabel=dict(align="left"),
        clickmode="event+select",
    )
    return fig


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
