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

## Chế độ gọn (`GON = true`, mặc định): dùng khi nhiều chuyến

Playwright **không ghi được file** (không có `fs`, `filename` vô dụng khi đổi phiên, xem `playwright-path.md`), nên kết quả bắt buộc đi qua context rồi mình chép ra file. Với 67 chuyến thì JSON nguyên văn là 75 KB, mà chép tay từng chuyến x từng người bán thì sai sót là chuyện chắc chắn xảy ra: ngày 01/11/2026 đã phải sửa script giữa lúc chạy để lấy dạng gọn. Giờ dạng gọn nằm sẵn trong script, đã test.

`GON = true` trả về text nhiều dòng, **bỏ đúng một trường: `url`**, vì `gf_booking_gon.py` dựng lại được từ `link_chuyen` trong checkpoint (chính là link merge đã dựng để in ra `FLIGHTS`, nên khớp từng byte). Mọi thứ khác đi qua nguyên văn, kể cả `chuyen` và ghi chú phí: đó là bằng chứng link mở đúng chuyến và giá gồm những gì, đừng cắt để tiết kiệm token. Đo trên run 67 chuyến ngày 01/11/2026: **75.404 → 32.003 byte, giảm 58%**.

```
# GON<TAB>1<TAB>2 chuyen
F<TAB>2026-11-14<TAB>SGN<TAB>DAD<TAB>VJ 632<TAB>20:10<TAB>14/11/2026 11:22 (giờ VN)<TAB>OK<TAB><TAB>Thứ 7, 14 thg 11 | 20:10 | – | 21:30 | Vietjet
H<TAB>Miễn phí 1 kiện hành lý xách tay ;; Có tính phí kiện hành lý ký gửi đầu tiên
B<TAB>Vietjet<TAB>H<TAB>742061<TAB>Bao gồm phí tiện lợi 100.000 ₫
B<TAB>Jettzy<TAB>D<TAB>679301<TAB>
F<TAB>2026-11-14<TAB>SGN<TAB>DAD<TAB>VN 2<TAB>08:00<TAB>14/11/2026 11:22 (giờ VN)<TAB>Không khả dụng<TAB>Google Flights báo hành trình không còn (hết chỗ, hết bán, hoặc sai số hiệu)<TAB>
# CON_LAI<TAB>(het)
# DUNG<TAB>(khong)
```

Phân cách là **tab**, mọi tab/xuống dòng trong nội dung bị đổi thành khoảng trắng trước khi ghi.

| Dòng | Cột |
|---|---|
| `F` | ngày (ISO), từ, đến, số hiệu, giờ đi, thời điểm đọc, trạng thái, lý do, khối chuyến đã chọn |
| `H` | hành lý, nhiều mục nối bằng ` ;; ` (không có dòng này = không đọc được mục hành lý nào) |
| `B` | người bán, `H` (hãng) hay `D` (đại lý), giá (rỗng = không đọc được giá), ghi chú phí |
| `# CON_LAI` | **chỉ số** trong `FLIGHTS` vừa dán, hoặc `(het)`. Không trả url: danh sách đang nằm ngay trong call, gọi lại với `FLIGHTS.slice(<số đầu>)` |
| `# DUNG` | lý do bị chặn, hoặc `(khong)` |

Mỗi `H` và `B` thuộc về dòng `F` ngay trên nó.

Các bước:

```bash
# 1. lưu nguyên văn chuỗi script trả về ra gf_booking_gon.txt (ĐỪNG đặt tên .json)
# 2. dựng ra file raw đúng schema
python3 scripts/gf_booking_gon.py gf_booking_gon.txt checkpoint.json gf_booking_raw.json
# 3. khai báo gf_booking_raw.json ở job.json "xac_nhan", chạy lại merge
```

**Giữ cả hai file trong thư mục run**: `gf_booking_gon.txt` là thứ script thật trả về, `gf_booking_raw.json` là thứ đã qua một bước xử lý. §8 đòi raw để dựng lại được workbook mà không quét lại.

Dòng `F` nào không tìm được trong checkpoint thì `gf_booking_gon.py` **thoát mã 1 và không ghi file**, kèm danh sách chuyến thiếu. Sai số hiệu hay sai ngày mà bỏ qua im lặng thì chuyến đó mất khỏi sheet Mua vé và không ai biết. Khai báo thẳng file `# GON` vào `xac_nhan` cũng bị merge chặn với thông báo chỉ đúng lệnh cần chạy.

