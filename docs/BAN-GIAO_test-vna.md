> **⚠️ ĐÃ XONG — 09/08/2026. Giữ lại để tra cứu lịch sử.**
>
> Test đã chạy. Kết quả tốt hơn giả thuyết trong file này: VNA có **API công khai
> `air-best-price`**, không cần auth, không captcha, không phải đụng tới form hay calendar.
> Xem `skill-src/references/vna-date-scan.md` và `skill-src/scripts/vna_date_scan.js`.
>
> Giới hạn đã xác nhận: API chỉ cho giá **theo ngày**, không có số hiệu chuyến và giờ bay
> — nên nó dùng để *chọn cặp ngày*, không thay được nguồn giá theo chuyến.

---

# Bàn giao — test vietnamairlines.com qua Playwright

Đọc file này ở session Cowork mới. Playwright MCP đã cài xong và hoạt động.

## Mục tiêu

Kiểm chứng **một giả thuyết duy nhất**, không phải "tự động hoá VNA nói chung":

> Calendar của vietnamairlines.com hiển thị giá thấp nhất của **từng ngày** ngay trên ô
> ngày (dạng `2.4Tr`, `2.6Tr`). Nếu đúng, một lần mở lịch cho giá **cả tháng** — với 8 cặp
> ngày thì VNA tốn **2 lượt** thay vì 16, và **không cần bấm "Tìm chuyến bay"** nên không
> chạm reCAPTCHA.

Cơ sở: quan sát được khi dò bằng Claude in Chrome ngày 02/08/2026, chưa xác minh lại.

**Giới hạn đã biết trước:** giá trên lịch là giá thấp nhất *trong ngày*, không gắn với
chuyến cụ thể → **không lọc được theo khung giờ**. Nếu đúng vậy, nó bổ sung cho việc chọn
ngày chứ không thay thế việc quét từng chuyến. Cân nhắc điều này trước khi đầu tư thêm.

## Trạng thái đã dò được (09/08/2026) — đừng làm lại

**VNA không chặn Playwright.** Trang render đủ. reCAPTCHA Enterprise có mặt dạng invisible
(`iframe[src*="recaptcha"]`) nhưng chưa kích hoạt ở bước duyệt.

**Cấu trúc DOM:**

- Widget nằm trong `#bookingSection`.
- Ô "Từ" / "Đến" là `button.container-region`, **không phải `<input>`**. Query
  `document.querySelectorAll('input')` không thấy gì → dễ tưởng nhầm widget chưa render.
  Kiểm tra bằng text `Khứ hồi|Một chiều|Từ|Đến` thay vì bằng input.
- `document.body.innerText` chỉ ~3.000 ký tự kể cả khi widget đã render đầy đủ. Độ dài
  ngắn **không** có nghĩa là trang lỗi.
- Click ô "Từ" mở `.choose-location-modal`. Bên trong có đúng một `<input>`
  (placeholder "Tìm kiếm").
- `page.locator('.choose-location-modal input').first().fill('SGN')` **chạy tốt** — ra
  kết quả đúng.
- Kết quả gợi ý là các `div.location` (một số có class `active`), nằm trong
  `.choose-location` / `.default-regions`.

**Chỗ tắc duy nhất:** click chọn kết quả trong dropdown. Text render **dính liền không có
khoảng trắng**:

```
Tp. Hồ Chí MinhSGNViệt NamTp. Hồ Chí Minh (SGN)
```

nên `getByText('Tp. Hồ Chí Minh (SGN)')` timeout. Thử tiếp theo: click theo
`.choose-location-modal .location` + index, hoặc `getByText(/SGN/)` với regex, hoặc
`page.keyboard.press('Enter')` sau khi fill.

**Chưa chạm tới:** tab "Một chiều" (nằm ngoài modal, trong `#notMultipleTrip` /
`.tab-content`), calendar, nút "Tìm chuyến bay".

## Đã loại trừ — đừng thử lại

- `getByText` với chuỗi có dấu ngoặc → trượt vì text dính liền.
- Tìm form bằng `querySelectorAll('input,select')` → chỉ ra ô tìm kiếm site, select ngôn
  ngữ và ô email newsletter. Không phải widget đặt vé.
- Banner cookie: ở Playwright **không xuất hiện** (đã thử `Từ chối tất cả` / `Reject all`
  → không tìm thấy). Khác với Chrome thật.

## Quy trình gợi ý

1. `browser_navigate` → `https://www.vietnamairlines.com/vn/vi/home`, đợi ~12 giây.
2. Click ô "Từ" (`button.container-region` chứa `HAN`).
3. Trong `.choose-location-modal`: chọn tab **"Một chiều"** trước, rồi fill `SGN`, chọn
   kết quả (thử các cách ở trên).
4. Lặp cho ô "Đến" với `DAD`.
5. Mở ô ngày → **đây là bước quyết định**: đọc xem lịch có giá từng ngày không.
   Dump text của container lịch, tìm pattern `\d+[.,]\d\s*Tr`.
6. **KHÔNG bấm "Tìm chuyến bay"** trừ khi bước 5 thất bại và cần xác minh thêm. Nếu bấm
   và gặp captcha → dừng, báo người dùng, không tự giải.

Dùng `browser_run_code_unsafe` để gộp nhiều bước trong một lượt và log từng bước
OK/FAIL — cách này đã hiệu quả, thấy ngay chỗ hỏng.

## Nếu ĐẠT

Sửa `ve-may-bay-noi-dia`:
- `references/site-quirks.md`: thay mục "vietnamairlines.com — dò dở dang" bằng quy trình
  hoàn chỉnh.
- `SKILL.md` §6: web hãng không còn "mặc định TẮT" cho VNA; ghi rõ calendar cho giá
  theo ngày (không theo chuyến).
- Cân nhắc thêm cột nguồn "Web hãng (VNA)" vào `build_workbook.py` — công thức `Giá chốt`
  đã ưu tiên cột đầu tiên nên chỉ cần đưa nó lên đầu `meta.nguon`.

## Nếu KHÔNG ĐẠT

Ghi kết quả vào `references/site-quirks.md` để lần sau không ai thử lại. Giữ nguyên
thiết kế 2 nguồn.

## Trạng thái skill hiện tại

- `ve-may-bay-noi-dia.skill` trong outputs — đã có đường Playwright, sanity check bắt
  buộc, và mục Playwright trong site-quirks. Cài đè bản cũ nếu chưa.
- Bẫy quan trọng nhất đã ghi trong `references/playwright-path.md`: phải
  `await response.json()` **trước** khi navigate sang chặng kế, nếu không dữ liệu thiếu
  im lặng (đo được: 126 → 18 phần tử, một ngày ra 0 chuyến mà không báo lỗi).
- `SGN-DAD_KhuHoi_T8-2026_20260805-2330.xlsx` — kết quả 8 cặp ngày 14/08–30/08, đã verify.
