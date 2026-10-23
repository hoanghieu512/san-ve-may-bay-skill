# Xác nhận nơi mua: trang đặt vé Google Flights

Bước bắt buộc giữa merge và build (SKILL.md §6). Mọi điều dưới đây đã chạy thật ngày 23/10/2026 bằng Playwright, context trắng, không cookie, chặng SGN-DAD ngày 14/11/2026.

## Vì sao cần

Link trang tìm kiếm không cho biết mua ở đâu, và giá ở danh sách Google Flights chưa chắc là giá mua thấp nhất:

| Chuyến | Giá ở danh sách GF | Trang đặt vé của chính chuyến đó |
|---|---|---|
| VJ 632 20:10 | 742.061 ₫ | Vietjet (hãng) 742.061 ₫, gồm phí tiện lợi 100.000 ₫ · **Jettzy (đại lý) 679.301 ₫** |
| 9G 954 05:50 | 906.181 ₫ | Sun PhuQuoc Airways (hãng) 906.181 ₫ |
| VN 6030 05:45 | 1.127.181 ₫ | Vietnam Airlines (hãng) 1.127.181 ₫, do Pacific Airlines khai thác |

Giá ở danh sách thường là giá của hãng. Đại lý có thể rẻ hơn (ở đây 8,5%) hoặc không có mặt.

## Link trang đặt vé của một chuyến

```
https://www.google.com/travel/flights/booking?tfs=<protobuf base64url>&hl=vi&gl=VN&curr=VND
```

`merge_sources.py` dựng sẵn link này cho mọi chuyến có số hiệu (`link_chuyen` trong checkpoint), từ 5 thứ: ngày, sân bay đi, sân bay đến, mã hãng, số hiệu. Hàm `gf_booking_url()` dựng lại **đúng từng byte** link bắt được khi bấm vào chuyến trên trang thật (có test ở `tests/test_scripts.py`).

- Kiểm chứng: dựng link cho VJ 632, 9G 954, VN 6030 rồi mở ở context trắng, cả 3 ra đúng chuyến kèm danh sách người bán.
- Link bấm từ danh sách có thêm `tfu=...` (token phiên). **Bỏ `tfu` vẫn chạy**, đã thử.
- Link cố định 1 người lớn, phổ thông, một chiều, bay thẳng. Người dùng muốn đổi số khách thì đổi trên trang.
- Đổi ngày trong link (VJ 632 ngày 15/11) vẫn ra đúng chuyến của ngày đó.

## Trang hiển thị gì

Đọc bằng `document.body.innerText`, hai khối:

```
Các chuyến bay bạn đã chọn
Theo dõi giá
Thứ 7, 14 thg 11
20:10
 – 
21:30
Vietjet
1 giờ 20 phút
SGN–DAD
Bay thẳng
...
Miễn phí 1 kiện hành lý xách tay
Có tính phí kiện hành lý ký gửi đầu tiên
...
Tùy chọn đặt vé
Cách xếp hạng các lựa chọn
Đặt vé của VietjetHãng hàng không
Bao gồm phí tiện lợi 100.000 ₫
742.061 ₫
Tiếp tục
Tùy chọn xem
Đặt vé của Jettzy
679.301 ₫
Tiếp tục
Tùy chọn xem
Giá bao gồm các loại phí và thuế bắt buộc cho 1 người lớn. ...
```

- Người bán là hãng: tên dính liền chữ `Hãng hàng không`. Không có chữ đó = đại lý.
- Dòng giữa tên và giá là ghi chú phí (vd phí tiện lợi). Giá đã gồm thuế phí bắt buộc cho 1 người lớn, theo đúng chân khối.
- Hành lý đọc ở khối chuyến đã chọn. VNA và 9G ghi "Miễn phí kiện hành lý ký gửi đầu tiên", Vietjet ghi "Có tính phí": hai giá ngang nhau chưa chắc ngang giá trị.
- Bấm "Tiếp tục" ở dòng hãng (chỉ thử một lần khi dò) mở `vietjetair.com` với chặng + ngày + số khách điền sẵn. **Skill không bấm**: link trong file để người dùng tự bấm.

## `scripts/gf_booking.js`

