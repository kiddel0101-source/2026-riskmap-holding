from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.config import CACHE_TTL_SECONDS, GRAPH_ACCOUNT, SHAREPOINT_SHARE_URL

load_dotenv()


class WorkbookFetchError(RuntimeError):
    pass


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Đang tải dữ liệu từ SharePoint...")
def fetch_workbook() -> tuple[bytes, datetime]:
    """Tai noi dung workbook truc tiep tu SharePoint vao bo nho (khong ghi file cuc bo).
    Duoc cache boi Streamlit (TTL) de tranh goi lai SharePoint tren moi lan rerun; nut
    "Lam moi du lieu" xoa cache de ep tai lai ngay."""
    from gex_msgraph import GraphClient

    client = GraphClient(GRAPH_ACCOUNT)
    try:
        data = client.download_sync(share_url=SHAREPOINT_SHARE_URL)
        return data, datetime.now()
    except Exception as exc:
        raise WorkbookFetchError(f"Không tải được dữ liệu từ SharePoint: {exc}") from exc
    finally:
        client.close_sync()


def refresh_workbook() -> None:
    fetch_workbook.clear()
