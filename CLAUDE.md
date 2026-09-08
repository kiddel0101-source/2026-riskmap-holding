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

### Bước 6 — MỞ APP CHO NGƯỜI DÙNG (rồi mới tới git, theo đúng thứ tự)

#### 6a. Mở app và đưa link

- **Luôn tự khởi động app và đưa link** (ví dụ `http://localhost:8600`) — không bắt người
  dùng tự chạy lệnh.
- Nếu người dùng báo trùng port → tắt hẳn tiến trình cũ rồi chạy port khác.

#### 6b. Kiểm tra git và BÁO CÁO (chưa push)

- Chạy `git status`, báo rõ file nào đã đổi.
- ⚠️ **Bắt buộc kiểm tra `.env` không bị đưa vào** bằng lệnh
  `git ls-files --cached | grep -iE "^\.env"` — lệnh này phải **không ra kết quả nào**.
  File `.env` chứa client secret và mật khẩu tài khoản dịch vụ thật. Đã được `.gitignore`
  và `.dockerignore` chặn — đừng bao giờ gỡ hai dòng đó.

#### 6c. CHỜ NGƯỜI DÙNG XÁC NHẬN rồi mới commit + push

- 🚫 **KHÔNG được tự ý `git push`.** Người dùng phải xem app chạy thực tế, hài lòng rồi mới
  cho lệnh (ví dụ: *"ok push đi"*).
- Nếu người dùng thấy chưa ổn → quay lại Bước 4 sửa tiếp, chưa đụng tới git.
- Chỉ khi được đồng ý mới `git commit` + `git push`, rồi báo lại kết quả.
- Repo: <https://github.com/khanh-at-gex/app-risk-visual-riskmap-holding> (nhánh `main`).

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
  4_Su_kien_rui_ro.py       Nhập sự kiện, dò từ khóa, gắn với dữ liệu hiện có, lưu lịch sử
src/
  config.py                 Link SharePoint, vị trí dòng header từng sheet, màu RAG,
                            COLUMN_LABELS + hàm vi() đổi tên cột sang tiếng Việt
  theme.py                  Nhận biết theme sáng/tối, bảng màu, ngắt dòng chữ trong ô
  insights.py               Tự phát hiện điểm bất thường để cảnh báo trên giao diện
  insights_event.py         Dò từ khóa (không AI) cho trang Sự kiện rủi ro
  data/loader.py            Tải file từ SharePoint vào bộ nhớ (có cache)
  data/repository.py        Đọc từng sheet thành DataFrame, các phép nối dữ liệu
  data/event_store.py       Lưu/đọc lịch sử sự kiện rủi ro qua SQLAlchemy (xem Mục 11)
  components/filters.py     Bộ chọn công ty dùng chung giữa các trang
  components/risk_dialog.py Hộp thoại hồ sơ rủi ro đầy đủ khi bấm vào 1 ô trên bản đồ
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
| **Ô trống hiện ra chữ `nan` trên màn hình** | Dữ liệu có rất nhiều ô trống. Hai cái bẫy đã mắc: (1) `row.get(col, "—")` **không** trả về `"—"` khi ô có giá trị `NaN` (vì cột vẫn tồn tại) → in ra `nan`; (2) `if row.get(col):` **luôn đúng** với `NaN` vì `float('nan')` là truthy → hiện "Phụ thuộc: nan". → Luôn dùng `theme.nz(value)` để hiển thị, và `pd.notna(...)` để kiểm tra có giá trị hay không. |
| Bộ lọc phải áp dụng nhất quán | Nếu lọc dữ liệu cho biểu đồ thì **chỉ số KPI, cảnh báo và bảng chi tiết cũng phải lọc theo**, nếu không con số sẽ không khớp với hình người dùng đang nhìn. |
| `single_source_flag` có 2 nghĩa | Vừa là "phụ thuộc 1 nhà cung cấp" (liên kết đầu vào) vừa là "tập trung 1 khách hàng" (liên kết đầu ra). Đừng gộp chung một nhãn — phải tách theo chiều `upstream/downstream` như trong `insights.supply_chain_alerts()`. |

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
- Chưa chạy thử Dockerfile trên môi trường deploy thật (xem Mục 10).

---

## 9. Phát hiện nghiệp vụ đáng chú ý (giữ lại khi làm tiếp)

Các cảnh báo sau được sinh **tự động** trong `src/insights.py`, không phải viết cứng:

- `SUPPLIER-CU-01` (đồng) cung cấp cho **cả CADIVI lẫn EMIC**, cả hai đều đánh giá "khó thay
  thế" → rủi ro tập trung cấp tập đoàn. Chỉ nhìn thấy ở chế độ **Toàn hệ thống**.
- `RISK-01` có điểm **sau** kiểm soát cao hơn **trước** kiểm soát (6 → 9).
- Ba rủi ro cùng điểm residual = 6 nhưng gắn nhãn RAG khác nhau → ngưỡng RAG chưa thống nhất.
- EMIC: 2/6 liên kết phụ thuộc một nguồn duy nhất, 3/6 khó thay thế.

---

## 10. Triển khai (Docker)

`Dockerfile` build từ image nội bộ `gex-base-streamlit:latest`, cài thêm `git` (cần để pip
lấy `gex-msgraph` từ GitHub) rồi chạy Streamlit ở cổng 8501.

⚠️ **Hai điểm phải nhớ khi deploy:**

1. Dockerfile dùng `COPY . .` → mọi file không nằm trong `.dockerignore` sẽ bị đóng gói vào
   image. `.env` đã được chặn — **không được gỡ**. Thay vào đó, truyền biến môi trường
   (`MS_DAS_U1_CLIENT_ID`, `MS_DAS_U1_CLIENT_SECRET`, `MS_DAS_U1_TENANT_ID`,
   `MS_DAS_U1_USERNAME`, `MS_DAS_U1_PASSWORD`) lúc chạy container.
2. Máy build phải vào được GitHub nội bộ để cài `gex-msgraph`; container lúc chạy phải vào
   được SharePoint, nếu không app sẽ báo lỗi không tải được dữ liệu (app **không** có bản
   sao dự phòng dưới đĩa theo đúng yêu cầu).

---

## 11. Trang "Sự kiện rủi ro" — lưu trữ tạm thời, cần IT xác nhận

Trang `4_Su_kien_rui_ro.py` là chỗ DUY NHẤT trong app có **ghi dữ liệu xuống đĩa/DB**
(`src/data/event_store.py`) — khác với mọi trang còn lại vốn chỉ đọc Excel từ SharePoint.
Nguyên tắc "không lưu file" ở Mục 6 nói về *bản sao workbook nguồn*, không áp dụng ở đây vì
lịch sử sự kiện là dữ liệu do chính app tạo ra, không phải cache của nguồn.

