# Bẫy từng trang — đọc trước khi quét

Mỗi mục dưới đây là một thứ đã mất thời gian thật mới tìm ra.

## Google Flights

**URL one-way** (đổi ngày/sân bay là dùng được ngay, không cần điền form):
```
https://www.google.com/travel/flights?q=Oneway%20flights%20from%20SGN%20to%20DAD%20on%202026-08-06&curr=VND&hl=vi&gl=VN
```
`curr=VND` bắt buộc, nếu không sẽ ra USD.

**Số hiệu chuyến KHÔNG có trong danh sách.** Phải click nút có `aria-label` bắt đầu bằng `"Thông tin"` trên từng dòng rồi mới đọc được `VJ 628`, `VN 104`… → **lọc khung giờ TRƯỚC khi bung**, chỉ bung 8-10 dòng thay vì cả 39.

**Bung dòng phải đợi trang hydrate xong.** Thử 23/10/2026 qua Playwright: click ngay sau khi `li.pIav2d` vừa xuất hiện thì không dòng nào bung; đợi thêm ~3 giây thì bung đủ 10/10, kể cả click bằng JS (`element.click()`). Vì vậy `gf_extract.js` dặn chờ ~8 giây sau navigate.

**Regex số hiệu:** dùng `/(VN|VJ|QH|VU|BL|9G)\s?\d{2,4}/`. Mã của Sun PhuQuoc Airways là **`9G`** (trang hiện `Airbus A321neo9G 954`); bản cũ ghi `SP` nên luôn trượt số hiệu hãng này. Đừng dùng `\b[A-Z]{2}\s?\d{2,4}\b`: text hiển thị là `Airbus A321VJ 628`, chữ `1` liền `V` nên không có word boundary, sẽ trượt.

**Nhận diện dòng chuyến bay phải dùng `aria-label` "Thời gian khởi hành", KHÔNG dùng mã sân bay.** Dòng chưa bung hiển thị `SGN–DAD`; sau khi bung, cùng dòng đó đổi sang `08:25Cảng hàng không quốc tế Đà Nẵng (DAD)`. Mọi regex kiểu `[A-Z]{3}–[A-Z]{3}` sẽ khớp ở lượt đọc đầu (nên vẫn bung được) rồi loại sạch dòng ở lượt đọc thứ hai — kết quả trả về **rỗng hoàn toàn mà không báo lỗi**. Bẫy này đã thực sự xảy ra.

**Giá bất thường:** thỉnh thoảng một chuyến hiện giá gấp ~7 lần mặt bằng (ví dụ 16.082.000 ₫ cho SGN–DAD một chiều) — gần như chắc chắn chỉ còn ghế hạng Thương gia. Ghi nguyên số đọc được và ghi chú vào `Log`; đừng lọc bỏ, đừng sửa.

**Giờ khởi hành** đọc từ `aria-label` khớp `/^Thời gian khởi hành/` — chính xác hơn parse innerText.

**Dòng lồng nhau:** các `<li>` chứa nhau. Lọc `rows.filter(x => !rows.some(o => o!==x && x.contains(o)))`. Dòng chưa bung có `arr === dep`; ưu tiên bản có `arr` khác `dep`.

**Giá đã gồm thuế + phí bắt buộc** cho 1 người lớn (Google ghi rõ). Chưa gồm phí hành lý ký gửi.

**Giá ở danh sách thường là giá của hãng, chưa chắc là giá mua thấp nhất.** Bấm vào một chuyến (một chiều) là sang trang đặt vé `/travel/flights/booking?tfs=...` liệt kê từng người bán kèm giá. VJ 632 ngày 14/11/2026: danh sách 742.061 ₫ (Vietjet), đại lý Jettzy 679.301 ₫. Link trang đặt vé dựng được từ số hiệu mà không cần bấm, xem `references/gf-booking.md`.

**Codeshare:** chuyến Pacific Airlines hiện dưới tên `Vietnam Airlines` kèm dòng "Do Pacific Airlines khai thác", số hiệu mã VN (vd `VN 6030`).

**Số hiệu dùng NBSP** (`VJ\u00a0636`), không phải dấu cách thường. Không chuẩn hoá thì Ctrl+F "VJ 636" trong Excel không ra. `gf_extract.js` và `merge_sources.py` đều đã thay bằng dấu cách.