Dán `FLIGHTS` do `merge_sources.py job.json checkpoint.json --de-xuat` in ra, chạy qua `browser_run_code_unsafe`. Trả về chuỗi JSON:

```json
{"ket_qua": [
  {"url": "...", "sh": "VJ 632", "dep": "20:10", "ngay": "2026-11-14", "tu": "SGN", "den": "DAD",
   "luc": "23/10/2026 11:22 (giờ VN)", "trang_thai": "OK", "ly_do": "",
   "chuyen": "Thứ 7, 14 thg 11 | 20:10 | – | 21:30 | Vietjet | 1 giờ 20 phút | SGN–DAD",
   "hanh_ly": ["Miễn phí 1 kiện hành lý xách tay", "Có tính phí kiện hành lý ký gửi đầu tiên"],
   "ban": [{"nguoi_ban": "Vietjet", "loai": "Hãng hàng không", "gia": 742061,
            "ghi_chu": "Bao gồm phí tiện lợi 100.000 ₫"},
           {"nguoi_ban": "Jettzy", "loai": "Đại lý", "gia": 679301, "ghi_chu": ""}]}
 ],
 "con_lai": [], "dung": ""}
```

Lưu **nguyên văn** ra `gf_booking_raw.json` trong thư mục run, rồi khai báo ở `job.json` khoá `xac_nhan`. Merge chấp nhận cả object lẫn chuỗi JSON nguyên văn.

| `trang_thai` | Khi nào | Merge làm gì |
|---|---|---|
| `OK` | Đọc được người bán, giờ đi khớp | Gắn vào chuyến, lên sheet Mua vé |
| `Không khả dụng` | Google báo "hành trình trước đây bạn chọn bây giờ không còn nữa": hết bán, hết chỗ, hoặc sai số hiệu | Log + dòng đỏ ở Mua vé |
| `Lỗi` | Trang không nạp trong 15s, giờ đi không khớp, hoặc không đọc được người bán nào (nghi Google đổi giao diện) | Log + dòng đỏ ở Mua vé |

`dung` khác rỗng = gặp captcha hoặc trang consent: script dừng ngay, các chuyến chưa làm nằm trong `con_lai`. Báo người dùng, chờ (SKILL.md §1.5).

**Sanity check có sẵn trong script**, đừng bỏ: giờ đi phải xuất hiện trong khối chuyến đã chọn (bắt link dựng sai chuyến), phải có ít nhất một người bán, người bán nào cũng phải có giá. Thiếu check này thì Google đổi giao diện sẽ cho ra 0 người bán mà không ai biết.

## Thời gian

Mỗi trang nạp 1–2,5 giây (đo 23/10/2026). `BUDGET_MS = 25000` dừng trước trần thời gian của một MCP request (xem `playwright-path.md`: một call quá dài bị reset về `about:blank`), nên mỗi call làm được khoảng 8 chuyến. Phần chưa làm trả về trong `con_lai`: gọi lại với `FLIGHTS = con_lai`, lưu file kết quả thứ hai, khai báo cả hai file trong `xac_nhan` (file sau đè file trước nếu trùng chuyến).

## Không có Playwright

Claude in Chrome không chạy được vòng lặp qua nhiều trang trong một lần gọi JS (navigate là mất script). Với từng chuyến: `navigate` tới `url`, `get_page_text`, đọc khối "Tùy chọn đặt vé", rồi tự ghi một phần tử `ket_qua` đúng định dạng trên (giữ `url`, `sh`, `dep`, `ngay`, `tu`, `den` từ `FLIGHTS`, điền `luc` giờ VN). Khoảng 2 thao tác mỗi chuyến.

## Không làm

- Không bấm "Tiếp tục", không mở link chuyển hướng tới người bán, không đăng nhập.
- Không lọc bỏ đại lý lạ, không sửa giá. Ghi đủ, gắn nhãn `Đại lý`, để người dùng quyết.
- Không dùng giá ở trang đặt vé để sửa cột giá Google Flights ở sheet Data: Data là ảnh chụp lúc quét, Mua vé là lúc xác nhận. Merge tự ghi Log khi giá hãng đổi giữa hai lần.
