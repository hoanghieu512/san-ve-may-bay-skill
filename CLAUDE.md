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

## Quy ước version

SKILL.md có dòng version + ngày cập nhật ở hai chỗ: `metadata.version` trong frontmatter và dòng `**vX.Y.Z** · cập nhật DD/MM/YYYY` ở đầu body. `build-skill.sh` chặn đóng gói nếu hai chỗ lệch nhau.

Đổi nội dung skill thì: bump version → cập nhật ngày → tạo git tag khớp (`git tag vX.Y.Z && git push --tags`). Tag là bắt buộc vì chính SKILL.md dặn người dùng đối chiếu version đang nạp với `git tag` mới nhất ở repo nguồn để biết bản của họ có cũ không.

Tag mới nhất hiện tại: `v1.4.0`.

## `runs/` không được commit

`.gitignore` đang ignore cả thư mục `runs/`. Kết quả chạy chỉ tồn tại trên máy local — không có bản sao trên GitHub, nên đừng xoá thư mục run cũ khi dọn dẹp.

Gói `*.skill` cũng bị ignore (sinh lại bằng `./build-skill.sh`).
