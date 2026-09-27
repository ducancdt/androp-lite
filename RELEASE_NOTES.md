# ANDrop Lite v0.1.2-alpha — tài khoản cố định, nhớ các máy

- Không cần chép mã dài: nhập IP, tài khoản và mật khẩu của máy kia một lần.
- Lưu máy đã kết nối hai chiều; lần sau mở app, chọn máy và gửi file.
- Ghi nhớ cổng nhận và tự bật kết nối khi mở lại ứng dụng.
- Giao diện đơn giản hơn, mật khẩu được che; lời mời cũ nằm trong mục nâng cao.
- Giữ xác thực danh tính máy, TLS, xác nhận nhận file và kiểm tra SHA-256.

**Cách dùng:** Mở cùng bản trên hai máy → Bật kết nối và ghi nhớ → máy A đặt tài khoản → máy B nhập IP + tài khoản + mật khẩu của A → chọn máy trong Trò chuyện & Gửi.

Đổi mật khẩu chỉ áp dụng cho đăng nhập mới; chọn Bỏ kết nối để thu hồi máy đã lưu. Hai máy cần mở app và có kết nối LAN/Tailscale. Nếu đổi IP/cổng thì thêm lại máy bằng địa chỉ mới.

**Kiểm thử:** 200 test Rust và 34 test planning PASS; fmt/check/clippy/release PASS. Đã kiểm thử truyền file, đăng nhập đúng/sai, chống giả mạo và lưu kết nối qua restart trên Windows local. Giao diện native đã kiểm tra bố cục. Chưa nghiệm thu hai máy thật hoặc Windows sạch. Bản alpha chưa ký số; batch/folder, pause/resume và phục hồi lượt truyền chưa hoàn chỉnh. Tải alpha trực tiếp tại trang này; trình cập nhật của bản cũ có thể chưa thấy bản alpha.

Tải ZIP đầy đủ hoặc EXE bên dưới. Dữ liệu cũ được giữ nguyên; nếu báo IDENTITY_CORRUPT cần khôi phục dữ liệu hoặc chủ động tạo lại danh tính, không tự reset.
