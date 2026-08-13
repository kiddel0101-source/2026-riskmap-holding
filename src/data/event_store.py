"""Luu lich su cac su kien rui ro nguoi dung da nhap (trang Su kien rui ro).

Day la NGOAI LE duy nhat trong app co ghi du lieu xuong dia/DB - khac voi nguyen tac
"khong luu file" o CLAUDE.md Muc 6 (nguyen tac do noi ve BAN SAO workbook nguon, khong
ap dung cho lich su su kien do chinh app tao ra). Xem CLAUDE.md Muc 11 de biet ly do
tam dung SQLite va cach doi sang Postgres sau nay (chi can doi bien moi truong
RISK_EVENTS_DB_URL, khong doi code o day).
"""

import json
import os
from datetime import datetime

import streamlit as st
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)

DEFAULT_DB_URL = "sqlite:///risk_events.db"

metadata = MetaData()
risk_events = Table(
    "risk_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime, nullable=False),
    Column("description", Text, nullable=False),
    Column("keywords", String, nullable=False),  # cac tu khoa, phan tach boi ";"
    Column("match_counts", Text, nullable=False),  # JSON: {"risks": 1, "value_chain": 1, "supply_chain": 1}
)

# Bang noi: chi danh dau 1 rui ro DA CO trong Risk Register la "lien quan den su kien" -
# khong copy du lieu rui ro, luon join song voi risks df dang tai tu Excel khi hien thi.
event_risk_confirmations = Table(
    "event_risk_confirmations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_id", Integer, ForeignKey("risk_events.id"), nullable=False),
    Column("risk_id", String, nullable=False),
    Column("confirmed_at", DateTime, nullable=False),
)

# Rui ro NHAP tao tu 1 hoat dong Chuoi gia tri khi xac nhan - day LA nguon du lieu chinh
# (khong co ban goc nao khac de join) vi rui ro nhap chua tung ton tai trong Risk Register.
event_draft_risks = Table(
    "event_draft_risks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_id", Integer, ForeignKey("risk_events.id"), nullable=False),
    Column("vc_node_id", String, nullable=False),
    Column("company_id", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("category_l1", String, nullable=True),
    Column("category_l2", String, nullable=True),
    # Ma nhom rui ro Tap doan (vd "4.3. Mua hang/dich vu") nguoi dung tu chon, dung de tra
    # "co the kich hoat" qua repository.risks_triggered_by_category - khac voi category_l1/l2
    # o tren (hop phan loai rieng, don gian cua app).
    Column("trigger_category", String, nullable=True),
    Column("created_at", DateTime, nullable=False),
)


def is_using_default_storage() -> bool:
    """True neu chua co RISK_EVENTS_DB_URL rieng - dang dung SQLite tam thoi, can canh
    bao nguoi dung vi du lieu co the mat khi deploy lai container khong gan volume."""
    return not os.getenv("RISK_EVENTS_DB_URL")


@st.cache_resource
def _get_engine():
    url = os.getenv("RISK_EVENTS_DB_URL", DEFAULT_DB_URL)
    engine = create_engine(url)
    metadata.create_all(engine)
    return engine


def save_event(description: str, keywords: list[str], match_counts: dict) -> int:
    engine = _get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            risk_events.insert().values(
                created_at=datetime.now(),
                description=description,
                keywords=";".join(keywords),
                match_counts=json.dumps(match_counts, ensure_ascii=False),
            )
        )
        return result.inserted_primary_key[0]


def confirm_risk(event_id: int, risk_id: str) -> None:
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(
            event_risk_confirmations.insert().values(
                event_id=event_id, risk_id=risk_id, confirmed_at=datetime.now()
            )
        )


def list_confirmed_risks() -> list[dict]:
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                event_risk_confirmations.c.risk_id,
                event_risk_confirmations.c.confirmed_at,
                risk_events.c.description.label("event_description"),
            )
            .join(risk_events, event_risk_confirmations.c.event_id == risk_events.c.id)
            .order_by(event_risk_confirmations.c.confirmed_at.desc())
        ).mappings().all()
    return [dict(r) for r in rows]


def save_draft_risk(
    event_id: int, vc_node_id: str, company_id: str, description: str,
    category_l1: str | None, category_l2: str | None, trigger_category: str | None,
) -> None:
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(
            event_draft_risks.insert().values(
                event_id=event_id,
                vc_node_id=vc_node_id,
                company_id=company_id,
                description=description,
                category_l1=category_l1,
                category_l2=category_l2,
                trigger_category=trigger_category,
                created_at=datetime.now(),
            )
        )


def list_draft_risks() -> list[dict]:
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            select(event_draft_risks).order_by(event_draft_risks.c.created_at.desc())
        ).mappings().all()
    return [dict(r) for r in rows]


def list_events(limit: int = 50) -> list[dict]:
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            select(risk_events).order_by(risk_events.c.created_at.desc()).limit(limit)
        ).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        d["keywords"] = [k for k in d["keywords"].split(";") if k]
        d["match_counts"] = json.loads(d["match_counts"])
        out.append(d)
    return out