**Captcha theo lượng truy cập.** 23/10/2026, từ một IP cloud: khoảng 30 lượt tải trang Google Flights (danh sách + trang đặt vé, nhiều context trắng) trong khoảng 40 phút thì bị trang "Hệ thống của chúng tôi đã phát hiện thấy lưu lượng truy cập bất thường". IP dân dụng ở nhà có thể chịu được nhiều hơn, chưa đo. Trang captcha **không có dòng chuyến bay nào**, nên trước v1.5.0 `gf_extract.js` trả về y như "khung giờ này không có chuyến". Giờ nó trả `# CHAN: ...` (captcha) hoặc `# CANH BAO: 0 dong ...` (trang trống), còn `gf_booking.js` dừng và trả `dung`. Gặp một trong hai: dừng, báo người dùng (SKILL.md §1.5), không quét tiếp.

**"Phổ thông cao cấp"** là mục riêng cuối danh sách — giá cao hơn hẳn, không cùng hạng vé. Hỏi người dùng có tính vào không.

## Traveloka

**URL:**
```
https://www.traveloka.com/vi-vn/flight/fullsearch?ap=SGN.DAD&dt=06-08-2026.NA&ps=1.0.0&sc=ECONOMY
```
`dt` định dạng `DD-MM-YYYY`, `.NA` = một chiều.

**Chờ nạp:** poll cho tới khi `"Đang tìm kiếm"` biến mất khỏi `document.body.innerText`, tối đa ~50 giây.

**Danh sách VIRTUALIZED — đây là bẫy lớn nhất.** `window.scrollBy` và `window.scrollTo` **không** kích hoạt lazy-load; `scrollHeight` đứng yên và chỉ nạp được ~8-11 dòng. Phải scroll thật bằng `computer` action `scroll`. Hai cách giảm chi phí:
1. Bấm bộ lọc khung giờ của Traveloka để list ngắn lại → thường chỉ cần 2-3 lần scroll.
2. Capture tích lũy vào một dict sau mỗi lần scroll, đừng đợi tới cuối mới đọc — dòng cũ bị unmount.

**Bấm bộ lọc bằng JS được** (React nhận `element.click()`): tìm `div/label/span` có `innerText.trim()` đúng bằng `"Buổi sáng"` / `"Buổi chiều"` / `"Buổi tối"`, rồi `.click()` phần tử tổ tiên cách 3 cấp. Lưu ý có **hai** khối khớp — khối đầu là "Giờ khởi hành", khối sau là "Giờ đến nơi"; lấy `[0]`. Bấm liên tiếp 2 bộ lọc đôi khi bỏ bộ đầu — kiểm tra lại, hoặc bấm cái thứ hai bằng click thật.

**MỘT CHUYẾN CÓ NHIỀU HẠNG VÉ**, liệt kê rời nhau trong danh sách, giá tăng dần. Key theo `(giờ khởi hành, hãng)` và **luôn lấy MIN** — nếu ghi đè theo thứ tự gặp sẽ dính hạng đắt nhất (0kg → 30kg hành lý, chênh tới 50%).

**Nối chuyến** cũng nằm chung danh sách. Lọc bằng cách yêu cầu chuỗi `"Bay thẳng"` xuất hiện trong text của dòng.

**Tên hãng khác Google Flights:** `VietJet Air` ↔ `Vietjet`, `SUN PhuQuoc AIRWAYS` ↔ `Sun PhuQuoc Airways`. Chuẩn hóa trước khi ghép.

**Không bán Bamboo Airways** (đã xác nhận trên 4 ngày khác nhau). Bộ lọc hãng của Traveloka không liệt kê Bamboo dù Google Flights có bán chuyến đó.

**Giá đã all-in.** Nhãn hành lý (`0kg` / `1x23kg`) hiển thị ngay trên dòng — dùng để xác nhận đúng hạng không ký gửi.

## Web hãng (chỉ khi được yêu cầu)

**vietnamairlines.com** — nếu chỉ cần **giá thấp nhất từng ngày**, ĐỪNG đụng vào form:
gọi thẳng API `air-best-price`, xem `references/vna-date-scan.md`. Hai request, không
captcha. Phần dưới chỉ dùng khi cần giá theo *chuyến cụ thể*.

Form hoạt động: click ô "Từ" → gõ mã sân bay → chọn từ dropdown → tab
`Khứ hồi / Một chiều / Nhiều chặng` nằm **trong `#bookingSection`**, ngoài modal. **Ô ngày
không nhận gõ trực tiếp**, phải mở calendar và chọn ô. Có reCAPTCHA Enterprise (invisible)
ở bước submit — chưa ai vượt qua và cũng chưa cần.

Banner cookie OneTrust: xem mục Playwright bên dưới, cách xử lý khác nhau giữa Chrome và
Playwright.

**Chi phí thực đo qua Claude in Chrome: 12+ thao tác mà vẫn chưa lấy được giá nào.** Đừng
đánh giá thấp. Qua Playwright thì chuỗi form chạy thông (mục dưới), nhưng vẫn đắt hơn API.

---

# Playwright MCP — đo thực tế 09/08/2026

