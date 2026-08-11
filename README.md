# ve-may-bay-noi-dia

Skill quét và so sánh giá vé máy bay **nội địa Việt Nam** từ Google Flights + Traveloka,
xuất Excel 3 sheet (Data / Summary / Log). Không bịa giá — ô nào không lấy được thì ghi
`Không khả dụng` kèm lý do vào sheet `Log`.

Repo này là **nguồn của skill**, không phải nơi chạy skill.

## Version

Phiên bản hiện tại: **v1.2.0** (11/08/2026)

Số version nằm ở hai chỗ trong [`SKILL.md`](skill/ve-may-bay-noi-dia/SKILL.md) — `metadata.version`
ở frontmatter và một dòng `**vX.Y.Z**` ngay đầu body. `build-skill.sh` từ chối đóng gói nếu hai
chỗ lệch nhau.

**Kiểm tra bản đang nạp có mới nhất chưa:** hỏi Claude "skill vé máy bay đang là version mấy",
rồi so với tag mới nhất ở repo:

```bash
git ls-remote --tags origin | tail -1
```

Lệch → bản đang nạp đã cũ: `./build-skill.sh` rồi Save đè gói `.skill` mới. Nếu cài bằng
symlink (xem dưới) thì không bao giờ lệch.

Quy ước tăng số: sửa quy trình quét / đổi format Excel → tăng **minor**; vá bug, sửa đường dẫn,
làm rõ văn bản → tăng **patch**. Mỗi lần tăng nhớ `git tag vX.Y.Z && git push --tags`.

| Version | Ngày | Thay đổi |
|---|---|---|
| 1.2.0 | 11/08/2026 | Tách bạch hai khái niệm giá: `Giá chốt` đổi tên thành `Giá chốt (nguồn ưu tiên)`, thêm cột `Giá thấp nhất (mọi nguồn)` ở Data và Summary. Cột Summary `Tổng vé rẻ nhất` (sai tên — nó không phải giá rẻ nhất) đổi thành `Tổng theo Giá chốt` |
| 1.1.0 | 11/08/2026 | Thêm `scripts/merge_sources.py` — mắt xích extract→build trước đây phải viết tay mỗi lần chạy. Thêm ngưỡng bắt buộc điều tra khi hai nguồn lệch ≥25%: tô cam trong workbook, cảnh báo ra stderr, thành luật ở §6 |
| 1.0.1 | 11/08/2026 | Sửa hai tham chiếu chéo sai: `vna-date-scan.md` tự gọi là "bước 0.5" (đúng ra là Bước 0 / §3), và `build_workbook.py` trỏ sang §7 thay vì §8 |
| 1.0.0 | 11/08/2026 | Mốc đầu tiên có đánh số. Gồm đường Playwright cho Traveloka, quét ngày qua API VNA `air-best-price`, và bản vá đường dò `recalc.py` chạy được cả Cowork lẫn Claude Code local |

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
- **`openpyxl`** cho python3 đang dùng — `scripts/build_workbook.py` cần:
  `pip3 install openpyxl`. Cowork có sẵn.
- **Skill `xlsx` của hệ thống** + **LibreOffice** (`soffice` trên PATH) — SKILL.md §8 gọi
  `recalc.py` từ đó để tính công thức Excel. Đường dò trong §8 chạy được cả ở Cowork lẫn
  Claude Code local.

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