- **Hiện trạng:** chưa xác nhận công ty có Postgres dùng chung cho app nội bộ hay không (image
  `gex-base-streamlit` đã có sẵn `sqlalchemy` + `psycopg2` — dấu hiệu có thể đã có). Vì vậy tạm
  dùng SQLite cục bộ (`risk_events.db`, đã chặn trong `.gitignore`) làm mặc định.
- ⚠️ **Rủi ro:** nếu server chạy Docker không gắn volume lưu trữ riêng cho `risk_events.db`,
  lịch sử sẽ **mất mỗi lần deploy lại container**. Trang có hiện cảnh báo này ngay trên giao
  diện (`event_store.is_using_default_storage()`).
- **Cách nâng cấp lên Postgres sau này:** chỉ cần đặt biến môi trường `RISK_EVENTS_DB_URL`
  (dạng `postgresql+psycopg2://user:pass@host/db`) lúc chạy container — không cần sửa code,
  `src/data/event_store.py` đọc thẳng từ biến này.
- Cơ chế dò từ khóa (`src/insights_event.py`) là **rule-based, không dùng AI** (đã chốt với
  người dùng) — dò 2 tầng: khớp chính xác (giữ dấu) trước, chỉ khi 1 từ khóa không ra kết quả
  chính xác nào mới thử lại kiểu bỏ dấu (gắn `is_exact=False`, hiện cảnh báo trên giao diện).
  ⚠️ **Đừng bỏ hết dấu tiếng Việt rồi so khớp trực tiếp** — từng gây lỗi thật: "đồng" (kim loại)
  và "động" (hoạt động/biến động) đều rút gọn về "dong" nên khớp lẫn lộn hàng loạt, xem lịch sử
  sửa lỗi trong code. Giới hạn đã biết: từ khóa vĩ mô không có mặt sẵn trong dữ liệu (vd "giá
  dầu" với công ty không liên quan dầu khí) sẽ ra "không tìm thấy" — đây là đánh đổi đã được
  người dùng chấp nhận để giữ minh bạch, không phải lỗi.

### 11.1. Tích chọn & xác nhận đưa vào "Danh mục rủi ro"

Trên trang Sự kiện rủi ro, mỗi rủi ro/hoạt động khớp có thêm ô tích để **xác nhận liên quan đến
sự kiện** — dữ liệu này **chỉ ghi trong DB riêng của app** (2 bảng mới trong
`src/data/event_store.py`), **không** ghi/upload gì vào file Excel Risk Register thật:

- `event_risk_confirmations` — chỉ đánh dấu 1 `risk_id` **đã có** trong Risk Register là liên
  quan đến 1 sự kiện; không copy dữ liệu, luôn join sống với `risks` df khi hiển thị.
- `event_draft_risks` — rủi ro **NHÁP** tạo từ 1 hoạt động Chuỗi giá trị chưa từng có rủi ro
  (form nhỏ: mô tả + loại rủi ro). Hiện trên trang Danh mục rủi ro với nhãn **NHÁP** màu cam, có
  ghi chú rõ đây chưa phải rủi ro chính thức, cán bộ phải tự thêm vào Excel nếu xác nhận là thật.
- MVP chưa có chức năng "bỏ xác nhận"/xoá — tích nhầm thì tạm thời chưa tự sửa được trên UI.

### 11.2. "Rủi ro có thể kích hoạt" — ĐÃ CHUYỂN sang `Risk_Linkages` + `Sheet1` (Phần 3) — [⚠️ ĐÃ XOÁ HẲN, xem Mục 11.5]

⚠️ **TOÀN BỘ tính năng mô tả trong mục này (11.2) đã bị GỠ BỎ hoàn toàn** — sheet `Risk_Linkages`
đã bị xoá khỏi workbook nguồn, không có sheet thay thế, người dùng đã xác nhận gỡ tính năng thay
vì giữ code chết (xem Mục 11.5). Giữ lại nội dung dưới đây CHỈ để tham khảo lịch sử/thiết kế cũ,
KHÔNG còn đúng với code hiện tại — đừng dựa vào mục này để sửa code.

⚠️ **Lịch sử:** bản đầu (Phần 2) dùng `0. Danh mục rủi ro` + `8_Risk_node` (nối theo TÊN NHÓM rủi
ro chung chung). Sau đó workbook được bổ sung 3 sheet mới (`Sheet1`, `Risk_Linkages`,
`Mapping_RiskCategory_VC`) và `0. Danh mục rủi ro` được thêm cột `VC2_ID` — người dùng đã chốt
chuyển hẳn sang cơ chế chính xác hơn này, không dùng `8_Risk_node` nữa (dù sheet đó vẫn còn trong
workbook, code không đọc nữa).

Đã xác minh trực tiếp trên workbook thật (không suy đoán):

- **`0. Danh mục rủi ro`** (145 dòng) nay có thêm cột **`VC2_ID`** nối thẳng `risk_id` (RR.xxxx,
  dùng chung không gian mã với `4_Risk_Register`) sang 1 hoạt động trong `Sheet1` — phủ 143/145
  dòng, đủ cho toàn bộ 12 rủi ro CADIVI/EMIC. ⚠️ Sheet có 2 cột trùng tên `VC2_ID`; pandas tự đổi
  tên cột thứ 2 thành `VC2_ID.1` — **chỉ dùng cột đầu** (chính), bỏ qua `.1`.
- **`Risk_Linkages`** — quan hệ **rủi ro → rủi ro trực tiếp** (không phải nhóm chung chung):
  `Source_Risk_ID/Name`, `Target_Risk_ID/Name` (mã dạng `RSK-xxx`, không gian mã RIÊNG của
  `Sheet1`, không phải `RR.xxxx`), `Mô tả cơ chế liên kết`, `Mức độ ảnh hưởng`. ⚠️ **Hiện chỉ có 1
  dòng dữ liệu thật** (LNK-001: RSK-018 → RSK-002) — độ phủ sẽ rất thưa cho tới khi được bổ sung
  thêm, người dùng đã chấp nhận dùng ngay dù thưa.
- **`Mapping_RiskCategory_VC`** (85 dòng, nối `risk_category_l2` ↔ `VC2_ID`) — **không còn cần
  dùng** vì `0. Danh mục rủi ro` đã có `VC2_ID` trực tiếp, đường nối ngắn hơn. Sheet vẫn còn trong
  workbook, giữ lại phòng khi cần fallback cho ~2 dòng thiếu `VC2_ID`.
- Cách nối: `risk_id` → `VC2_ID` (từ `0. Danh mục rủi ro`) → các `risk_id` dạng `RSK-xxx` gắn với
  `VC2_ID` đó trong `Sheet1` (1 hoạt động có thể có nhiều rủi ro, tối đa 3) → lọc `Risk_Linkages`
  theo `Source_Risk_ID` → trả **tên rủi ro đích + mức ảnh hưởng + mô tả cơ chế** (chi tiết hơn hẳn
  bản cũ). Không tra được, hoặc không có quan hệ nào → im lặng bỏ qua, không hiện khung rỗng.
- Hàm dùng: `repository.get_risk_taxonomy()` (nay trả thêm `vc2_id`), `get_value_chain_v2()`,
  `get_risk_trigger_edges()` (đọc `Risk_Linkages`), `risks_triggered_by(risk_id, taxonomy, vc2_df,
  edges)` (theo risk_id có sẵn), `risks_triggered_by_vc2(vc2_id, vc2_df, edges)` (theo 1 hoạt động
  người dùng tự chọn — dùng cho rủi ro nháp).

### 11.3. Trang Chuỗi giá trị — nguồn dữ liệu THAY THẾ bằng `Sheet1` (Phần 3)

⚠️ **[CẬP NHẬT — xem Mục 11.5]** App TỪNG có 2 mô hình Chuỗi giá trị song song (đoạn dưới đây mô
tả trạng thái CŨ, giữ lại để tham khảo lịch sử). Sheet `2_Value_Chain_Master` (mô hình cũ theo
công ty) đã bị **xoá khỏi workbook nguồn**, không có sheet thay thế — `repository.get_value_chain()`
và mọi tính năng phụ thuộc nó ở Trang chủ/Sự kiện rủi ro đã bị GỠ BỎ. `2_VC_Master` (dưới đây vẫn
gọi bằng tên cũ "Sheet1" ở một số đoạn — đã đổi tên, xem Mục 11.3 phần đầu) giờ là nguồn Chuỗi giá
trị **DUY NHẤT** trong toàn app.

- ~~`2_Value_Chain_Master`~~ (qua `repository.get_value_chain()` + `viz.value_chain.build_value_chain_map()`)
  — mô hình CŨ, có cột `company_id` (theo từng công ty CADIVI/EMIC), 7 khối, `vc_node_id` kiểu
  "MS-001". **ĐÃ XOÁ** (sheet nguồn không còn tồn tại) — không còn dùng ở đâu nữa.
- `2_VC_Master` (qua `repository.get_value_chain_v2()`) — mô hình DUY NHẤT hiện tại, **không có
  cột công ty** (dùng chung toàn Tập đoàn), đủ **9 khối Porter** (thêm Cơ sở hạ tầng doanh nghiệp
  + Quản trị nguồn nhân lực), có rủi ro gắn TRỰC TIẾP theo hoạt động (`risk_id` dạng `RSK-xxx`,
  không phải `RR.xxxx`). Chỉ dùng ở **trang Chuỗi giá trị** (`pages/2_Chuoi_gia_tri.py`).
- ⚠️ Sheet1 vừa bị đổi tên 2 cột gốc trên SharePoint (`Chuỗi giá trị 1`→`Value Chain`, `Chuỗi giá
  trị 2`→`Sub-Value Chain`) — `get_value_chain_v2()` nhận cả tên cũ/mới để không vỡ lại nếu người
  phụ trách dữ liệu đổi tên tiếp.
- ⚠️ **Lần đổi cấu trúc mới nhất (đã gặp thật, đã sửa):** Sheet1 được thêm 1 cấp phân cấp trung
  gian mới **`Value Chain L2`** (còn thưa, phần lớn rỗng — CHƯA dùng trong app), đồng thời đổi
  hẳn 2 cột đang dùng cho hoạt động: cột **`VC2_ID`** cũ nay **RỖNG HOÀN TOÀN** (còn tồn tại như
  vết tích, không bị xoá khỏi sheet) — dữ liệu mã hoạt động thật (kiểu `"IL-001"`) chuyển sang
  cột mới **`VC3_ID`**; tên hiển thị hoạt động chuyển từ `"Sub-Value Chain"` sang **`"Value Chain
  L3"`**. Khác các lần đổi tên trước (chỉ 1 trong 2 tên tồn tại tại 1 thời điểm), lần này **CẢ 2
  cột cũ/mới cùng tồn tại đồng thời** trong sheet — dict `rename()` đơn giản KHÔNG dùng được nữa
  (2 cột sẽ cùng đổi thành `vc2_id`, pandas không gộp giá trị, sinh cột trùng tên). Đã sửa bằng
  hàm mới `repository._first_non_empty_column(df, candidates)` — duyệt qua danh sách tên cột ứng
  viên theo thứ tự ưu tiên (mới trước, cũ sau), chọn cột ĐẦU TIÊN có ít nhất 1 giá trị khác rỗng,
  không chỉ dựa vào "cột có tồn tại trong sheet". Rút kinh nghiệm: khi sheet đổi cấu trúc, đừng
  giả định tên cột cũ đã biến mất — có thể vẫn còn nhưng rỗng, phải kiểm tra dữ liệu thật trước
  khi tin vào tên cột.
- `vc2_id` (kiểu "MS-005" trong Sheet1) và `vc_node_id` (kiểu "MS-001" trong `2_Value_Chain_Master`)
  **KHÔNG cùng không gian mã** dù format giống nhau — đã kiểm tra thực tế 2 mã khác nội dung nhau.
  Đừng bao giờ so sánh trực tiếp giữa 2 hệ này.
- **Trang hiện hiển thị 2 CẤP** (đã chốt với người dùng): `viz.value_chain.build_value_chain_blocks()`
  vẽ **cấp 1** — mỗi khối chức năng là 1 box TRUNG TÍNH (không tô màu rủi ro), 2 hàng theo khung
  Porter (5 khối Chính/4 khối Hỗ trợ). Bấm 1
  khối → **mở rộng ngay trên trang** (không dùng hộp thoại) danh sách hoạt động (sub-value chain,
  cấp 2) trong khối đó, mỗi hoạt động có chip màu số rủi ro. Bấm nút "Xem rủi ro" trên 1 hoạt động
  mới mở hộp thoại `risk_dialog.show_activity_risks()` (cấp 3, rút gọn — vì `Sheet1` không có điểm
  số/RAG/chủ trì/kiểm soát như Risk Register, chỉ có `Risk_ID`, tên rủi ro, `Problem`, `Details`).
  Hàm `build_value_chain_map_v2()` (bản vẽ hết 66 hoạt động trong 1 lần, không thu gọn theo khối)
  đã bị THAY THẾ hoàn toàn, không còn trong code.
- ⚠️ **Lần đổi tên thứ 3 trên SharePoint (đã gặp thật, đã sửa):** giá trị hiển thị của `vc1_name`
  bị đổi ("Vận hành / Sản xuất"→"Sản xuất", "Marketing & Bán hàng"→"Bán hàng", "Thu mua"→"Mua
  hàng"), khiến logic phân loại Chính/Hỗ trợ cũ (so khớp theo TÊN, hằng `_PRIMARY_FUNCTIONS_V2`/
  `_SUPPORT_FUNCTIONS_V2`) không nhận ra "Sản xuất"/"Bán hàng" là hoạt động Chính nữa → 2 khối này
  bị xếp nhầm xuống hàng Hỗ trợ trên giao diện. Đã sửa tận gốc: phân loại + sắp xếp nay dựa vào
  **`vc1_id`** (mã ổn định IL/OP/OL/MS/SV/PR/TD/FI/HR — cũng là tiền tố của `vc2_id` như "OP-001",
  đã qua 3 lần đổi tên vẫn không đổi) thay vì `vc1_name` — hằng số đổi tên thành `_ID_ORDER_V2`/
  `_PRIMARY_IDS_V2`/`_SUPPORT_IDS_V2`, tên hiển thị chỉ tra cứu qua `id_to_name` lúc vẽ. Rút kinh
  nghiệm chung: **bất cứ đâu cần so khớp/phân loại theo dữ liệu Sheet1, luôn ưu tiên khớp theo mã
  ID ổn định, không khớp theo tên hiển thị** — tên hiển thị trên sheet này đã đổi nhiều lần và sẽ
  còn đổi tiếp.

### 11.4. Rủi ro từ `CADIVI_RCM` (tên cũ `7_RCM`) — nguồn rủi ro THỨ 3, cộng dồn vào trang Chuỗi giá trị

⚠️ Sheet đã đổi tên từ `7_RCM` sang `CADIVI_RCM` (tách theo từng công ty trên SharePoint — hiện
CHỈ có `CADIVI_RCM`, người dùng đã xác nhận chưa có công ty nào khác; nếu công ty khác được bổ
sung sau này, sheet mới sẽ có dạng `"{Tên công ty}_RCM"`, nhưng code hiện đọc CỨNG `"CADIVI_RCM"`
— cần cập nhật nếu có sheet thứ 2). `SHEET_HEADER_ROW["CADIVI_RCM"]` (`src/config.py`).

Sheet Ma trận kiểm soát rủi ro này là nguồn rủi ro **tách biệt hoàn toàn** với `RSK-xxx`
(`2_VC_Master`) và `RR.xxxx` (Risk Register) — cột `"Risk"` ở đây là **mô tả rủi ro theo danh
mục** (vd *"4.3.1. Sự phụ thuộc vào nhóm nhà cung cấp"*, mã `Risk_category_ID` = `"RC-4.3"`),
không phải 1 mã định danh. Gắn theo công ty (`company_id`).

⚠️ **Lần đổi cấu trúc gần nhất (đã gặp thật, đã sửa):** cột `VC2_ID` của `CADIVI_RCM` giờ chứa mã
CẤP NHÓM NHỎ (vd `"FI-02"`, khớp `2_VC_Master.VC2_ID`/`"Value Chain L2"`, đã xác minh 10/10 mã
khớp), KHÔNG còn khớp với mã hoạt động cụ thể (VC3, vd `"FI-021"`) mà app dùng làm `vc2_id` nữa
(0/10 khớp) — khác hẳn thời điểm sheet còn tên `7_RCM`, khi đó `VC2_ID` khớp thẳng cấp hoạt động
(16/16). Người dùng đã xác nhận **CHƯA cần** gán rủi ro CADIVI_RCM xuống từng hoạt động cụ thể —
chỉ dùng được ở cấp khối (`vc1_id`, xem `rcm_block_health_color()`) và cấp nhóm nhỏ (`vc2_id` của
chính CADIVI_RCM, chưa hiển thị lên UI). Nếu sau này cần gán xuống VC3, phải đi qua
`2_VC_Master`: `vc1_id` → tất cả `vc2_id` (nhóm nhỏ) → tất cả `vc3_id` (hoạt động con) — 1 nhóm
nhỏ có thể có 3-6 hoạt động con, cần hỏi lại người dùng cách hiển thị (rủi ro lặp lại trên mọi
hoạt động con, hay 1 khu vực riêng theo nhóm).

⚠️ **Sheet này đang được người phụ trách chỉnh sửa TRỰC TIẾP trong lúc làm tính năng** — đã bắt gặp
thật 2 lần trong cùng 1 buổi: (1) số dòng dữ liệu giảm từ 20 (CADIVI+EMIC) xuống còn 12 (chỉ
CADIVI, các dòng EMIC bị xoá/di chuyển đi đâu đó), khiến `n_rcm_risks` tụt từ 18 xuống 12 giữa 2
lần mở app; (2) cột đánh giá kiểm soát đổi cấu trúc — bản đầu gộp chung "Đánh giá hiệu lực, hiệu
quả của kiểm soát" thành 1 cột, bản sau **tách thành 2 cột riêng** "Đánh giá hiệu lực của kiểm
soát" + "Đánh giá hiệu quả của kiểm soát" (làm số cột từ 24 tăng lên 26). Rút kinh nghiệm: đừng
coi số liệu/cấu trúc cột của sheet này là cố định, luôn đối chiếu lại trực tiếp khi số liệu trông
bất thường.

- `repository.get_rcm_risks()` đọc **theo VỊ TRÍ cột Excel** (I-N, O-P, R-W, X-Y — xem docstring
  hàm) chứ không theo tên, vì tên cột kiểm soát TRÙNG NHAU giữa khối Entity Level và Transaction
  Level (và có sai khác chính tả nhỏ giữa 2 bản, vd "hiệu lựccủa" thiếu dấu cách ở Entity nhưng
  "hiệu lực của" đúng dấu cách ở Transaction) — không thể dựa vào tên cột để phân biệt ổn định.
  ⚠️ Nếu người phụ trách dữ liệu chèn/xoá/đổi thứ tự cột trên SharePoint, mapping vị trí này sẽ đọc
  SAI mà không báo lỗi — phải đối chiếu lại thủ công với sheet thật khi thấy số liệu bất thường.
- Sheet có dòng lặp y hệt (1 rủi ro có cả kiểm soát Entity lẫn Transaction sẽ chiếm 2 dòng thô) —
  `get_rcm_risks()` tự `drop_duplicates` trên `(company_id, vc2_id, risk_desc, risk_category_id)`.
- **Trang Chuỗi giá trị cộng dồn** số đếm rủi ro của mỗi hoạt động = rủi ro Sheet1 + rủi ro 7_RCM
  (đã chốt với người dùng), nhưng **luôn ghi rõ tách nguồn** ở mọi nơi hiển thị số liệu (KPI đầu
  trang, card "Chi tiết hoạt động") — không bao giờ gộp thành 1 số duy nhất mà không chú thích, vì
  2 hệ risk_id khác nhau hoàn toàn, gộp im lặng sẽ gây hiểu lầm khi so sánh với dữ liệu gốc.
- Hộp thoại `risk_dialog.show_activity_risks()` nhận thêm tham số `rcm_risks` (tùy chọn) — hiện 1
  mục RIÊNG "🗂️ Từ Ma trận kiểm soát rủi ro (7_RCM)" bên dưới mục "📋 Từ Sheet1" (mục Sheet1 hiện
  LUÔN khi có `rcm_risks`, kể cả khi rỗng — ghi rõ "Chưa có rủi ro nào trong Sheet1..." — để người
  dùng không hiểu lầm 2 nguồn là một). Mỗi rủi ro 7_RCM gắn nhãn công ty + mã danh mục ngay trên
  tiêu đề, không trộn với rủi ro Sheet1.
- **Hiệu lực/hiệu quả kiểm soát:** mỗi rủi ro 7_RCM có 2 nút bấm-mở-rộng (`st.expander`) "Entity
  Level" / "Transaction Level", tiền tố bằng 1 emoji màu (`_EFF_EMOJI` trong `risk_dialog.py`) theo
  `_rcm_effectiveness_key(valid, effective)`: Có hiệu lực + Có hiệu quả → 🟢; Có hiệu lực + Không
  hiệu quả → 🟠; Không hiệu lực + Không hiệu quả → 🔴; tổ hợp khác (vd Không hiệu lực nhưng Có hiệu
  quả) hoặc thiếu dữ liệu → ⚪ (xám, KHÔNG đoán, đã chốt với người dùng). Bấm vào mới hiện chi tiết
  6 trường tương ứng (Entity: mô tả kiểm soát/đầu mối/cấp phê duyệt/độ bao phủ/mức định lượng/tần
  suất cập nhật — cột I-N; Transaction: mô tả kiểm soát/người soát xét/người phê duyệt/tần suất
  thực hiện/hình thức/nền tảng — cột R-W), không hiện sẵn để hộp thoại không quá dài.
- ⚠️ **Đã XOÁ `rcm_control_health_color()`** (bản màu ô mã hoạt động ở cấp vc2_id) — sheet
  `7_RCM` đổi tên thành `CADIVI_RCM` và đồng thời đổi Ý NGHĨA cột `vc2_id` sang cấp NHÓM NHỎ
  (không còn khớp với `vc2_id` cấp hoạt động cụ thể app đang dùng, xem Mục 11.4 bên dưới) - hàm
  cũ luôn trả `None` nên đã bỏ hẳn, chỉ còn `rcm_block_health_color()` ở cấp khối.
- Thêm khoá `"yellow"` vào `risk_palette()` (`src/theme.py`) — **tách riêng** với `"low"` (cam)
  vì phục vụ thang 4 mức (xanh/vàng/cam/đỏ) của ngưỡng trên, khác ý nghĩa với RAG 3 mức thông
  thường (none/low/high) đang dùng ở những chỗ khác trong app.
- **Màu KHỐI chức năng** (9 box "HẬU CẦN ĐẦU VÀO", "BÁN HÀNG"...) trên biểu đồ cấp 1: `risk_dialog.
  rcm_block_health_color(vc1_id, rcm_risks)` — CÙNG quy tắc/ngưỡng như màu ô mã hoạt động ở trên,
  chỉ khác PHẠM VI đếm: tổng số đánh giá "đỏ" trên **TẤT CẢ hoạt động trong khối** đó (không phải
  từng hoạt động riêng lẻ) — đã chốt với người dùng mở rộng quy tắc cấp hoạt động lên cấp khối.
  `pages/2_Chuoi_gia_tri.py` tính `block_colors: dict[vc1_id, hex]` rồi truyền vào
  `viz.value_chain.build_value_chain_blocks(vc2, block_colors=...)` — khối không có trong dict
  (chưa có hoạt động nào trong khối có dữ liệu 7_RCM) giữ màu trung tính như thiết kế gốc (xem Mục
  11.3 — quyết định "khối trung tính" ban đầu nay chỉ áp dụng khi thật sự KHÔNG có dữ liệu, không
  còn tuyệt đối cho mọi trường hợp).

### 11.5. XOÁ tính năng phụ thuộc `2_Value_Chain_Master` + `Risk_Linkages` — 2 sheet đã bị xoá khỏi workbook nguồn

⚠️ **Đã gặp thật, mức độ nghiêm trọng cao nhất từ trước tới nay:** workbook nguồn bị chỉnh sửa
trực tiếp, XOÁ HẲN 2 sheet app đang đọc, không có sheet thay thế — khác các lần trước (đổi tên/
đổi cấu trúc cột), lần này là **xoá toàn bộ nguồn dữ liệu**. Đã hỏi lại người dùng, được xác nhận:
*"Nếu ko tìm thấy thông tin nào hãy loại ra khỏi hệ thống"* — tức gỡ bỏ HẲN các tính năng phụ
thuộc, không để lại code chết/nhánh luôn rỗng.

- **`2_Value_Chain_Master`** — mô hình Chuỗi giá trị CŨ theo công ty (7 khối, mã `vc_node_id`
  kiểu `"PR-001"`). Trước đây dùng ở **Trang chủ** (KPI "Công ty có dữ liệu") và **Sự kiện rủi
  ro** (nguồn tìm kiếm "Hoạt động trong Chuỗi giá trị" + form tạo rủi ro nháp từ 1 hoạt động).
- **`Risk_Linkages`** — quan hệ "rủi ro này có thể kích hoạt rủi ro khác". Trước đây dùng ở
  **Chuỗi giá trị** (dòng "🔗 Có thể kích hoạt" trong hộp thoại rủi ro), **Danh mục rủi ro** (cột
  "Có thể kích hoạt" ở 2 bảng xác nhận/nháp), **Sự kiện rủi ro** (dòng "có thể kích hoạt" dưới mỗi
  rủi ro khớp + preview trong form tạo rủi ro nháp).
- `4_Risk_Register.vc_node_id` (mã kiểu `"PR-001"`) giờ **không còn nối được đi đâu** vì sheet
  đích đã mất — cột này coi như dữ liệu vết tích, không dùng được cho tính năng nào nữa.

**Đã xoá hoàn toàn** (không phải comment-out): `repository.get_value_chain()`,
`get_risk_trigger_edges()`, `risks_triggered_by()`, `risks_triggered_by_vc2()`,
`risks_exploded_by_vc_node()`, `risk_counts_by_node()`, `risks_for_node()` (2 hàm cuối đã chết từ
trước, không ai gọi); `insights.value_chain_hotspots()`; `viz.value_chain.build_value_chain_map()`
+ `_FUNCTION_ORDER`/`_sort_functions` + `build_risk_by_function_bar()` (bản cũ — 3 hàm/hằng này đã
chết từ trước khi bị xoá, không có trang nào gọi tới, có lẽ sót lại từ khi Trang chủ được đơn giản
hoá ở 1 thời điểm nào đó trước dự án này); `insights_event._VC_FIELDS`/`_label_value_chain`/
`scan_value_chain()` + nhánh `"value_chain"` trong `_scan_source()`/`scan_all()`;
`risk_dialog.show_activity_risks()`'s tham số `edges`; `pages/4_Su_kien_rui_ro.py`'s
`_render_vc_group()` + toàn bộ luồng "chọn hoạt động Chuỗi giá trị để tạo rủi ro nháp" + dòng "có
thể kích hoạt" dưới mỗi rủi ro Risk Register khớp; cột "Có thể kích hoạt" ở 2 bảng trên
`pages/3_Danh_muc_rui_ro.py`; `SHEET_HEADER_ROW` entries cho `"2_Value_Chain_Master"`,
`"Risk_Linkages"`, và `"6_Risk_Appetite_Threshold"`/`"0. Danh mục rủi ro"`/`"8_Risk_node"` (3 sheet
cuối không tồn tại nữa VÀ không còn code nào đọc tới sau khi `get_risk_taxonomy()` cũng bị xoá —
hàm đó chỉ tồn tại để phục vụ `risks_triggered_by`).

**KHÔNG xoá:** `src/data/event_store.py` (lớp lưu trữ SQLite riêng của app) — bảng
`event_draft_risks` vẫn giữ nguyên schema (cột `vc_node_id`, `trigger_category`) và
`list_draft_risks()` vẫn hiển thị dữ liệu LỊCH SỬ trên trang Danh mục rủi ro (nhãn "NHÁP"), chỉ
riêng đường TẠO MỚI draft từ 1 hoạt động Chuỗi giá trị (ở trang Sự kiện rủi ro) bị gỡ vì không còn
nguồn "Hoạt động trong Chuỗi giá trị" để chọn từ đó nữa.

**Rút kinh nghiệm:** khi 1 sheet nguồn bị XOÁ HẲN (không phải đổi tên/cấu trúc) và không có sheet
thay thế rõ ràng, đừng để code âm thầm crash (`ValueError: Worksheet ... not found`) hay để lại
nhánh tính năng luôn-luôn-rỗng — hỏi thẳng người dùng có xác nhận xoá tính năng đó không, rồi dọn
sạch (kể cả code đã chết từ trước bị lộ ra trong lúc dọn, như `build_value_chain_map` ở trên).

### 11.6. Thêm cấp VC2 (nhóm nhỏ) vào trang Chuỗi giá trị — luồng bấm nay có 3 cấp

`2_VC_Master` có 3 cấp phân cấp thật (xem Mục 11.3): **VC1** (khối, vd "FI") → **VC2** "Value
Chain L2" (nhóm nhỏ, vd "FI-02", 1-20 nhóm/khối tuỳ khối) → **VC3** "Value Chain L3" (hoạt động
cụ thể, vd "FI-021", 187 hoạt động toàn bộ). Trước đây trang chỉ hiển thị 2 cấp (VC1 → nhảy thẳng
xuống danh sách VC3) — đã chốt với người dùng thêm cấp VC2 làm tầng trung gian, vì đây đúng là
cấp mà dữ liệu `CADIVI_RCM` khớp thật (xem Mục 11.4), giúp màu kiểm soát chính xác hơn hẳn so với
chỉ tô ở cấp khối.

