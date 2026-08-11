# Kết quả test vietnamairlines.com — 09/08/2026

**Kết luận: GIẢ THUYẾT ĐẠT — và tìm được thứ tốt hơn nhiều.**

---

## 1. Giả thuyết gốc: ĐẠT

Calendar VNA hiển thị giá thấp nhất từng ngày ngay trên ô ngày, **2 tháng một lần mở**,
**không cần bấm "Tìm chuyến bay"**, **không chạm reCAPTCHA**.

Đo được cho SGN→DAD (một chiều, 1 người lớn):

```
Tháng 8 2026:  9→1.6Tr  10→1.6Tr  11→1.2Tr  12→1.2Tr  13→1.3Tr  14→1.3Tr
               15→1.1Tr 16→989Ng  17→1.2Tr  ...  23→956Ng  24→956Ng  25→956Ng
               28→2.2Tr 29→2.3Tr  30→2Tr    31→1.3Tr
Tháng 9 2026:  đủ 30 ngày
```

61 ô ngày, 53 ô có giá (8 ô quá khứ bị disable). Chân lịch ghi rõ:
*"Giá vé một chiều tính bằng VND cho 1 người lớn — Giá mang tính tham khảo và có thể thay
đổi khi quý khách mua vé."*

Lưu ý pattern: có cả đơn vị **`Ng`** (nghìn), không chỉ `Tr`. Regex chỉ bắt `Tr` sẽ sót
đúng những ngày rẻ nhất.

---

## 2. Phát hiện quan trọng hơn: API JSON công khai

Trong lúc calendar load, trang gọi một endpoint **không cần auth, không cần cookie,
không cần referer, không có captcha**:

```
POST https://integration-middleware-website.vietnamairlines.com/api/v1/public/booking/air-best-price
Content-Type: application/json

{
  "route": {
    "originLocationCode": "SGN",
    "destinationLocationCode": "DAD",
    "departureDateTime": "2026-08-09"
  },
  "tripDetails": { "rangeOfDeparture": 62 },
  "location": "VN"
}
```

Trả về:

```json
{"success":true,"code":"0","data":{"prices":[
  {"departureDate":"2026-08-23","price":[{"base":"359000","total":"955181",
   "currencyCode":"VND","totalTaxes":"596181"}]}, ...
]}}
```

**Đã kiểm chứng:**

| Điều kiểm | Kết quả |
|---|---|
| Gọi từ context trắng (không cookie/session/referer) | 200 OK |
| 3 chặng khác nhau (HAN-SGN, SGN-DAD, HAN-DAD) | đều 200, đều đủ ngày |
| `rangeOfDeparture: 62` | 63 ngày |
| `rangeOfDeparture: 90` | 91 ngày |
| `rangeOfDeparture: 180` | **181 ngày trong 1 request** |
| `rangeOfDeparture: 365` | 400 — `INVALID DATA RECEIVED, must be less than or equal...` |

Endpoint phụ, cho khứ hồi: `GET .../api/v1/public/booking/lowest-fare/stay-duration/SGN-DAD`
→ `{"stayDurationMin":2,"stayDurationMax":31}`.

### Đối chiếu độ chính xác

So với `checkpoint_20260805.json` (nguồn Google Flights, thu ngày 05/08):

| Ngày | Google Flights (VN rẻ nhất) | API VNA | |
|---|---|---|---|
| 23/08 | 955.181 (VN 106 / VN 7108) | **955.181** | khớp tuyệt đối |
| 16/08 | 988.181 (VN 106 / VN 7108) | **988.181** | khớp tuyệt đối |
| 21/08 | 1.528.181 (VN 7108) | **1.528.181** | khớp tuyệt đối |
| 14/08 | 1.376.181 (VN 106, khung 05:45–10:30) | 1.225.181 | API thấp hơn — vì API quét **cả ngày**, checkpoint chỉ lấy khung sáng |

Khớp đến từng đồng ở 3/3 ngày so sánh được. Giá VNA và Google Flights là cùng một fare
bucket. Dòng 14/08 không phải mâu thuẫn mà là minh hoạ giới hạn ở mục 3.

---

## 3. Giới hạn — phải nhớ trước khi thiết kế lại

1. **Không có số hiệu chuyến, không có giờ bay.** Chỉ là min-của-ngày. Không lọc được
   theo khung giờ 05:45–10:30 như thiết kế hiện tại.
2. **Chỉ Vietnam Airlines.** Không có VJ / VU / QH.
3. **Một chiều, 1 người lớn, phổ thông.** Khứ hồi = cộng 2 chiều (nội địa VN thì đúng,
   nhưng chưa verify với vé khứ hồi combo).
4. **VNA tự ghi "giá mang tính tham khảo"** — có thể lệch ở bước thanh toán.

⇒ API này **chọn ngày**, không **chọn chuyến**. Nó bổ sung chứ không thay thế
Google Flights / Traveloka.

---

## 4. Phụ lục — sửa lại chỗ ghi sai trong bàn giao

| Bàn giao ghi | Thực tế 09/08 |
|---|---|
| "Banner cookie ở Playwright không xuất hiện" | **Sai.** OneTrust có xuất hiện. Banner tự ẩn nhưng để lại `div.onetrust-pc-dark-filter` chặn mọi click, `#onetrust-reject-all-handler` không click được. Cách xử lý: `document.querySelectorAll('.onetrust-pc-dark-filter, #onetrust-consent-sdk').forEach(e => e.remove())` |
| "Chỗ tắc: click kết quả dropdown — text dính liền nên getByText timeout" | **Đã vượt.** Không cần getByText: `page.locator('.choose-location-modal .location:visible').first().click()` chạy ngay. Sau khi chọn "Từ", modal "Đến" **tự mở**; sau khi chọn "Đến", calendar **tự mở**. |
| `browser_run_code_unsafe` nhận code dạng statement | **Sai.** Phải bọc thành `async () => { ... }` (một expression), nếu không lỗi `SyntaxError: Unexpected token 'const'`. |
| — | `waitForTimeout` dài (12s) trong 1 lượt run_code → MCP request timeout, **page bị reset về `about:blank`**, mất hết state. Chia nhỏ, dùng `waitForSelector`. |
| — | `newContext()` gọi API bị `unable to verify the first certificate` → cần `{ ignoreHTTPSErrors: true }`. |

Chuỗi thao tác đã chạy thông từ đầu đến cuối:

```
navigate → waitForSelector('button.container-region')
→ xoá overlay OneTrust
→ click 'Một chiều'
→ click button.container-region (ô Từ) → fill 'SGN' → click .location:visible đầu tiên
→ (modal Đến tự mở) → fill 'DAD' → click .location:visible đầu tiên
→ (calendar tự mở) → đọc .date-picker__wrapper .date-picker__date
```

Nhưng nếu dùng API ở mục 2 thì **không cần chuỗi này nữa**.
