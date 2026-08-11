# Ghép nguồn — `scripts/merge_sources.py`

Mắt xích giữa **extract** và **build**: biến JSON thô của từng nguồn thành một
checkpoint đúng schema (`checkpoint-schema.md`).

```bash
python3 scripts/merge_sources.py job.json checkpoint.json
```

Đường dẫn file thô trong `job.json` được hiểu **tương đối so với chính `job.json`**.

## Khoá ghép

`(giờ khởi hành, hãng đã chuẩn hoá)`. Không dùng số hiệu chuyến vì Google Flights
không cấp số hiệu khi chưa bung từng dòng — bung hết là tốn gấp nhiều lần.

Khoá này **không hoàn hảo và đã gãy thật**: 09/08/2026 Traveloka trả VU 685 ở hai
khung giờ khác nhau trong khi Google Flights chỉ có một. Script không tự đoán —
gặp nhiều dòng cùng khoá trong một nguồn thì giữ giá thấp nhất (Traveloka liệt kê
nhiều hạng vé rời nhau cho cùng một chuyến, xem `site-quirks.md`) và ghi một dòng
`Log` mức `Lỗi` cho người đọc tự xử.

## `job.json`

```json
{
  "meta": { "chang": "SGN ⇄ DAD", "khung_di": "05:45–10:30", "khung_ve": "15:45–20:30",
            "khach": "1 người lớn", "hang_ve": "Phổ thông", "loai": "Chỉ bay thẳng" },
  "nguon": ["Google Flights", "Traveloka"],
  "san_bay": { "di": ["SGN", "DAD"], "ve": ["DAD", "SGN"] },
  "raw": {
    "Google Flights": { "di": "gf_di_raw.json", "ve": "gf_ve_raw.json",
                        "cot": ["dep", "arr", "hang", "gia"] },
    "Traveloka":      { "file": "tvl_raw.json",
                        "cot": ["sh", "dep", "arr", "hang", "gia"] }
  },
  "loai_hang": ["Vietravel Airlines"],
  "hang_alias": { "VJ Air": "Vietjet" },
  "caps": [
    { "id": 1, "ngay_di": "14/08/2026", "ngay_ve": "17/08/2026", "thu": "Thứ 6 → Thứ 2" }
  ],
  "log_them": [
    { "cap": "(toàn bộ)", "nguon": "Google Flights", "trang_thai": "OK",
      "ly_do": "…", "ghi_chu": "…" }
  ]
}
```

| Khoá | Bắt buộc | Ghi chú |
|---|---|---|
| `meta` | ✅ | Chép thẳng vào `meta` của checkpoint; `thu_thap` và `nguon` script tự điền |
| `nguon` | ✅ | **Thứ tự = thứ tự ưu tiên** của `Giá chốt` trong workbook |
| `san_bay` | ✅ | Dùng để dựng link nguồn cho từng chiều |
| `raw` | ✅ | `{"di":…, "ve":…}` nếu mỗi chiều một file; `{"file":…}` nếu một file chứa cả hai. `cot` là tên cột theo đúng thứ tự trong mảng thô |
| `caps` | ✅ | `ten` mặc định `"Cặp <id>"`, `thu` để trống được |
| `loai_hang` | | Loại hãng ở **mọi** nguồn trước khi tính. Nhớ ghi lý do vào `log_them` |
| `hang_alias` | | Bổ sung bảng chuẩn hoá tên hãng dựng sẵn trong script |
| `log_them` | | Các dòng `Log` viết tay (verify hãng, calibrate, quyết định của người dùng). `thoi_diem` tự điền |
| `thu_thap` | | Ghi đè timestamp — dùng khi dựng lại checkpoint cũ |

Định dạng thô mỗi nguồn là `{ "YYYY-MM-DD": [[…], […]] }`, mỗi mảng con là một
chuyến, thứ tự phần tử khớp `cot`. Đây đúng là thứ các extractor trong `scripts/`
trả về.

## Log tự sinh

Không cần viết tay, script tự thêm:

- **Chuyến thiếu ở một nguồn** → `Không khả dụng`, kèm chiều / số hiệu / giờ / hãng.
- **Hai nguồn lệch ≥10%** → `Lỗi`, kèm giá từng nguồn.
- **Lệch ≥25%** → cùng dòng đó nhưng gắn tiền tố `CẦN ĐIỀU TRA —`, và script in
  cảnh báo ra stderr. Xem SKILL.md §6: đây là ngưỡng **bắt buộc điều tra**, không
  phải gợi ý.
- **Nhiều dòng cùng khoá trong một nguồn** → `Lỗi`, ghi rõ giữ số nào bỏ số nào.

Các dòng `log_them` luôn nằm trước log tự sinh.

## Nguyên tắc

Script **không bao giờ sửa hay bỏ một mức giá nào**. Giá lạ thì ghi kèm dòng `Log`,
để người đọc quyết định — đúng §1 của SKILL.md. Đừng sửa script theo hướng "lọc
outlier cho bảng đẹp".
