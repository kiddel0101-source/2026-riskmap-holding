# CLAUDE.md — Hướng dẫn làm việc trên dự án Risk Map GELEX

> File này dành cho Claude đọc mỗi khi mở dự án. Người dùng dự án này là **cán bộ nghiệp vụ
> (business), không phải lập trình viên** — toàn bộ code sẽ do AI viết. Vì vậy các quy tắc ở
> Mục 1 là **bắt buộc**, không được bỏ qua để "làm cho nhanh".

---

## 1. QUY TRÌNH BẮT BUỘC — không được nhảy bước

Mỗi khi người dùng yêu cầu thêm/sửa tính năng, đi đúng 6 bước sau:

### Bước 1 — Phỏng vấn kỹ yêu cầu (KHÔNG được tự suy diễn)

- Hỏi cho đến khi hiểu rõ: **ai xem, xem để quyết định điều gì, cần thấy con số/hình gì**.
- Nếu yêu cầu liên quan tới giao diện, biểu đồ, báo cáo mẫu → **chủ động xin ảnh chụp màn
  hình / file mẫu / link tham khảo**. Nói thẳng: *"Anh/chị gửi em ảnh mẫu để em làm đúng ý nhé."*
- Nếu người dùng nói chung chung ("làm đẹp hơn", "thêm insight") → hỏi lại cụ thể, đừng đoán.
- Dùng `AskUserQuestion` khi có 2–4 phương án rõ ràng để người dùng chọn nhanh.

### Bước 2 — Lập kế hoạch + VẼ MOCKUP

- Vào plan mode (`EnterPlanMode`) để dựng kế hoạch.
- **Luôn vẽ mockup trước khi viết code thật.** Cách làm: viết 1 file HTML wireframe (dùng SVG
  vẽ đúng hình dạng biểu đồ dự kiến) rồi publish bằng công cụ `Artifact` và gửi link cho
  người dùng xem.
- Mockup phải mô tả rõ: bố cục từng trang, loại biểu đồ, quy tắc màu, bộ lọc, tương tác.
- Đã có tiền lệ: mockup đặc tả giao diện 3 trang MVP từng được duyệt theo cách này.

### Bước 3 — Chờ người dùng XÁC NHẬN

- Không viết code sản phẩm khi người dùng chưa nói "ok/duyệt/làm đi".
- Người dùng có thể yêu cầu đổi thứ tự, đổi biểu đồ → sửa mockup rồi trình lại.

### Bước 4 — Code

- Viết theo đúng mockup đã duyệt. Lệch ý phải báo trước, không tự ý đổi.

### Bước 5 — TEST KỸ, tự sửa lỗi trước khi báo cáo

- Chạy smoke test Python (gọi thẳng các hàm với dữ liệu thật) để bắt lỗi runtime.
- Chạy app rồi kiểm tra bằng trình duyệt thật (Playwright): duyệt hết các trang, **bấm thử
  bộ lọc thật**, chụp màn hình và **tự nhìn ảnh** để phát hiện lỗi trình bày (chữ tràn khung,
  đường kẻ đè chữ, biểu đồ trắng...).
- Kiểm tra cả giao diện **sáng và tối**.
- Chỉ báo "xong" khi đã tự sửa hết lỗi mình tìm ra. Nếu còn lỗi chưa sửa được → nói thẳng.

### Bước 6 — MỞ APP CHO NGƯỜI DÙNG + KIỂM TRA GIT

- **Luôn khởi động app và đưa link** (ví dụ `http://localhost:8600`) — không bắt người dùng
  tự chạy lệnh.
- Nếu người dùng báo trùng port → tắt hẳn tiến trình cũ rồi chạy port khác.
- **Sau mỗi lần cập nhật, kiểm tra tình trạng git** (`git status`), báo rõ file nào đã đổi.
  Chỉ commit khi người dùng yêu cầu.
  ⚠️ **Hiện thư mục này CHƯA phải git repo** — cần chạy `git init` một lần trước khi luật này
  có tác dụng. Hỏi người dùng trước khi khởi tạo.

### Cách giao tiếp

- Trả lời bằng **tiếng Việt**, diễn giải theo ngôn ngữ nghiệp vụ, hạn chế thuật ngữ kỹ thuật.
- Khi báo lỗi/hạn chế của dữ liệu → nói thẳng, kèm con số cụ thể.

---

## 2. Dự án này là gì

Web app Streamlit trực quan hoá **chuỗi giá trị – chuỗi cung ứng – bản đồ rủi ro** của Tập
đoàn GELEX, đọc dữ liệu trực tiếp từ file Excel trên SharePoint.