- `repository.get_value_chain_v2()` trả thêm 2 cột `group_id`/`group_name` (đọc thẳng từ
  `VC2_ID`/`"Value Chain L2"` của `2_VC_Master`) — đặt tên KHÁC hẳn `vc2_id`/`vc2_name` (đã dùng
  sẵn cho cấp VC3) để tránh nhầm 2 khái niệm.
- `risk_dialog.rcm_group_health_color(group_id, rcm_risks)` — giống hệt quy tắc ngưỡng của
  `rcm_block_health_color()` (đếm "đỏ", ngưỡng 7/5/3) nhưng lọc theo `rcm_risks["vc2_id"] ==
  group_id` (khớp ĐÚNG cấp, đã xác minh 10/10 mã khớp — khác `rcm_block_health_color` phải gộp
  qua `vc1_id`).
- **Luồng bấm mới trên `pages/2_Chuoi_gia_tri.py`:** bấm 1 khối VC1 (biểu đồ Plotly, không đổi)
  → hiện **lưới ô VC2** (Streamlit native — khung bo viền + nút "Chọn nhóm", 4 cột/hàng, tự xuống
  dòng, KHÔNG dùng Plotly vì số lượng ô dao động quá lớn 1-20 giữa các khối, không hợp biểu đồ cố
  định 5+4 cột như VC1) — mỗi ô tô màu theo `rcm_group_health_color()`, ô trung tính nếu nhóm
  chưa có dữ liệu CADIVI_RCM → bấm 1 ô VC2 → mới hiện danh sách hoạt động VC3 (UI cũ, không đổi)
  ngay bên dưới lưới ô (không thay thế, ĐÍNH KÈM thêm — khớp mockup đã duyệt). Trạng thái lưu ở
  `st.session_state["_vc2_selected_group"]`, được reset về `None` mỗi khi người dùng bấm sang 1
  khối VC1 khác hoặc bấm "✕ Đóng" — tránh việc chọn nhóm cũ "dính" sang ngữ cảnh khối mới. (⚠️ Cơ
  chế bấm khối VC1 đã đổi hẳn ở Mục 11.7 — không còn dùng `clicked_block`/Plotly `on_select`.)
