---
name: ve-may-bay-noi-dia
description: Thu thập và đối chiếu giá vé máy bay nội địa Việt Nam từ nhiều nguồn, rồi xuất file Excel so sánh. Use when người dùng muốn so sánh giá vé, tìm vé rẻ, quét giá nhiều ngày bay, dò giá khứ hồi, hoặc lập bảng so sánh chuyến bay — ví dụ "so giá vé SGN đi Đà Nẵng tháng 8", "tìm vé rẻ nhất HAN-SGN mấy cuối tuần tới", "quét giá vé máy bay giúp huynh", "compare flight prices Vietnam domestic", "check vé Tết". KHÔNG dùng cho chặng quốc tế (logic nối chuyến và hạng vé khác hẳn).
metadata:
  version: "1.1.0"
  updated: "2026-08-11"
  source: "https://github.com/hoanghieu512/san-ve-may-bay-skill"
---

# Thu thập & so sánh giá vé nội địa VN

**v1.1.0** · cập nhật 11/08/2026 · nguồn: `github.com/hoanghieu512/san-ve-may-bay-skill`

Quét giá thật từ Google Flights / Traveloka bằng Claude in Chrome, đối chiếu chéo, xuất Excel 3 sheet.

> Người dùng hỏi skill này version mấy / có mới nhất không → đọc số trên, đối chiếu với
> `git tag` mới nhất ở repo nguồn. Lệch nghĩa là bản đang nạp đã cũ, cần build lại gói
> `.skill` rồi Save đè.

## 1. Nguyên tắc bất di bất dịch

Đây là file người dùng sẽ dựa vào để tiêu tiền thật. Vi phạm phần này làm toàn bộ deliverable trở nên có hại.

1. **TUYỆT ĐỐI KHÔNG BỊA GIÁ.** Không suy đoán, không nội suy, không "ước lượng theo mặt bằng", không dùng kiến thức có sẵn. Chỉ ghi con số đọc trực tiếp trên trang tại thời điểm quét.
2. Ô không lấy được → ghi `Không khả dụng` **kèm lý do** vào sheet `Log` (bị chặn / cần login / captcha / hết chuyến / hãng không bán / ngoài khung giờ).
3. **Một file nhiều ô `Không khả dụng` trung thực tốt hơn một file đầy đủ có số bịa.** Khi phải chọn, luôn chọn trung thực.
4. Mỗi mức giá bắt buộc có link nguồn + timestamp.
5. Không đăng nhập, không nhập thanh toán, không bấm đặt vé. Gặp captcha → **dừng, báo người dùng, chờ**. Không tự giải, không vòng qua.
6. Cookie/consent → chọn phương án bảo vệ riêng tư nhất.

## 2. Tham số — hỏi nếu thiếu

| Tham số | Mặc định |
|---|---|
| Chặng | *(bắt buộc hỏi)* |
| Cặp ngày đi/về | *(bắt buộc hỏi — nếu người dùng chưa chốt, chạy §3 trước)* |
| Khung giờ đi / về | Không lọc — hỏi người dùng có muốn lọc không |
| Số khách / hạng | 1 người lớn / Phổ thông |
| Loại chuyến | Chỉ bay thẳng |
| Hành lý | Không ký gửi (lấy hạng vé rẻ nhất còn bán) |
| Nguồn | Google Flights (bắt buộc) + Traveloka (mặc định bật) |
| Web hãng | **Mặc định TẮT** làm nguồn giá — xem §7 |

## 3. Bước 0 — Quét ngày (bỏ qua nếu người dùng đã chốt cặp ngày)

Khi người dùng nói "tháng 8 có ngày nào rẻ", "mấy cuối tuần tới", hoặc chưa chốt cặp ngày
cụ thể — **đừng đoán, cũng đừng quét bừa 8 cặp**. Chạy `scripts/vna_date_scan.js` qua
`browser_run_code_unsafe`: **2 request HTTP** trả giá thấp nhất từng ngày của Vietnam
Airlines cho tối đa 181 ngày, cả hai chiều, đã ghép sẵn cặp đi/về.

Không cần navigate, không cookie, không captcha. Chi phí ~1 tool call — rẻ hơn quét thật
hai bậc độ lớn. Đọc `references/vna-date-scan.md` trước.

**Đây là công cụ chọn ngày, KHÔNG phải nguồn giá.** Chỉ có min-của-cả-ngày, không có số
hiệu chuyến, không có giờ bay, chỉ Vietnam Airlines. **Không đưa vào `meta.nguon`, không
thêm cột vào workbook** — đặt cạnh cột giá theo chuyến là so sai đơn vị. Ghi một dòng vào
`Log` là đủ.