Thứ tự trang theo hướng nhìn top-down đã chốt với người dùng:
**Chuỗi cung ứng → Chuỗi giá trị → Danh mục rủi ro.**

Nguồn dữ liệu: `0. GELEX_Risk_Map_Database.xlsx` trên SharePoint (link cấu hình trong
`src/config.py`), lấy qua thư viện nội bộ `gex-msgraph`.

---

## 3. Chạy app

```bash
# Cài lần đầu
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# Chạy (đổi port nếu trùng)
./.venv/Scripts/python.exe -m streamlit run app.py --server.port 8600 --server.headless true
```

Thông tin đăng nhập SharePoint nằm trong `.env` (đã được `.gitignore` loại trừ — **tuyệt đối
không commit file này, không in nội dung ra màn hình**).

---

## 4. Cấu trúc file

```
app.py                      Điểm vào, khai báo điều hướng bằng st.navigation
pages/
  0_Trang_chu.py            Tổng quan + KPI + link sang các trang
  1_Chuoi_cung_ung.py       2 chế độ xem: Theo công ty / Toàn hệ thống
  2_Chuoi_gia_tri.py        Bản đồ hoạt động theo khối chức năng
  3_Danh_muc_rui_ro.py      Bảng rủi ro + heatmap + risk migration
src/
  config.py                 Link SharePoint, vị trí dòng header từng sheet, màu RAG,
                            COLUMN_LABELS + hàm vi() đổi tên cột sang tiếng Việt
  theme.py                  Nhận biết theme sáng/tối, bảng màu, ngắt dòng chữ trong ô
  insights.py               Tự phát hiện điểm bất thường để cảnh báo trên giao diện
  data/loader.py            Tải file từ SharePoint vào bộ nhớ (có cache)
  data/repository.py        Đọc từng sheet thành DataFrame, các phép nối dữ liệu
  components/filters.py     Bộ chọn công ty dùng chung giữa các trang
  viz/supply_chain.py       Sơ đồ chuỗi cung ứng (theo công ty + toàn hệ thống)
  viz/value_chain.py        Bản đồ chuỗi giá trị + biểu đồ rủi ro theo khối chức năng
  viz/risk.py               Heatmap Likelihood × Impact + risk migration
```

---

## 5. Đặc thù DỮ LIỆU — đọc kỹ trước khi sửa

| Vấn đề | Chi tiết |
|---|---|
| **Dòng header khác nhau giữa các sheet** | `1_Company_Master` và `6_Risk_Appetite_Threshold` dùng `header=2`; các sheet còn lại `header=3` (do có thêm dòng ghi chú). Đã khai báo sẵn trong `SHEET_HEADER_ROW`. |
| **Không có dữ liệu thứ tự quy trình** | Sheet Value Chain **KHÔNG** có cột nào chỉ hoạt động nào nối tiếp hoạt động nào. ⚠️ **Tuyệt đối không vẽ mũi tên luồng quy trình** — từng mắc lỗi này. Chỉ nhóm theo `vc_function` + `vc_category`. |
| **Dữ liệu mới có 2 công ty** | Chỉ `CADIVI` và `EMIC` có đủ chuỗi giá trị/rủi ro. `GELEX` chỉ xuất hiện ở 1 dòng góp vốn trong chuỗi cung ứng. `GEE`, `GEL` chưa có gì → giao diện phải chịu được trạng thái rỗng. |
| **`vc_node_id` trong Risk Register là đa giá trị** | Dạng `"MS-001, MS-002"` → phải tách bằng `repository.risks_exploded_by_vc_node()`. |
| **`sc_link_id`** | Là đơn giá trị, không cần tách. |
| **Cột rỗng/placeholder** | `criticality_level` toàn dấu `-`; `annual_volume_value` rỗng hoàn toàn; `lead_time_days` chỉ có 4/10 dòng → đừng làm biểu đồ dựa trên các cột này. |
| **Rủi ro chưa chấm điểm** | Chỉ 8/22 rủi ro có điểm inherent, 6/22 có residual → mọi biểu đồ điểm số **phải ghi rõ đang vẽ bao nhiêu trên tổng bao nhiêu**, không im lặng bỏ qua. |
| **Sheet `7_RCM`** | Header lồng nhau 2 tầng, **chưa xử lý**. Muốn dùng phải viết hàm đọc riêng. |

---

## 6. Bẫy KỸ THUẬT đã gặp — đừng lặp lại

