SHAREPOINT_SHARE_URL = (
    "https://gelexvn.sharepoint.com/:x:/s/gex.qtrr/"
    "IQDWQHZUIRVpTL-ADxqLD5YCAWbE3wwxAGLMmuV1RFokV6M?&e=5b7kH6"
)
GRAPH_ACCOUNT = "DAS_U1"
CACHE_TTL_SECONDS = 900  # 15 phut

# Vi tri dong header (0-indexed) khac nhau giua cac sheet: 1_Company_Master chi co 1 dong
# tieu de + 1 dong trong truoc header (header=2); cac sheet con lai co them 1 dong ghi chu
# huong dan truoc dong trong (header=3).
#
# ⚠️ Workbook nguon dang duoc phu trach du lieu tai cau truc TRUC TIEP, da gap 3 lan lien
# tiep trong cung du an (xem CLAUDE.md Muc 11.3/11.4/11.5): sheet "2_Value_Chain_Master"
# (mo hinh Chuoi gia tri CU theo cong ty, dung o Trang chu + Su kien rui ro) va sheet
# "Risk_Linkages" (quan he rui ro-kich-hoat-rui-ro) đa bi XOA HAN, khong co sheet thay the -
# nguoi dung da xac nhan go bo hoan toan tinh nang phu thuoc 2 sheet nay khoi app (xem Muc
# 11.5). "6_Risk_Appetite_Threshold" cung khong con nhung chua tung duoc code nao doc toi.
SHEET_HEADER_ROW = {
    "1_Company_Master": 2,
    "3_Supply_Chain_Master": 3,
    "4_Risk_Register": 3,
    "5_KRI_Library": 3,
    # Mo hinh Chuoi gia tri Porter 9 khoi dung chung toan Tap doan (xem CLAUDE.md Muc 11.2/
    # 11.3). Header dong dau tien. Sheet nay ten cu la "Sheet1", da doi ten thanh
    # "2_VC_Master" tren SharePoint.
    "2_VC_Master": 0,
    # Ma tran kiem soat rui ro (xem CLAUDE.md Muc 11.4) - tieu de nam ngay dong dau tien du
    # co 2 dong ghi chu huong dan phia tren (khong tinh vao header), da kiem tra truc tiep.
    # Ten cu la "7_RCM", da doi ten thanh "{Ten cong ty}_RCM" - hien CHI co "CADIVI_RCM"
    # (nguoi dung xac nhan chua co cong ty nao khac), tach theo tung cong ty tren SharePoint.
    "CADIVI_RCM": 2,
    # Cac yeu to dan phat (PESTEL) noi voi danh muc rui ro (xem CLAUDE.md Muc 11.11) - header
    # o dong 4 Excel (2 dong tieu de + 1 dong vi du minh hoa phia tren), da kiem tra truc tiep.
    "Risk_Driver_Library": 3,
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
    "risk_category_id": "Danh mục rủi ro",
    "risk_desc": "Mô tả (theo danh mục)",
    # yeu to dan phat (Risk_Driver_Library)
    "driver_category": "Nhóm PESTEL",
    "driver_name": "Tên yếu tố dẫn phát",
    "driver_details": "Chi tiết yếu tố dẫn phát",
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