- ⚠️ **Phát hiện trong lúc test (KHÔNG phải lỗi do tính năng này gây ra, đã báo cho người dùng):**
  bộ lọc "Nhóm hoạt động" (Chính/Hỗ trợ, `nodes["category"].isin(categories)`) đã tồn tại từ
  trước — nhưng với 1 số khối (vd "Cơ sở hạ tầng doanh nghiệp"), rất nhiều hoạt động VC3 có cột
  "Phân loại" (category) RỖNG (`NaN`) trong dữ liệu nguồn (33/67 dòng ở khối này) — vì
  `NaN.isin({"Chính","Hỗ trợ"})` luôn là `False`, các dòng đó bị bộ lọc ẩn đi dù người dùng chưa
  đổi gì (mặc định chọn cả 2 giá trị). Ở cấp VC3 (danh sách phẳng) hậu quả không rõ ràng lắm
  (chỉ thiếu vài dòng trong 1 danh sách dài); nhưng ở cấp VC2 mới này, hậu quả RÕ hơn nhiều — nếu
  TẤT CẢ hoạt động con của 1 nhóm đều rỗng category, cả Ô NHÓM ĐÓ biến mất hoàn toàn khỏi lưới
  (đã gặp thật: 9/20 nhóm của "Cơ sở hạ tầng doanh nghiệp" biến mất vì lý do này). Đây là hành vi
  lọc CÓ TỪ TRƯỚC (không phải lỗi mới), chưa tự ý sửa vì đó là thiết kế đã duyệt trước đây — nếu
  người dùng muốn đổi (vd hoạt động chưa phân loại luôn hiện bất kể bộ lọc), cần hỏi lại và có
  thể cần mockup riêng.