| Bẫy | Cách xử lý đúng |
|---|---|
| `gex-msgraph` không có trên PyPI | Cài qua git URL (xem `requirements.txt`). Máy cài phải vào được GitHub nội bộ. |
| Tên tài khoản Graph | Biến môi trường là `MS_DAS_U1_*` → phải gọi `GraphClient("DAS_U1")`, không phải `"U1"`. |
| API Excel của Graph không dùng được | `list_excel_sheets` / `read_excel` trả lỗi 400 *"not supported for AAD accounts"* trên tenant này. → Chỉ dùng `download_sync()` lấy bytes rồi đọc bằng `pandas.read_excel`. |
| Hàm của thư viện là async | Dùng bản `*_sync` (`download_sync`, `close_sync`), nhớ `close_sync()` trong `finally`. |
| **Không lưu file xuống đĩa** | Người dùng yêu cầu luôn dùng dữ liệu trực tiếp trên SharePoint. Loader trả về **bytes trong bộ nhớ**, cache bằng `st.cache_data(ttl=900)`. Không tạo thư mục `data/`. |
| pandas 3.x | `Styler.applymap` đã bị bỏ → dùng `Styler.map`. |
| Streamlit 1.61 | `use_container_width` đã lỗi thời → dùng `width="stretch"`. |
| Nhiều trang | `st.set_page_config` **chỉ được gọi 1 lần trong `app.py`**, các file trong `pages/` không được gọi. Điều hướng bằng `st.navigation` (nếu dùng cơ chế thư mục `pages/` mặc định thì nhãn sidebar sẽ mất dấu tiếng Việt). |
| Theme sáng/tối | Nhận biết bằng `st.context.theme.type`. Đã có sẵn `theme.risk_palette()` và `theme.plotly_template()`. Đừng đặt màu cứng chỉ hợp 1 theme. |
| Không đặt `[theme]` trong `config.toml` | Nếu đặt sẽ khoá app ở 1 theme, mất khả năng tự đổi theo máy người dùng. |
| Chữ tràn khỏi khung trong biểu đồ | Dùng `theme.wrap_text()` và hàm `_add_box()` trong `viz/supply_chain.py` (tự chia đều dòng theo chiều cao ô). |

---

## 7. Cách test cho đúng

**Smoke test Python** — gọi thẳng các hàm dựng biểu đồ với dữ liệu thật, kiểm tra cả trường
hợp rỗng (công ty chưa có dữ liệu) và bộ lọc chỉ chọn 1 giá trị.

**Test giao diện bằng Playwright** — điểm quan trọng nhất:

```js
// SAI: sleep cố định -> chụp lúc biểu đồ chưa vẽ xong, tưởng nhầm là lỗi trắng trang
await page.waitForTimeout(1500);

// ĐÚNG: chờ Plotly vẽ xong thật sự
await page.waitForFunction((n) => {
  const plots = document.querySelectorAll('.js-plotly-plot');
  return plots.length >= n &&
    [...plots].every(p => p.querySelectorAll('.main-svg path').length > 3);
}, expectedChartCount);
```

Bắt buộc: lắng nghe `pageerror` + `console` để phát hiện lỗi JS, và **tự xem lại ảnh chụp**
— nhiều lỗi trình bày chỉ nhìn ảnh mới thấy.

Lưu ý: mở thẳng URL trang con (deep-link) sẽ sinh vài lỗi 404 vô hại của Streamlit
(`_stcore/health`, `_stcore/host-config`). Nên **điều hướng bằng cách bấm menu** như người
dùng thật.

---

## 8. Việc chưa làm (đợt sau)

- Sheet `5_KRI_Library` — dashboard KRI theo ngưỡng xanh/vàng/đỏ.
- Sheet `6_Risk_Appetite_Threshold` — đối chiếu mức rủi ro thực tế với khẩu vị rủi ro.
- Sheet `7_RCM` — ma trận kiểm soát (cần xử lý header lồng nhau trước).
- Trang Overview chi tiết cấp tập đoàn.
- Chưa khởi tạo git (xem Bước 6).

---

## 9. Phát hiện nghiệp vụ đáng chú ý (giữ lại khi làm tiếp)

Các cảnh báo sau được sinh **tự động** trong `src/insights.py`, không phải viết cứng:

- `SUPPLIER-CU-01` (đồng) cung cấp cho **cả CADIVI lẫn EMIC**, cả hai đều đánh giá "khó thay
  thế" → rủi ro tập trung cấp tập đoàn. Chỉ nhìn thấy ở chế độ **Toàn hệ thống**.
- `RISK-01` có điểm **sau** kiểm soát cao hơn **trước** kiểm soát (6 → 9).
- Ba rủi ro cùng điểm residual = 6 nhưng gắn nhãn RAG khác nhau → ngưỡng RAG chưa thống nhất.
- EMIC: 2/6 liên kết phụ thuộc một nguồn duy nhất, 3/6 khó thay thế.
