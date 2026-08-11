SHAREPOINT_SHARE_URL = (
    "https://gelexvn.sharepoint.com/:x:/r/sites/gex.qtrr/Shared%20Documents/General/"
    "7.%20C%C3%B4ng%20vi%E1%BB%87c%20kh%C3%A1c/25.%20Mindmap%20r%E1%BB%A7i%20ro%20h%E1%BB%87%20th%E1%BB%91ng/"
    "0.%20GELEX_Risk_Map_Database.xlsx?d=w97bbddd67a644ca3961e22251fe307e8&csf=1&web=1&e=fUbgzW"
)
GRAPH_ACCOUNT = "DAS_U1"
CACHE_TTL_SECONDS = 900  # 15 phut

# Vi tri dong header (0-indexed) khac nhau giua cac sheet: 1_Company_Master va
# 6_Risk_Appetite_Threshold chi co 1 dong tieu de + 1 dong trong truoc header (header=2);
# cac sheet con lai co them 1 dong ghi chu huong dan truoc dong trong (header=3).
# 7_RCM co header long nhau -> de lai dot sau, khong doc trong MVP nay.
SHEET_HEADER_ROW = {
    "1_Company_Master": 2,
    "2_Value_Chain_Master": 3,
    "3_Supply_Chain_Master": 3,
    "4_Risk_Register": 3,
    "5_KRI_Library": 3,
    "6_Risk_Appetite_Threshold": 2,
}

RAG_COLORS = {
    "Red": "#C0392B",
    "Amber": "#B7860B",
    "Green": "#2E7D5B",
    "Chưa đánh giá": "#8B93A3",
}
GREY = "#8B93A3"
ACCENT = "#B4551F"

# Doi ten cot ky thuat sang nhan tieng Viet khi hien thi bang cho nguoi dung
COLUMN_LABELS = {
    # chung
    "company_id": "Công ty",
    "company_name": "Tên công ty",
    "bloc": "Khối",
    "tier_level": "Cấp",
    # value chain
    "vc_node_id": "Mã hoạt động",
    "vc_category": "Nhóm",
    "vc_function": "Khối chức năng",
    "vc_sub_function": "Hoạt động",
    "activity_description": "Mô tả hoạt động",
    "process_owner": "Đơn vị chủ trì",
    "dependency_note": "Ghi chú phụ thuộc",
    # supply chain
    "sc_link_id": "Mã liên kết",
    "upstream_entity_id": "Đối tác thượng nguồn",
    "upstream_entity_type": "Loại đối tác",
    "downstream_entity_id": "Bên hạ nguồn",
    "sc_tier": "Tier",
    "input_output_type": "Đầu vào / đầu ra",
    "single_source_flag": "Phụ thuộc một nguồn",
    "geographic_origin": "Nguồn gốc",
    "lead_time_days": "Lead time (ngày)",
    "contract_type": "Loại hợp đồng",
    "substitutability": "Khả năng thay thế",
    "annual_volume_value": "Giá trị/năm",
    # risk
    "risk_id": "Mã rủi ro",
    "risk_category_l1": "Nhóm rủi ro",
    "risk_category_l2": "Loại rủi ro",
    "risk_event_l3": "Sự kiện rủi ro",
    "root_cause": "Nguyên nhân gốc",
    "impact_description": "Mô tả tác động",
    "impact_area": "Phạm vi tác động",
    "inherent_score": "Điểm gộp",
    "residual_score": "Điểm còn lại",
    "inherent_likelihood": "Khả năng (gộp)",
    "inherent_impact": "Tác động (gộp)",
    "residual_likelihood": "Khả năng (còn lại)",
    "residual_impact": "Tác động (còn lại)",
    "existing_controls": "Kiểm soát hiện có",
    "risk_owner": "Người phụ trách",
    "status_rag": "Trạng thái",
    "last_review_date": "Kỳ rà soát",
    "review_cycle": "Chu kỳ rà soát",
    "linked_dimension": "Chiều liên kết",
}


def vi(df):
    """Doi ten cot sang tieng Viet de hien thi (khong doi du lieu goc)."""
    return df.rename(columns=COLUMN_LABELS)