### 11.7. Khối VC1 chuyển từ biểu đồ Plotly sang lưới Streamlit — mở rộng ngay dưới hàng đã bấm

Người dùng muốn khi bấm 1 khối VC1, nội dung mở rộng (lưới VC2 + danh sách VC3) hiện **ngay sau
hàng chứa khối đó** (hàng Chính hoặc hàng Hỗ trợ), không phải ở cuối trang như thiết kế cũ (Mục
11.3/11.6) — đã xác nhận: **full chiều rộng trang**, không ép nội dung vừa đúng 1 ô. Plotly KHÔNG
làm được kiểu "mở rộng tại chỗ" này (biểu đồ là 1 hình duy nhất) — nên 9 khối VC1 đã chuyển hẳn từ
`viz.value_chain.build_value_chain_blocks()` (Plotly, ĐÃ XOÁ hoàn toàn khỏi codebase) sang lưới
Streamlit-native (giống hệt cách dựng lưới VC2 ở Mục 11.6: `st.container(border=True)` + nút bấm
trong mỗi cột của `st.columns()`).

- `repository.vc1_bands(vc1_ids) -> list[tuple[str, list[str]]]` (thay cho `_ID_ORDER_V2`/
  `_PRIMARY_IDS_V2`/`_sort_ids_v2` trước đây nằm trong `viz/value_chain.py`) — chuyển logic sắp
  xếp/phân loại Chính-Hỗ trợ sang tầng du liệu (repository) vì `pages/2_Chuoi_gia_tri.py` giờ cần
  gọi trực tiếp (không còn qua 1 ham dung Plotly duy nhat).