Bản Playwright MCP đang dùng: **`browser_route` và `browser_mouse_wheel` KHÔNG tồn tại.**
Đừng đi tìm. Không cần thiết nữa — `page.on('response')` trong `browser_run_code_unsafe`
đã giải quyết xong.

## Traveloka

- **Không chặn.** `navigator.webdriver` + profile trắng không kích hoạt gì. Traveloka *có*
  chống bot (`sentinel.token` trong request body) nhưng vẫn cấp token bình thường.
- Endpoint: `POST /api/v2/flight/search/initial`, response ~700KB, chứa **toàn bộ** chuyến
  của ngày đó (~110–130 phần tử cho SGN–DAD).
- **`searchId` là one-shot** — replay request với đúng body/ngày/token vẫn trả
  `searchResults` rỗng (HTTP 200). Mỗi chặng phải `page.goto()` một lần.
- **`filename` chỉ ghi được vào session lúc MCP khởi động**, không phải session đang chạy.
  Đường file vô dụng khi đổi session — lọc trong Node rồi trả giá trị về.
- Rate-limit: 5 chặng liên tiếp không delay + ~13 navigate/phiên → không vấn đề gì.
- **Bẫy mất dữ liệu im lặng:** xem `playwright-path.md`. Đây là thứ nguy hiểm nhất.

## `browser_network_requests` — bẫy context

Gọi **không** truyền `filter` thì nó xả hàng chục request kèm query string tracking vào
context (~15k token một lần gọi — đắt hơn cả 3 screenshot). Luôn truyền `filter` chặt.
Với filter `search/initial` thì output chỉ 1 dòng, an toàn.

## vietnamairlines.com qua Playwright — đã chạy thông (09/08/2026)

**Trước khi đọc tiếp: nếu chỉ cần giá theo ngày thì không cần chuỗi này.** Xem
`references/vna-date-scan.md` — API nhanh hơn hẳn. Phần dưới giữ lại cho trường hợp cần
tương tác form thật.

Chuỗi đã chạy thông từ đầu đến calendar:

```
navigate → waitForSelector('button.container-region')
→ xoá overlay OneTrust
→ click 'Một chiều'
→ click button.container-region (ô Từ) → fill 'SGN' → click .location:visible đầu tiên
→ (modal 'Đến' TỰ MỞ) → fill 'DAD' → click .location:visible đầu tiên
→ (calendar TỰ MỞ) → đọc .date-picker__wrapper .date-picker__date
```

**Banner cookie — bàn giao cũ ghi sai.** OneTrust **có** xuất hiện ở Playwright. Banner tự
ẩn (`display:none`) nhưng để lại `div.onetrust-pc-dark-filter` chặn mọi click, và
`#onetrust-reject-all-handler` lúc đó không còn click được → mọi `.click()` timeout với
log `subtree intercepts pointer events`. Cách duy nhất chạy được:

```js
document.querySelectorAll('.onetrust-pc-dark-filter, #onetrust-consent-sdk').forEach(e => e.remove());
```

**Chọn kết quả dropdown — không dùng `getByText`.** Text render dính liền
(`Tp. Hồ Chí MinhSGNViệt NamTp. Hồ Chí Minh (SGN)`) nên mọi match theo chuỗi đều trượt.
Dùng `page.locator('.choose-location-modal .location:visible').first().click()`. Sau khi
chọn "Từ" thì có **2** `.choose-location-modal` trong DOM — bắt buộc lọc `:visible`.

**Cấu trúc DOM:**

- Widget trong `#bookingSection`. Ô "Từ"/"Đến" là `button.container-region`, **không phải
  `<input>`** — `querySelectorAll('input')` không thấy gì, dễ tưởng chưa render.
- `document.body.innerText` chỉ ~3.300 ký tự kể cả khi render đủ. Ngắn **không** nghĩa là lỗi.
- Tab `Khứ hồi / Một chiều / Nhiều chặng` là `button._mobileItem_*` trong `#bookingSection`.
- Calendar: `.date-picker__wrapper`, mỗi ô là `.date-picker__date`, `innerText` dạng
  `"23\n\n956Ng"`. Hiện **2 tháng** một lần mở.
- **Đơn vị giá có cả `Ng` (nghìn) lẫn `Tr`** — regex chỉ bắt `Tr` sẽ sót đúng những ngày
  rẻ nhất. Dùng `/\d+[.,]?\d*\s*(Tr|Ng)/`.
- Chân lịch: *"Giá vé một chiều tính bằng VND cho 1 người lớn — Giá mang tính tham khảo và
  có thể thay đổi khi quý khách mua vé."*

**Chưa chạm tới và cũng không cần:** nút "Tìm chuyến bay" (reCAPTCHA Enterprise ở đó).
