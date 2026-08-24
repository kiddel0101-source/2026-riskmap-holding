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

### 11.2. "Rủi ro có thể kích hoạt" — ĐÃ CHUYỂN sang `Risk_Linkages` + `Sheet1` (Phần 3)

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

⚠️ **App hiện có 2 mô hình Chuỗi giá trị SONG SONG, đừng nhầm lẫn:**

- `2_Value_Chain_Master` (qua `repository.get_value_chain()` + `viz.value_chain.build_value_chain_map()`)
  — mô hình CŨ, có cột `company_id` (theo từng công ty CADIVI/EMIC), 7 khối, `vc_node_id` kiểu
  "MS-001". Vẫn dùng ở **Trang chủ** và **Sự kiện rủi ro** (dò từ khóa hoạt động Chuỗi giá trị) —
  KHÔNG đổi ở 2 trang này.
- `Sheet1` (qua `repository.get_value_chain_v2()`) — mô hình MỚI, **không có cột công ty** (dùng
  chung toàn Tập đoàn), đủ **9 khối Porter** (thêm Cơ sở hạ tầng doanh nghiệp + Quản trị nguồn
  nhân lực), có rủi ro gắn TRỰC TIẾP theo hoạt động (`risk_id` dạng `RSK-xxx`, không phải
  `RR.xxxx`). Chỉ dùng riêng ở **trang Chuỗi giá trị** (`pages/2_Chuoi_gia_tri.py`) — đã thay thế
  hoàn toàn mô hình cũ ở trang này theo yêu cầu người dùng.
- ⚠️ Sheet1 vừa bị đổi tên 2 cột gốc trên SharePoint (`Chuỗi giá trị 1`→`Value Chain`, `Chuỗi giá
  trị 2`→`Sub-Value Chain`) — `get_value_chain_v2()` nhận cả tên cũ/mới để không vỡ lại nếu người
  phụ trách dữ liệu đổi tên tiếp.
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