- **Cach dung**: voi moi band tu `vc1_bands()`, ve 1 hang `st.columns(len(ids))`, moi cot la 1
  `st.container(border=True)` (ten khoi to mau qua `rcm_block_health_color()`, giong het style o
  VC2) + nut "Chọn khối"/"✓ Đang chọn". Ngay SAU vong lap ve ca hang (ngoai `with col:`), kiem tra
  `if selected_block_id in ids: _render_block_expansion(selected_block_id)` — vi day la code binh
  thuong sau khi cac `st.columns()` cua hang do da dong, noi dung se rong full trang va nam dung
  ngay sau hang vua ve, KHONG phai cuoi trang (moi band tu ve xong hang cua no roi moi kiem tra mo
  rong, nen band Ho tro luon ve SAU band Chinh, giu dung thu tu doc).
- **State**: `st.session_state["_vc2_selected_block_id"]` (luu `vc1_id` ON dinh, KHONG phai
  `vc1_name` nhu ban Plotly cu - nhat quan voi nguyen tac "luon khop theo ma on dinh" da rut ra
  o Muc 11.3) - set truc tiep khi bam nut (khong can co che "ack" chong-bam-lai-do-Plotly-rerun
  nhu truoc, vi nut Streamlit tu nhien khong bi trigger lai qua nhieu lan tren 1 lan bam that).
  Reset ve `None` cung voi `_vc2_selected_group` khi doi khoi hoac bam "✕ Đóng".
