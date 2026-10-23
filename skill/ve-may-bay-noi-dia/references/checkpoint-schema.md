# Checkpoint JSON

Ghi sau **mỗi chặng one-way**, không đợi hết cặp. Nếu phiên đứt, chạy tiếp từ chặng cuối đã ghi.

```json
{
  "meta": {
    "chang": "SGN-DAD",
    "thu_thap": "2026-08-02 14:30 (giờ VN)",
    "khung_di": "06:00-10:00",
    "khung_ve": "17:00-22:00",
    "nguon": ["Google Flights", "Traveloka"],
    "khach": "1 người lớn",
    "hang_ve": "Phổ thông",
    "loai": "Chỉ bay thẳng"
  },
  "caps": [
    {
      "id": 1,
      "ten": "Cặp 1",
      "ngay_di": "06/08/2026",
      "ngay_ve": "10/08/2026",
      "thu": "Năm → Hai",
      "di": {
        "link": { "Google Flights": "https://…", "Traveloka": "https://…" },
        "thu_thap": { "Google Flights": "02/08/2026 14:05 (giờ VN)", "Traveloka": "02/08/2026 14:31 (giờ VN)" },
        "chuyen": [
          { "sh": "VN 104", "hang": "Vietnam Airlines", "dep": "06:30", "arr": "07:50",
            "gia": { "Google Flights": 2100181, "Traveloka": 2079179 },
            "link_chuyen": "https://www.google.com/travel/flights/booking?tfs=…",
            "mua": { "url": "https://www.google.com/travel/flights/booking?tfs=…",
                     "luc": "02/08/2026 14:50 (giờ VN)", "trang_thai": "OK", "ly_do": "",
                     "chuyen": "…", "hanh_ly": ["Miễn phí kiện hành lý ký gửi đầu tiên"],
                     "ban": [ { "nguoi_ban": "Vietnam Airlines", "loai": "Hãng hàng không",
                                "gia": 2100181, "ghi_chu": "" } ] } }
        ]
      },
      "ve": { "link": {}, "thu_thap": {}, "chuyen": [] }
    }
  ],
  "de_xuat": [
    { "ngay": "2026-08-06", "tu": "SGN", "den": "DAD", "sh": "VN 104", "dep": "06:30",
      "hang": "Vietnam Airlines", "url": "https://www.google.com/travel/flights/booking?tfs=…",
      "chieu": "di", "cap": ["Cặp 1"], "ly_do": ["Rẻ nhất", "Top 3 rẻ nhất chiều"] }
  ],
  "log": [
    { "thoi_diem": "…", "cap": "Cặp 1", "nguon": "Traveloka",
      "trang_thai": "Không khả dụng", "ly_do": "…", "ghi_chu": "…" }
  ]
}
```

**Quy ước**

- `gia` thiếu key của một nguồn = nguồn đó không có giá cho chuyến này → ô ghi `Không khả dụng`. Bắt buộc có dòng `log` giải thích.
- `sh` để `""` nếu nguồn không cho số hiệu chuyến.
- `dep` / `arr` dạng `"HH:MM"` 24h.
- Thứ tự nguồn trong `meta.nguon` chính là **thứ tự ưu tiên** của công thức `Giá chốt`.
- `trang_thai` ∈ `OK` | `Không khả dụng` | `Lỗi`.
- `thu_thap` theo chặng = giờ quét của từng nguồn cho đúng ngày bay đó. Thiếu thì workbook dùng `meta.thu_thap`.
- `link_chuyen` = link trang đặt vé Google Flights của đúng chuyến, `""` nếu chưa có số hiệu.
- `mua` chỉ có ở chuyến đã chạy bước xác nhận nơi mua (`references/gf-booking.md`). `ban` = người bán trên trang đặt vé, `loai` ∈ `Hãng hàng không` | `Đại lý`.
- `de_xuat` = danh sách chuyến cần xác nhận nơi mua (Block C + top 3 mỗi chiều), mỗi chuyến một lần dù thuộc nhiều cặp. Sheet Mua vé dựng theo danh sách này.