Đưa kết quả cho người dùng bằng **AskUserQuestion** — 2-3 nhóm cặp ngày (rẻ nhất / cuối
tuần / linh hoạt) kèm giá tham chiếu — rồi mới sang §4. Nói rõ con số này là tham chiếu
VNA cả ngày, giá thật theo chuyến có thể cao hơn nếu họ lọc khung giờ.

## 4. Bước 0.5 — Ước lượng ngân sách TRƯỚC khi quét

Bỏ qua bước này là lỗi nghiêm trọng nhất có thể mắc: nó khiến kế hoạch vỡ ở giữa chừng, sau khi đã tiêu phần lớn ngân sách.

Đơn vị công việc là **chặng one-way** = số cặp ngày × 2.

| Nguồn | Công cụ | Thao tác / chặng | Phủ hãng | Số hiệu chuyến |
|---|---|---|---|---|
| Traveloka | **Playwright** | **~1** (gộp nhiều chặng 1 call) | Thiếu Bamboo | Có (trong JSON) |
| Google Flights | Playwright / Chrome | ~2 | Toàn bộ | Có (phải bung từng dòng) |
| Traveloka | Claude in Chrome | ~7 + 3 ảnh | Thiếu Bamboo | Không |
| Web hãng | cả hai | ~15+ **mỗi hãng** | 1 hãng / site | Có |

Nếu Playwright MCP có sẵn, Traveloka rẻ hơn ~15–20 lần — đọc `references/playwright-path.md`.

Tính tổng, rồi **dùng AskUserQuestion đưa ra 2-3 phương án phạm vi kèm ưu/nhược** trước khi tốn thao tác nào. Ví dụ 4 cặp × 2 nguồn ≈ 36 thao tác (chạy tốt); 8 cặp × 2 nguồn ≈ 72 (vẫn được); thêm web hãng cho 4 hãng ≈ 480 (không khả thi).

## 5. Bước 1 — Verify hãng khai thác

**Không hard-code danh sách hãng.** Thị trường VN đổi liên tục — hãng mới xuất hiện, hãng cũ cắt chặng. Chạy một lượt Google Flights bất kỳ trên chặng đó, đọc xem hãng nào thực sự bay, ghi kết quả vào `Log`.

Lưu ý đã gặp: Pacific Airlines chỉ bay codeshare dưới mã VN. Bamboo Airways còn khai thác nhưng Traveloka không bán. Google Flights xếp một số hãng vào mục "Phổ thông cao cấp" — hỏi người dùng có tính vào không.

## 6. Bước 2 — Quét

**LUÔN search one-way từng chiều. KHÔNG BAO GIỜ search khứ hồi.**

Chế độ khứ hồi của Google Flights trả về *tổng* khứ hồi khi ghép với chuyến về rẻ nhất — không tách được giá từng chặng, nên không dựng được bảng so sánh theo chuyến. Vé nội địa VN không có discount khứ hồi, nên `tổng = đi + về` luôn đúng.

**Chọn công cụ:**

- Có Playwright MCP → dùng `scripts/tvl_playwright.js` cho Traveloka. Bắt thẳng JSON của API, không scroll, không ảnh. **Đọc `references/playwright-path.md` trước** — có một bẫy làm mất dữ liệu mà không báo lỗi.
- Không có Playwright, hoặc trang cần đăng nhập → Claude in Chrome với `scripts/gf_extract.js` và `scripts/tvl_extract.js`.

Đọc `references/site-quirks.md` trước khi chạm vào trang — nó chứa các bẫy đã mất công mới tìm ra (danh sách virtualized, nhiều hạng vé một chuyến, số hiệu chuyến ẩn).

Thứ tự quét: **tự do**. Cross-check hợp lệ miễn hai nguồn cách nhau dưới ~2 giờ. Thực nghiệm trên chặng nội địa: quét hết một nguồn rồi sang nguồn kia, cách nhau ~40 phút, lệch chỉ 0,2–2,2%. Quét theo nguồn rẻ hơn vì tái dùng được extractor.

Sau **mỗi chặng**: chạy sanity check (số kết quả thô và số hãng — xem `playwright-path.md`), ghi JSON thô ra file, báo tiến độ một dòng. Không giữ dữ liệu trong đầu.

**Không bao giờ chấp nhận một chặng có ít chuyến bất thường mà không điều tra.** Cả hai công cụ đều có thể trả dữ liệu thiếu một cách im lặng: Chrome vì danh sách virtualized chưa nạp hết, Playwright vì body bị cắt khi navigate quá sớm. Ít chuyến có thể là thật, nhưng phải xác minh chứ không mặc định.