- `build_risk_by_function_bar_v2()` (bar chart "Rủi ro theo khối chức năng" o cuoi trang) VAN
  con dung Plotly nhu cu - KHONG lien quan toi thay doi nay, chi doi rieng phan 9 khoi VC1.

### 11.8. Xem chi tiết rủi ro + chốt kiểm soát CADIVI_RCM ở cấp nhóm nhỏ (VC2)

Người dùng phát hiện thực tế: ô nhóm "OP-02" hiện "1 rủi ro" (gộp Sheet1 + CADIVI_RCM, xem Mục
11.6) nhưng không có hoạt động VC3 con nào bên dưới hiện rủi ro nào — vì rủi ro đó là của
CADIVI_RCM, gắn ở cấp nhóm nhỏ (`vc2_id` của chính CADIVI_RCM, xem Mục 11.4), không có thông tin
xuống được hoạt động cụ thể nào, nên trước đây **không có cách nào xem được rủi ro đó là gì**.

- Trong `_render_block_expansion()` (`pages/2_Chuoi_gia_tri.py`), mỗi ô nhóm trên lưới VC2 nay có
  thêm nút thứ 2 (dưới nút "Chọn nhóm"): `group_rcm_rows = rcm[rcm["vc2_id"] == g["group_id"]]`
  → có dữ liệu → nút bấm được, nhãn `"🗂️ Xem rủi ro và kiểm soát (n)"`; KHÔNG có dữ liệu → nút
  **vô hiệu hoá** (`disabled=True`), nhãn "Không có rủi ro/kiểm soát" — **cố ý giữ nguyên vị trí
  thay vì ẩn hẳn**, để mọi ô trong cùng 1 hàng vẫn cao bằng nhau (không phá lại phần căn đều chiều
  cao ô ở `_uniform_name_height()`, xem lần sửa trước Mục 11 gần nhất) — đã xác nhận với người
  dùng qua mockup trước khi code.