Cần JSON nguyên văn (ít chuyến, hoặc muốn bỏ hẳn bước chuyển): đặt `GON = false`, lưu ra `gf_booking_raw.json`, khai báo luôn. Hai đường cho ra **cùng `ket_qua` và `dung`**, tức là mọi thứ merge đọc: `tests/gf_booking_offline.js` + `tests/test_scripts.py` chạy cùng một bộ chuyến hai lần rồi so từng khoá. Đã đối chiếu thêm trên dữ liệu thật của run 01/11/2026 (4 file, 67 chuyến, 335 dòng người bán): dựng dạng gọn từ raw rồi chuyển về, `ket_qua` khớp từng khoá cả 4 file, kể cả 67/67 link.

Khác duy nhất là `con_lai`: đường JSON giữ nguyên các object (có url), đường gọn chỉ còn chỉ số ở `_con_lai_chi_so`. Merge không đọc `con_lai`, nên workbook không đổi; nhưng đọc file gọn về sau thì **không suy ra được chuyến nào còn treo**: chỉ số chỉ có nghĩa cùng với `FLIGHTS` của đúng call đó. Chuyến còn treo nằm ở file xác nhận lượt sau, nên dấu vết không mất, chỉ không nằm trong một file.

| `trang_thai` | Khi nào | Merge làm gì |
|---|---|---|
| `OK` | Đọc được người bán, giờ đi khớp | Gắn vào chuyến, lên sheet Mua vé |
| `Không khả dụng` | Google báo "hành trình trước đây bạn chọn bây giờ không còn nữa": hết bán, hết chỗ, hoặc sai số hiệu | Log + dòng đỏ ở Mua vé |
| `Lỗi` | Không mở được trang (lỗi mạng), trang không nạp trong 15s, giờ đi không khớp, hoặc không đọc được người bán nào (nghi Google đổi giao diện) | Log + dòng đỏ ở Mua vé |

`dung` khác rỗng = gặp captcha hoặc trang consent: script dừng ngay. Chuyến đang mở lúc bị chặn và mọi chuyến sau nó nằm trong `con_lai`, để lần chạy lại (khi hết bị chặn) thử lại đủ. Báo người dùng, chờ (SKILL.md §1.5).

**Sanity check có sẵn trong script**, đừng bỏ: giờ đi phải xuất hiện trong khối chuyến đã chọn (bắt link dựng sai chuyến), phải có ít nhất một người bán, người bán nào cũng phải có giá. Thiếu check này thì Google đổi giao diện sẽ cho ra 0 người bán mà không ai biết.

## Thời gian

Mỗi trang nạp 1–2,5 giây (đo 23/10/2026). `BUDGET_MS = 25000` dừng trước trần thời gian của một MCP request (xem `playwright-path.md`: một call quá dài bị reset về `about:blank`), nên mỗi call làm được khoảng 8 chuyến. Ngân sách tính cho **cả chuyến**, không chỉ lúc bắt đầu: mỗi bước chờ bị cắt theo phần ngân sách còn lại, chuyến bị cắt ngang không ghi `Lỗi` mà chuyển vào `con_lai`. Phần chưa làm trả về trong `con_lai`: gọi lại với phần đó (`GON = false` trả về nguyên các object, dán thẳng làm `FLIGHTS`; `GON = true` trả về chỉ số, dùng `FLIGHTS.slice(<số đầu>)`), lưu file kết quả thứ hai, khai báo cả hai file trong `xac_nhan` theo thứ tự chạy. Chuyến có nhiều kết quả thì merge lấy kết quả `OK` mới nhất, nên một lượt chạy lại bị lỗi không xoá mất kết quả tốt đã có.

## Không có Playwright

Claude in Chrome không chạy được vòng lặp qua nhiều trang trong một lần gọi JS (navigate là mất script). Với từng chuyến: `navigate` tới `url`, `get_page_text`, đọc khối "Tùy chọn đặt vé", rồi tự ghi một phần tử `ket_qua` đúng định dạng trên (giữ `url`, `sh`, `dep`, `ngay`, `tu`, `den` từ `FLIGHTS`, điền `luc` giờ VN). Khoảng 2 thao tác mỗi chuyến.

## Không làm

- Không bấm "Tiếp tục", không mở link chuyển hướng tới người bán, không đăng nhập.
- Không lọc bỏ đại lý lạ, không sửa giá. Ghi đủ, gắn nhãn `Đại lý`, để người dùng quyết.
- Không dùng giá ở trang đặt vé để sửa cột giá Google Flights ở sheet Data: Data là ảnh chụp lúc quét, Mua vé là lúc xác nhận. Merge tự ghi Log khi giá hãng đổi giữa hai lần.