### Ghép nguồn — đừng viết lại bằng tay

Quét xong thì **dùng `scripts/merge_sources.py`**, đừng tự viết code ghép cho từng lần chạy. Nó nhận một `job.json` mô tả chặng và cặp ngày, trả về checkpoint đúng schema, tự chuẩn hoá tên hãng và tự sinh các dòng `Log` bắt buộc. Đọc `references/merge-sources.md`.

```bash
python3 scripts/merge_sources.py job.json checkpoint.json
```

### Ngưỡng bắt buộc điều tra — không phải gợi ý

**Hai nguồn lệch ≥25% cho cùng một chuyến → phải điều tra trước khi build workbook.** Cả `merge_sources.py` lẫn `build_workbook.py` đều đếm và in cảnh báo ra stderr; workbook tô cam những dòng đó.

Không được bỏ qua, và cũng không được sửa/lọc số. Việc phải làm: mở lại nguồn cao hơn, xem nó đang bán hạng vé nào, rồi ghi kết luận vào `Log`. Nếu không xác minh được thì ghi thẳng là chưa xác minh được.

Ví dụ đã gặp (09/08/2026): Sun PhuQuoc Airways lệch 78–123% ở mọi chặng vì Google Flights chỉ truy cập được hạng vé đắt của hãng này. **Điều đó không đổi chuyến rẻ nhất** — đã kiểm chứng 16/16 chiều hai nguồn chọn cùng một chuyến — **nhưng làm hỏng nhận xét ở §9 về hãng nào rẻ**. Đừng xếp hạng hãng bằng những dòng bị tô cam.

## 7. Web hãng — vẫn mặc định TẮT làm nguồn giá theo chuyến

"Website chính thức của hãng" nghe như một nguồn nhưng thực chất là **N site độc lập**, mỗi site một form nhiều tầng, có reCAPTCHA. Chi phí ~15+ thao tác/site/chặng và không phải lúc nào cũng lấy được số.

Chỉ bật khi người dùng yêu cầu rõ, và giới hạn **1 hãng × 1 chặng** để calibrate xem Google Flights lệch bao nhiêu so với giá gốc. Ghi kết quả calibrate vào `Log`.

**Ngoại lệ đã kiểm chứng 09/08/2026 — Vietnam Airlines, chỉ cho giá theo NGÀY.** VNA có API công khai `air-best-price` không cần auth, không captcha — đó là §3. Nó khớp Google Flights đến từng đồng ở 3/3 ngày đối chiếu được, nhưng **không có số hiệu chuyến và không có giờ bay** nên không thay được nguồn giá theo chuyến. Đừng nhầm hai việc này.

Toàn bộ chuỗi form VNA (chọn sân bay → calendar) cũng đã dò thông qua Playwright — xem `site-quirks.md`. Nhưng nếu chỉ cần giá theo ngày thì **không cần đụng tới form**, gọi thẳng API nhanh hơn nhiều. Chưa ai vượt qua bước submit "Tìm chuyến bay" (reCAPTCHA Enterprise) và **cũng không cần vượt**.

Các hãng khác (VJ / VU / QH) chưa dò. Rất có thể cũng có endpoint tương tự — đáng thử `browser_network_requests` với filter `price|fare|calendar` khi mở calendar của họ, trước khi bỏ công tự động hoá form.

Cảnh báo LCC cộng thuế phí ở bước sau **chỉ áp dụng cho web hãng**. Google Flights và Traveloka đã hiển thị giá all-in — đừng lặp lại cảnh báo này cho hai nguồn đó. Giá `total` của API VNA cũng đã all-in.

## 8. Bước 3 — Xuất Excel

Chuỗi đầy đủ: **extract → `merge_sources.py` → `build_workbook.py` → recalc → đối chiếu.**

`scripts/build_workbook.py <checkpoint.json> <output.xlsx>` → 3 sheet:

- **Data** — nhóm theo cặp ngày. Block A (chiều đi), Block B (chiều về), Block C (phương án ghép: "Rẻ nhất" và "Cùng hãng rẻ nhất"). Cột giá sinh động theo số nguồn thực quét; `Chênh lệch max %` chỉ xuất hiện khi có ≥2 nguồn.
- **Summary** — mỗi cặp một dòng, sắp xếp tổng tăng dần.
- **Log** — bắt buộc. Đây là bằng chứng phân biệt "ô trống vì hết chuyến" với "ô trống vì bị chặn".