- `src/components/risk_dialog.py` tách phần vẽ 1 thẻ rủi ro CADIVI_RCM (trước đây nằm inline
  trong vòng lặp cuối `show_activity_risks()`) ra hàm dùng chung `_render_rcm_card(r)`, và thêm
  hàm mới `show_group_rcm_risks(rcm_risks, subject_label, subject_sub="")` — hộp thoại CHỈ hiện
  danh sách rủi ro CADIVI_RCM của 1 nhóm (KHÔNG có mục "Từ Sheet1" như `show_activity_risks()`, vì
  ở cấp nhóm không có dữ liệu Sheet1 trực tiếp — Sheet1 chỉ gắn tới cấp hoạt động VC3).
- ⚠️ **Thêm 2 trường mới vào CẢ 2 khung mở rộng Entity/Transaction Level** (áp dụng cho MỌI nơi
  dùng `_render_rcm_card`, kể cả hộp thoại rủi ro theo hoạt động cụ thể VC3 đã có từ Mục 11.4):
  **"Đánh giá hiệu lực"** (`ent_valid`/`tx_valid`) và **"Đánh giá hiệu quả"** (`ent_effective`/
  `tx_effective`) — 2 giá trị này TRƯỚC ĐÂY đã đọc sẵn để tính emoji màu qua
  `_rcm_effectiveness_key()` nhưng CHƯA hiện tường minh, chỉ ẩn sau màu 🟢🟠🔴⚪; người dùng yêu
  cầu hiện rõ khi xem mockup, đặt ở cuối danh sách trường mỗi khung.

### 11.9. Bỏ hẳn rủi ro từ `2_VC_Master` (mã `RSK-xxx`) — trang Chuỗi giá trị chỉ còn CADIVI_RCM

Người dùng xác nhận dữ liệu rủi ro nhúng trực tiếp trong sheet `2_VC_Master` (cột `Risk`/
`Risk_ID`/`Problem`/`Details`, mã `RSK-xxx` — nguồn được mô tả ở Mục 11.3) **không còn đáng tin/
không còn dùng** — yêu cầu bỏ hẳn. `2_VC_Master` **vẫn là nguồn DUY NHẤT cho cấu trúc phân cấp
VC1→VC2→VC3** (không đổi) — chỉ bỏ phần dữ liệu rủi ro nhúng trong sheet đó. Từ mục này trở đi,
**CADIVI_RCM là nguồn rủi ro DUY NHẤT** trên trang Chuỗi giá trị.

- `repository.get_value_chain_v2()` **không còn rename/trả về** `risk_name`/`risk_id`/`problem`/
  `details` — cột gốc `Risk`/`Risk_ID`/`Problem`/`Details` vẫn còn tồn tại thô trong DataFrame trả
  về (hàm không lọc bỏ cột, chỉ không alias sang tên snake_case như trước) nhưng KHÔNG có nơi nào
  trong code còn đọc tới, coi như dữ liệu vết tích — đúng tinh thần đã rút ra ở Mục 11.3 (đừng giả
  định tên cột cũ biến mất, chỉ ngừng dùng).
- `risk_dialog.show_activity_risks()` (hộp thoại rút gọn rủi ro Sheet1 + CADIVI_RCM ở cấp hoạt
  động VC3, xem Mục 11.3/11.4) **đã XOÁ HẲN** — không còn nơi nào gọi sau khi bỏ nút "Xem rủi ro"
  trên danh sách VC3 (xem dưới). `show_group_rcm_risks()` (Mục 11.8) là hộp thoại chi tiết rủi ro
  DUY NHẤT còn lại trên trang, chỉ hoạt động ở cấp nhóm nhỏ VC2 (đúng cấp CADIVI_RCM khớp thật).
- `viz.value_chain.build_risk_by_function_bar_v2()` đổi chữ ký: nhận thẳng 1 `pd.Series` đếm sẵn
  (index = tên khối, value = số rủi ro CADIVI_RCM) thay vì nhận `vc2` df và tự đếm `risk_id` như
  trước — trang tính `rcm_by_block = rcm.groupby("vc1_id").size()` rồi `.rename(index=
  vc1_id_to_name).reindex(...)` trước khi truyền vào, tách hẳn khỏi Sheet1.
- `pages/2_Chuoi_gia_tri.py` — các thay đổi chính:
  - KPI "Hoạt động có rủi ro" (Sheet1-based) đổi thành **"Nhóm có rủi ro"** = số `group_id` (VC2)
    duy nhất có ít nhất 1 dòng CADIVI_RCM / tổng số nhóm. KPI "Tổng rủi ro" chỉ còn đếm CADIVI_RCM
    (bỏ cộng Sheet1). Câu "Điểm cần chú ý" (hotspot khối nhiều rủi ro nhất) tính thẳng từ
    `rcm_by_block`, không còn gộp `sheet1_by_block`.
  - Danh sách "Hoạt động trong nhóm" (VC3, hiện khi bấm 1 ô nhóm VC2) **giữ nguyên** (mã + tên +
    phân loại, vẫn dùng để xem cấu trúc) nhưng **bỏ cột số rủi ro + nút "Xem rủi ro"** — quyết
    định giữ danh sách thay vì xoá hẳn vì vẫn có giá trị điều hướng/xem cấu trúc dù không còn rủi
    ro gắn ở cấp này nữa (đã chốt qua AskUserQuestion).
  - Khối **"Chi tiết hoạt động"** ở cuối trang (chọn 1 hoạt động + bảng rủi ro Sheet1) **đã bỏ
    hẳn** — hết ý nghĩa vì CADIVI_RCM không có dữ liệu ở cấp hoạt động cụ thể (VC3). Layout 2 cột
    (`col_bar, col_detail`) đổi thành 1 cột full-width cho biểu đồ "Rủi ro theo khối chức năng".
  - Câu info cuối trang ("không vẽ mũi tên luồng quy trình") đổi từ nhắc "Sheet1" sang
    "2_VC_Master" cho khớp tên sheet hiện tại (không liên quan tới thay đổi rủi ro — chỉ sửa luôn
    vì phát hiện tên cũ còn sót lại khi test).
- Rút kinh nghiệm: khi người dùng nói "không dùng gì đến X" (ở đây là rủi ro trong 1 sheet), luôn
  hỏi rõ PHẠM VI trước khi sửa (Mục nào giữ/mục nào bỏ hẳn) — trang này có tới 5 chỗ phụ thuộc dữ
  liệu đó (KPI, hotspot, màu/đếm ô khối-nhóm, danh sách VC3, khối chi tiết + biểu đồ cuối trang),
  không thể đoán 1 câu ngắn gọn ứng với toàn bộ 5 chỗ theo cùng 1 cách.
