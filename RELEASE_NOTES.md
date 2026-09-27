ANDrop Lite **v0.1.1-alpha** cho Windows x64, tập trung sửa ghép nối, chat và gửi file qua LAN/Tailscale. Hai máy cần cập nhật cùng bản.

### Thay đổi

- Yêu cầu ghép và màn hình duyệt dùng chung trạng thái; sửa endpoint/cổng gọi ngược. Mỗi máy chạy ứng dụng làm bên nhận, không cần server ANDrop trung tâm.
- Runtime dùng TLS 1.3, pin chứng chỉ và token riêng từng peer. Dùng toàn bộ lời mời `androp-pair-v1:...`, không dùng PIN đơn lẻ của bản cũ.
- Chat chỉ báo đã nhận sau ACK, có chống trùng khi retry.
- File cần người nhận chấp thuận, đủ byte và khớp SHA-256; lưu không ghi đè. Xác minh bất đồng bộ, phục hồi khi mất ACK/status.
- Sửa thu hồi peer khi đang gửi/nhận, lỗi lưu quyền, trạng thái pending lúc tắt mạng, cuộn phần duyệt và đóng cửa sổ.

### Tải và chạy

Tải ZIP `androp-lite-windows-x64-v0.1.1-alpha.zip`, giải nén vào thư mục riêng và mở `androp-desktop.exe`. ZIP gồm hướng dẫn, launcher, metadata và third-party notices. Có EXE riêng và `SHA256SUMS.txt` để đối chiếu.

Vào **Thiết bị**, chọn IP của chính máy mình, bật cổng **53318**. Máy A tạo lời mời; máy B dán toàn bộ lời mời và gửi yêu cầu; máy A cuộn xuống duyệt. File cũng cần chấp thuận riêng ở máy nhận. Không đưa lời mời/token vào issue công khai.

### Kiểm thử và giới hạn

**190 test Rust PASS**; fmt, check, clippy và release build PASS. 20 test runtime gồm TLS loopback, chat/file nhiều chunk hai chiều, consent, retry, hash/no-overwrite và revoke.

Đây là **prerelease chưa ký số**, chưa nghiệm thu LAN/Tailscale trên hai máy thật hoặc máy Windows sạch. Chưa qualification file trên 4 GiB, crash/power loss toàn diện, soak và DPI/RDP. Luồng mới hiện một file mỗi lượt; batch/folder, pause/resume và startup recovery chưa hoàn chỉnh. Không coi kết quả local là xác nhận toàn bộ release gates.

Cập nhật không tự xóa/reset danh tính. Nếu gặp `IDENTITY_CORRUPT`, ứng dụng khóa mạng; giữ bản sao dữ liệu và quyết định khôi phục/tạo mới có chủ đích. Danh tính mới cần ghép lại. Không tắt Defender/SmartScreen toàn hệ thống để chạy bản unsigned.