Màu trong sheet `Data`: **vàng** = rẻ nhất trong chiều đó; **cam** = hai nguồn lệch ≥25%, số đáng ngờ. Ô cam không phải giá để tiêu tiền — đọc `Log` trước.

Sau khi build, làm **hai bước tách biệt**:

**1. Recalc.** `recalc.py` **KHÔNG nằm trong skill này** — nó thuộc skill `xlsx` có sẵn của hệ thống. Định vị nó rồi chạy:

```bash
RECALC=""
for p in /sessions/*/mnt/.claude/skills/xlsx/scripts/recalc.py \
         "$HOME/.claude/skills/xlsx/scripts/recalc.py"; do
  [ -f "$p" ] && { RECALC="$p"; break; }
done
[ -z "$RECALC" ] && RECALC=$(find "$HOME/.claude" \
  "$HOME/Library/Application Support/Claude/local-agent-mode-sessions" \
  /sessions /mnt -maxdepth 12 -path '*/skills/xlsx/scripts/recalc.py' 2>/dev/null | head -1)
python3 "$RECALC" <output.xlsx> 180
```

Đường dẫn skill hệ thống đổi theo phiên **và theo môi trường** nên phải dò. Hai glob đầu bắt
đường nhanh (sandbox Cowork `/sessions/*/mnt/...`, và thư mục skill cá nhân). Nhánh `find`
là dự phòng cho Claude Code trên macOS, nơi skill hệ thống nằm sâu trong
`~/Library/Application Support/Claude/local-agent-mode-sessions/.../skills/xlsx/`. Đo thực tế
trên máy local: **~0,8 giây**. **Đừng dùng `find /`** — mất ~53 giây. Nếu vẫn không thấy, gọi
skill `xlsx` để nó tự nạp.

`recalc.py` cần **LibreOffice** (`soffice` trên PATH) và import package `office/` nằm cạnh nó
trong `scripts/` — gọi bằng đường dẫn tuyệt đối như trên là đủ, không cần chỉnh `PYTHONPATH`.
Thiếu `soffice` thì nó báo lỗi rõ ràng chứ không âm thầm bỏ qua.

openpyxl ghi công thức dưới dạng chuỗi **không kèm giá trị**, nên chưa recalc thì mọi ô công thức đọc ra `None`. Bỏ bước này là file giao đi trông rỗng.

**2. Đối chiếu độc lập bằng Python.** Load lại file với `data_only=True`, kiểm tra `Giá chốt` khớp nguồn, `Tổng khứ hồi` khớp `Giá đi + Giá về`, `Summary` khớp kết quả tính tay từ dữ liệu thô.

**Recalc sạch chỉ chứng minh công thức *chạy được*, không chứng minh *đúng*.** Một range lệch một dòng vẫn cho file 0 lỗi với số sai. Bước 2 mới là bước bắt lỗi thật.

Nếu đã chạy §3: đối chiếu giá VNA thấp nhất mỗi ngày trong workbook với con số quét ngày. Lệch nhiều (ngoài ~5%) là dấu hiệu quét sót chuyến hoặc giá đã đổi giữa hai lần — điều tra trước khi giao file.

Đặt tên file kèm timestamp để so sánh biến động giữa các lần quét.

## 9. Bước 4 — Nhận xét (trong chat, không cần trong file)

Chỉ dựa trên số đã thu, không suy diễn ngoài dữ liệu:

1. Cặp rẻ nhất / đắt nhất, chênh bao nhiêu %
2. Hãng nào thường rẻ nhất — nêu rõ chiều nào, khung giờ nào
3. Khung giờ nào giá tốt
4. Mua ngay hay theo dõi — **trả lời riêng từng cặp**, không kết luận chung

Bắt buộc kèm: timestamp, cảnh báo giá thay đổi liên tục, và **tỷ lệ phủ dữ liệu** (bao nhiêu ô có giá thật / bao nhiêu `Không khả dụng`).

**Nêu giả thuyết rồi kiểm chứng bằng số — và nói rõ khi dữ liệu bác bỏ nó.** Ví dụ thực tế: giả thuyết "cặp sát lễ đắt vì chiều về sát lễ" đã bị bác bỏ — chiều về sát lễ chỉ đắt hơn 0,3%, toàn bộ phần đắt nằm ở chiều đi Thứ 6 (+52,7%). Tách theo từng chiều trước khi kết luận về cả cặp; hai hiệu ứng ngược chiều có thể triệt tiêu nhau ở mức tổng.

Với ít hơn ~6 cặp ngày, không đủ điểm dữ liệu để tách hiệu ứng "booking horizon" khỏi hiệu ứng "ngày trong tuần". Nói thẳng là không kết luận được thay vì đoán.
