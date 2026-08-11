# Quét ngày bằng API VNA — chọn cặp ngày trước khi quét chuyến

Kiểm chứng 09/08/2026. Đây là **Bước 0** (SKILL.md §3): chạy trước khi ước lượng ngân sách
(§4), để biết cặp ngày nào đáng quét thay vì đoán.

## Endpoint

```
POST https://integration-middleware-website.vietnamairlines.com/api/v1/public/booking/air-best-price
Content-Type: application/json

{
  "route": {
    "originLocationCode": "SGN",
    "destinationLocationCode": "DAD",
    "departureDateTime": "2026-08-09"
  },
  "tripDetails": { "rangeOfDeparture": 180 },
  "location": "VN"
}
```

Response:

```json
{"success": true, "code": "0", "data": {"prices": [
  {"departureDate": "2026-08-23",
   "price": [{"base": "359000", "total": "955181",
              "currencyCode": "VND", "totalTaxes": "596181"}]}
]}}
```

**Dùng `total`** — đã gồm thuế + phí, cùng cơ sở với Google Flights / Traveloka.
`base` là giá vé trần, đừng dùng để so sánh.

`prices` **không sắp xếp theo ngày** (server trả theo giá tăng dần). Phải tự sort.

## Đã kiểm chứng

| Điều kiểm | Kết quả |
|---|---|
| Không cookie / session / referer / auth | 200 OK |
| Nhiều chặng (HAN-SGN, SGN-DAD, HAN-DAD) | đều 200, đều đủ ngày |
| `rangeOfDeparture: 62 / 90 / 180` | trả 63 / 91 / **181** ngày |
| `rangeOfDeparture: 365` | 400 `INVALID DATA RECEIVED` — trần ở đâu đó ≤ 180 |
| Không có reCAPTCHA ở đường này | đúng — không đụng tới nút "Tìm chuyến bay" |

**Độ chính xác** — đối chiếu với dữ liệu Google Flights thu ngày 05/08 cho SGN-DAD:

| Ngày | Google Flights (VN rẻ nhất) | API VNA |
|---|---|---|
| 23/08 | 955.181 | **955.181** |
| 16/08 | 988.181 | **988.181** |
| 21/08 | 1.528.181 | **1.528.181** |

Khớp đến từng đồng ở 3/3 ngày so được. Cùng một fare bucket.

Endpoint phụ cho khứ hồi:
`GET .../api/v1/public/booking/lowest-fare/stay-duration/SGN-DAD`
→ `{"stayDurationMin": 2, "stayDurationMax": 31}` — độ dài lưu trú VNA cho phép.

## Giới hạn — nói rõ với người dùng, đừng để họ hiểu nhầm

1. **Không có số hiệu chuyến, không có giờ bay.** Chỉ là min-của-cả-ngày. **Không lọc được
   theo khung giờ.** Nếu người dùng đã chốt khung giờ sáng, con số này có thể thuộc chuyến
   đêm — dùng để *xếp hạng ngày*, không dùng làm giá dự kiến.
2. **Chỉ Vietnam Airlines.** Không có VJ / VU / QH / Bamboo. Ngày VNA rẻ chưa chắc là ngày
   rẻ nhất toàn thị trường, nhưng thực nghiệm cho thấy các hãng biến động khá cùng pha.
3. **Một chiều, 1 người lớn, phổ thông.** Khứ hồi = cộng 2 chiều.
4. VNA tự ghi *"giá mang tính tham khảo và có thể thay đổi khi quý khách mua vé"*.

⇒ Đây là công cụ **chọn ngày**, không phải nguồn giá. **KHÔNG đưa vào `meta.nguon`,
KHÔNG thêm cột vào workbook** — đặt cạnh cột giá theo chuyến là so sai đơn vị.
Kết quả quét ngày ghi vào `Log` như một dòng ghi chú, thế là đủ.

## Cách dùng

`scripts/vna_date_scan.js` — dán vào `mcp__playwright__browser_run_code_unsafe`, sửa
`ROUTE` / `START` / `RANGE` / `STAYS` ở đầu. Một call lấy cả hai chiều và ghép sẵn cặp
đi/về theo các độ dài lưu trú cần xét.

Bắt buộc `newContext({ ignoreHTTPSErrors: true })` — nếu không sẽ lỗi
`unable to verify the first certificate`.

Trình bày kết quả cho người dùng bằng **AskUserQuestion**: đưa 2-3 nhóm cặp ngày
(rẻ nhất / cuối tuần / linh hoạt) kèm giá tham chiếu VNA, để họ chốt quét cặp nào.
