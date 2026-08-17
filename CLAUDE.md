# ve-may-bay — hướng dẫn cho Claude khi làm việc trong repo này

Repo này có hai vai trò tách biệt:

- **Nguồn sự thật của skill `ve-may-bay-noi-dia`** — code + tài liệu skill được phát triển ở đây, đóng gói thành `.skill` để Save vào tài khoản Claude.
- **Kho lưu kết quả các lần chạy skill** — mỗi lần quét giá là một thư mục trong `runs/`, giữ lại để đối chiếu biến động giá giữa các lần.

## Nơi lưu kết quả chạy skill

`/Users/lavopavden/Dev/projects/ve-may-bay/runs/<YYYYMMDD>/`

Khi chạy skill trong Cowork: **mount thư mục này ngay đầu phiên** bằng `request_cowork_directory`, trước khi bắt đầu quét. Đừng để đến lúc build workbook mới phát hiện không ghi được — lúc đó dữ liệu raw đang nằm trong scratchpad của phiên và rất dễ rơi mất khi copy tay.

Yêu cầu về nội dung mỗi thư mục run (`job.json` + raw + checkpoint + `.xlsx`) nằm ở §8 của `skill/ve-may-bay-noi-dia/SKILL.md` — đó là quy ước chung, không phải thứ riêng của máy này.

## Sửa skill ở đâu

Nguồn sự thật: `skill/ve-may-bay-noi-dia/`. Sửa ở đây → chạy `./build-skill.sh` → Save đè gói `.skill` trong Cowork.

`build-skill.sh` sinh hai file giống hệt nhau: `ve-may-bay-noi-dia.skill` và `ve-may-bay-noi-dia-v<version>.skill`. **Upload bản có version.** Đã xảy ra chuyện upload bản không-version mà Cowork vẫn nạp nội dung cũ, rồi kết luận là chưa build lại — mất một vòng tranh luận mới truy ra file bên phía Cowork không đổi. Tên có version thì nhìn là biết đang cầm bản nào, không phải đi so `md5`.

Sửa SKILL.md xong mà không chạy `build-skill.sh` thì gói vẫn là ảnh chụp cũ — upload lên không có tác dụng gì.

Cache skill mà Cowork nạp (nằm dưới `/var/folders/.../claude-hostloop-plugins/`) là **read-only**. Sửa trực tiếp trong đó không có tác dụng và sẽ mất khi đổi phiên.

### Cài đè phải đủ 13 file, không chỉ SKILL.md

Gói `.skill` là zip chứa **đủ 13 file** (SKILL.md + 5 `references/` + 7 `scripts/`). Nhưng agent
bên Cowork có đường tắt `save_skill` chỉ ghi lại SKILL.md và giữ nguyên `references/` +
`scripts/` của bản đang cài. Đã xảy ra ở v1.4.0: gói đủ file, nhưng chỉ SKILL.md được ghi.

Lần đó vô hại vì v1.4.0 chỉ sửa SKILL.md. Nguy hiểm là khi bản mới có sửa `scripts/`: SKILL.md
mới chạy với script cũ, sai âm thầm, không có lỗi nào để lần ra.

Vì vậy khi drop gói: nói rõ **"cài đè toàn bộ gói, cả references và scripts"**, rồi yêu cầu
liệt kê lại từng file đã ghi. Đường tắt chỉ-SKILL.md chấp nhận được duy nhất khi đã diff và
biết chắc 12 file kia không đổi.

Cách tự kiểm nhanh xem bản mới có đụng file khác ngoài SKILL.md:

```bash
git diff --stat <tag-cũ> HEAD -- skill/
```

Lịch sử để tham chiếu: 3/5 bản đầu (v1.0.1, v1.1.0, v1.2.0) đều có sửa `scripts/` —
"hầu như chỉ sửa SKILL.md" là cảm giác sai, đừng dựa vào nó để chọn cách upload.

## Quy ước version

SKILL.md có dòng version + ngày cập nhật ở hai chỗ: `metadata.version` trong frontmatter và dòng `**vX.Y.Z** · cập nhật DD/MM/YYYY` ở đầu body. `build-skill.sh` chặn đóng gói nếu hai chỗ lệch nhau.

Đổi nội dung skill thì: bump version → cập nhật ngày → tạo git tag khớp (`git tag vX.Y.Z && git push --tags`). Tag là bắt buộc vì chính SKILL.md dặn người dùng đối chiếu version đang nạp với `git tag` mới nhất ở repo nguồn để biết bản của họ có cũ không.

Tag mới nhất hiện tại: `v1.4.0`.

## `runs/` không được commit

`.gitignore` đang ignore cả thư mục `runs/`. Kết quả chạy chỉ tồn tại trên máy local — không có bản sao trên GitHub, nên đừng xoá thư mục run cũ khi dọn dẹp.

Gói `*.skill` cũng bị ignore (sinh lại bằng `./build-skill.sh`).
