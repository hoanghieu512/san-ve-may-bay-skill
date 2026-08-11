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
        "chuyen": [
          { "sh": "VN 104", "hang": "Vietnam Airlines", "dep": "06:30", "arr": "07:50",
            "gia": { "Google Flights": 2100181, "Traveloka": 2079179 } }
        ]
      },
      "ve": { "link": {}, "chuyen": [] }
    }
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
