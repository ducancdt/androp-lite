# ANDrop Lite v0.1.2-alpha — Windows x64

Kết nối cố định bằng tài khoản và mật khẩu. Hai máy chỉ cần kết nối một lần, sau đó chọn máy và gửi file.

## Tải về

- [ZIP đầy đủ](https://github.com/ducancdt/androp-lite/releases/download/v0.1.2-alpha/androp-lite-windows-x64-v0.1.2-alpha.zip)
- [EXE](https://github.com/ducancdt/androp-lite/releases/download/v0.1.2-alpha/androp-desktop.exe)
- [SHA-256](https://github.com/ducancdt/androp-lite/releases/download/v0.1.2-alpha/SHA256SUMS.txt)

## Cách dùng

1. Mở bản mới trên cả hai máy. Vào **Thiết bị**, bấm **Bật kết nối và ghi nhớ**.
2. Máy A đặt **Tài khoản của máy này** và mật khẩu cố định, rồi **Lưu tài khoản**.
3. Máy B nhập **IP + tài khoản + mật khẩu của A**, bấm **Kết nối và ghi nhớ máy**. IP có thể sao chép trên máy A; cổng mặc định 53318 nên không cần nhập thêm.
4. Vào **Trò chuyện & Gửi**, chọn máy rồi gửi file. Máy nhận bấm **Nhận tệp**.

Lần sau mở ứng dụng, chọn máy đã lưu và gửi. Không cần chép mã dài hoặc nhập lại mật khẩu. Chỉ một máy cần đặt tài khoản để thiết lập kết nối hai chiều. Cả hai máy phải mở ứng dụng và có đường mạng LAN hoặc Tailscale tới nhau. Không cần server ANDrop trung tâm.

## Điểm mới

- Tài khoản và mật khẩu cố định để thêm máy, lưu kết nối hai chiều qua lần mở lại.
- Ghi nhớ IP/cổng đã chọn và tự bật kết nối khi mở lại; nút Tắt kết nối giữ trạng thái tắt.
- Giao diện ngắn gọn; lời mời dài nằm trong mục nâng cao cho tương thích bản cũ.
- Xác thực mật khẩu có mã hóa và kiểm chứng khóa danh tính; chat/file giữ TLS và quyền riêng từng máy.
- File nhận vẫn cần chấp thuận, kiểm SHA-256, lưu không ghi đè.

## Đổi mật khẩu / bỏ kết nối

Tài khoản thuộc máy của bạn, không phải tài khoản cloud. Đổi mật khẩu ngăn lần đăng nhập mới bằng mật khẩu cũ. Máy đã lưu vẫn được dùng; chọn **Bỏ kết nối** để thu hồi máy đó. Nếu đổi IP/cổng, thêm lại bằng địa chỉ mới. IP Tailscale phù hợp khi muốn địa chỉ ổn định.

## Dữ liệu và cập nhật

Đóng bản cũ rồi mở EXE mới. Dữ liệu được giữ ở `%LOCALAPPDATA%\ANDropLite\network-v2`, bảo vệ bằng Windows DPAPI. Không sao chép thư mục này sang máy khác. Không tự xóa/reset dữ liệu khi cập nhật. Khi báo `IDENTITY_CORRUPT`, mạng bị khóa: cần giữ bản sao và khôi phục dữ liệu hoặc chủ động tạo danh tính mới, rồi kết nối lại các máy.

## Kiểm thử và giới hạn

200 kiểm thử Rust PASS; fmt/check/clippy/build release PASS trên Windows. Đã kiểm thử đăng nhập, mật khẩu sai, giả mạo/replay, đổi mật khẩu, lưu máy/cổng qua restart và truyền file thật giữa hai runtime local. Giao diện native Windows đã mở để kiểm tra bố cục. Chưa nghiệm thu LAN/Tailscale trên hai máy thật, DPI/RDP hoặc Windows sạch; không coi các mục này là PASS.

Bản alpha chưa ký số. Một file mỗi lượt; batch/folder, pause/resume và khôi phục lượt truyền sau khởi động chưa hoàn chỉnh. Mất xác nhận cuối khi đăng nhập có thể cần đăng nhập lại. Không tự thay pin khi chứng chỉ thay đổi; chứng chỉ hiện có thời hạn khoảng một năm. Không cài Windows autostart/service, không tự sửa firewall/tailnet. Xem THIRD_PARTY_NOTICES.md cho inventory và license của thư viện. Windows x64, có thể cần Microsoft Visual C++ Runtime.
