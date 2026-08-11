> **⚠️ LƯU TRỮ — 11/08/2026.** Repo đã sắp xếp lại, đường dẫn trong file này không còn đúng.
> Xem [`README.md`](../README.md) ở gốc repo. Giữ lại vì phần bối cảnh vẫn có ích.

# Đọc file này trước

Thư mục: `~/Dev/projects/ve-may-bay`

## Bối cảnh trong một đoạn

Skill `ve-may-bay-noi-dia` quét và so sánh giá vé máy bay nội địa VN, xuất Excel 3 sheet.
Đã qua 3 vòng cải tiến: bản đầu dùng Claude in Chrome, sau đó vá bug regex, và mới nhất
là thêm đường Playwright (nhanh hơn ~15–20 lần cho Traveloka).

## Có gì ở đây

| File | Dùng để làm gì |
|---|---|
| `ve-may-bay-noi-dia.skill` | **Gói cài đặt.** Bấm Save skill một lần là xong — sau đó skill sống trong tài khoản Claude, không đọc từ thư mục này nữa. Giữ lại làm backup |
| `skill-src/` | Bản sao dạng thư mục để đọc/sửa/`git`. Không có gì chạy từ đây |
| `BAN-GIAO_test-vna.md` | Việc còn dang dở — cũng có sẵn trong skill ở `references/vna-todo.md` |
| `SGN-DAD_KhuHoi_T8-2026_20260805-2330.xlsx` | Kết quả quét 8 cặp ngày 14/08–30/08 (dữ liệu ngày 05/08) |
| `checkpoint_20260805.json` | Dữ liệu thô của lần quét đó. Dựng lại Excel bằng `scripts/build_workbook.py` |

## Muốn làm tiếp việc dang dở

Mở session Cowork mới, cho Claude truy cập `~/Dev/projects`, rồi bảo:

> đọc `~/Dev/projects/ve-may-bay/BAN-GIAO_test-vna.md` rồi chạy test

Điều kiện: Playwright MCP đã cài (`npx @playwright/mcp@latest` trong
`claude_desktop_config.json`), và skill đã được Save.

## Muốn quét giá mới

Chỉ cần bảo Claude, ví dụ: *"so giá vé SGN đi Đà Nẵng, thứ 6 đi chủ nhật về, 4 cuối tuần
tới"*. Skill tự kích hoạt.

Lưu ý: file Excel ở trên dùng dữ liệu ngày **05/08/2026**. Giá vé đổi liên tục — quá vài
ngày là nên quét lại chứ đừng dựa vào con số cũ.

## Ba thứ dễ mắc lại nhất

1. **Luôn `await response.json()` trước khi sang chặng kế** (đường Playwright). Không thì
   dữ liệu thiếu mà không báo lỗi — đo được 126 → 18 phần tử, một ngày ra 0 chuyến.
2. **Sanity check bắt buộc**: kết quả thô phải ~110–130 và có ≥3 hãng. Lệch thì quét lại.
3. **Không bịa giá.** Ô nào không lấy được ghi `Không khả dụng` kèm lý do vào sheet `Log`.
   File nhiều ô trống trung thực tốt hơn file đầy đủ có số bịa.
