# ANDrop Lite v0.1.1-alpha — Windows x64

Bản alpha mới cho chat và gửi file qua LAN/Tailscale. Chưa ký số; chưa nghiệm thu trên hai máy thật hoặc máy Windows sạch. Hai máy cần chạy cùng bản này.

## Tải về

- [ZIP đầy đủ](https://github.com/ducancdt/androp-lite/releases/download/v0.1.1-alpha/androp-lite-windows-x64-v0.1.1-alpha.zip)
- [EXE](https://github.com/ducancdt/androp-lite/releases/download/v0.1.1-alpha/androp-desktop.exe)
- [SHA-256](https://github.com/ducancdt/androp-lite/releases/download/v0.1.1-alpha/SHA256SUMS.txt)
- [Release notes](https://github.com/ducancdt/androp-lite/releases/tag/v0.1.1-alpha)

## Thay đổi

- Ghép nối và màn hình duyệt dùng chung trạng thái; hỗ trợ endpoint/cổng gọi ngược từ lời mời.
- LAN/Tailscale dùng cùng runtime TLS 1.3, pin chứng chỉ và token riêng từng peer. Không cần server ANDrop trung tâm.
- Chat báo máy kia đã nhận sau ACK; retry có chống trùng.
- Nhận file cần chấp thuận, truyền theo checkpoint, kiểm SHA-256 và lưu không ghi đè. Xác minh chạy riêng để control/chat tiếp tục phản hồi.
- Sửa mất ACK/status, báo pending khi mạng tắt, cuộn tới phần duyệt và đóng cửa sổ.
- Thu hồi peer hủy target gửi cũ và tác vụ nhận ở điểm an toàn; lỗi lưu quyền không báo thành công.

## Chạy thử trên hai máy

1. Đóng bản cũ, giải nén vào thư mục riêng và mở `androp-desktop.exe` hoặc `MO_APP_TAI_DAY.bat`.
2. Vào **Thiết bị**, chọn IP LAN/Tailscale của chính máy đó, cổng **53318**, rồi **Bật kết nối**.
3. Máy A tạo lời mời, sao chép toàn bộ chuỗi `androp-pair-v1:...` và chuyển riêng qua kênh tin cậy.
4. Máy B dán toàn bộ lời mời rồi gửi yêu cầu ghép. Mã PIN đơn lẻ của bản cũ không dùng cho luồng này.
5. Máy A cuộn tới **Duyệt yêu cầu**, kiểm tra thiết bị và **Chấp thuận**. Đợi cả hai máy báo đã ghép.
6. Thử chat hai chiều. Khi gửi file synthetic, máy nhận phải bấm **Nhận tệp**. Chỉ coi hoàn tất khi bên nhận đã xác minh/lưu xong.
7. Đối chiếu file nguồn/đích bằng `Get-FileHash -Algorithm SHA256 <file>`.

LAN cần có route giữa hai máy. Tailscale cần kết nối cùng tailnet với quyền truy cập phù hợp; ứng dụng không tự thay đổi firewall hoặc tailnet.

## Dữ liệu và cập nhật

Danh tính/trust được bảo vệ bằng DPAPI theo tài khoản Windows tại `%LOCALAPPDATA%\ANDropLite\network-v2`. Không copy thư mục này sang máy khác, không đưa lời mời/token vào báo cáo công khai. Cập nhật EXE không tự xóa/reset dữ liệu. Khi báo `IDENTITY_CORRUPT`, mạng bị khóa; cần giữ bản sao dữ liệu và quyết định khôi phục hoặc tạo danh tính mới có chủ đích. Tạo mới phải ghép lại.

## Trạng thái kiểm thử và giới hạn

190 test Rust PASS; fmt/check/clippy/build release PASS trên Windows build 26200, Rust 1.95.0. Trong đó 20 test runtime kiểm TLS loopback, pairing, chat, file nhiều chunk hai chiều, consent, retry, hash/no-overwrite và revoke. Kết quả local không thay cho nghiệm thu LAN/Tailscale trên hai máy thật.

Một file mỗi lượt; chưa hỗ trợ đầy đủ batch/folder, pause/resume và startup recovery trong luồng desktop mới. Chưa qualification file trên 4 GiB, soak, DPI/RDP, sleep/wake hoặc máy sạch. Sau mở lại cần chọn IP/bật kết nối và kiểm tra thư mục nhận. API runtime đang khác baseline đầy đủ; không khẳng định tương thích protocol-v1 với client khác.

Windows x64; có thể cần Microsoft Visual C++ Runtime. Không tắt Defender/SmartScreen toàn hệ thống để chạy bản unsigned. Xem `THIRD_PARTY_NOTICES.md` để biết thông tin thư viện và giấy phép.
