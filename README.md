# ve-may-bay-noi-dia

Skill quét và so sánh giá vé máy bay **nội địa Việt Nam** từ Google Flights + Traveloka,
xuất Excel 3 sheet (Data / Summary / Log). Không bịa giá — ô nào không lấy được thì ghi
`Không khả dụng` kèm lý do vào sheet `Log`.

Repo này là **nguồn của skill**, không phải nơi chạy skill.

## Cấu trúc

| Đường dẫn | Là gì | Có push lên GitHub |
|---|---|---|
| `skill/ve-may-bay-noi-dia/` | **Toàn bộ skill.** SKILL.md + `references/` + `scripts/` | ✅ |
| `docs/` | Ghi chép lịch sử: bàn giao, kết quả test VNA | ✅ |
| `build-skill.sh` | Đóng gói thành file `.skill` | ✅ |
| `runs/` | Sản phẩm từng lần quét: Excel, checkpoint, JSON thô, script ad-hoc | ❌ (gitignore) |
| `*.skill` | Gói cài đặt — sinh lại được, không commit | ❌ (gitignore) |

Ranh giới: cái gì skill cần để **chạy lần sau** thì nằm trong `skill/`. Cái gì là **kết quả**
của một lần chạy cụ thể thì nằm trong `runs/`.

## Cài skill

**Cowork / Claude Desktop** — đóng gói rồi Save:

```bash
./build-skill.sh
```

Kéo `ve-may-bay-noi-dia.skill` vào chat, bấm Save skill. Sau đó skill sống trong tài khoản,
không đọc từ thư mục này nữa.

**Claude Code** — symlink thẳng vào thư mục skill cá nhân:

```bash
ln -s "$PWD/skill/ve-may-bay-noi-dia" ~/.claude/skills/ve-may-bay-noi-dia
```

Cách này sửa file trong repo là skill đổi theo ngay, không cần đóng gói lại.

## Điều kiện chạy

- **Playwright MCP** (`npx @playwright/mcp@latest`) — đường nhanh cho Traveloka, rẻ hơn
  ~15–20 lần so với Claude in Chrome. Không có vẫn chạy được nhưng tốn thao tác.
- **Claude in Chrome** — đường dự phòng, và là đường chính cho Google Flights.
- **`openpyxl`** cho python3 đang dùng — `scripts/build_workbook.py` cần. Cowork có sẵn;
  máy local có thể phải `pip3 install openpyxl`.
- **Skill `xlsx` của hệ thống** — SKILL.md §8 gọi `recalc.py` từ đó. Đường dò hiện viết theo
  sandbox Cowork (`/sessions/*/mnt/...`); chạy ở Claude Code local có thể phải dò lại.

## Chạy

Chỉ cần nói chuyện bình thường, skill tự kích hoạt:

> so giá vé SGN đi Đà Nẵng, 4 cặp ngày cuối tháng 8

Skill sẽ hỏi tham số thiếu, ước lượng ngân sách thao tác trước khi quét, quét one-way từng
chiều, ghi checkpoint sau mỗi chặng, rồi build Excel.

## Đọc thêm

- [`skill/ve-may-bay-noi-dia/SKILL.md`](skill/ve-may-bay-noi-dia/SKILL.md) — quy trình đầy đủ
- [`references/site-quirks.md`](skill/ve-may-bay-noi-dia/references/site-quirks.md) — bẫy của từng trang
- [`references/playwright-path.md`](skill/ve-may-bay-noi-dia/references/playwright-path.md) — bẫy mất dữ liệu im lặng
- [`docs/KET-QUA_test-vna_20260809.md`](docs/KET-QUA_test-vna_20260809.md) — kết quả dò API VNA
