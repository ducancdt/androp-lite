# ANDrop Lite (Windows x64)

> **Ultra-fast, lightweight peer-to-peer file transfer for Windows — Zero-cloud, mTLS-secured, privacy-first.**

[![Release](https://img.shields.io/github/v/release/ducancdt/androp-lite?include_prereleases&style=flat-square)](https://github.com/ducancdt/androp-lite/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20x64-blue?style=flat-square)](https://github.com/ducancdt/androp-lite)
[![Architecture](https://img.shields.io/badge/arch-x86__64-orange?style=flat-square)](https://github.com/ducancdt/androp-lite)
[![Language](https://img.shields.io/badge/built%20with-Rust%20%2B%20egui-lightgrey?style=flat-square)](https://github.com/ducancdt/androp-lite)

ANDrop Lite là giải pháp truyền nhận dữ liệu ngang hàng nội bộ (LAN và Tailscale) được tối ưu hóa chuyên sâu cho hệ điều hành Windows (Windows 10 và Windows 11 64-bit). Ứng dụng mang đến trải nghiệm chia sẻ tệp tốc độ cao mà không phụ thuộc vào bất kỳ máy chủ đám mây (cloud) trung gian nào.

---

## 🌟 Điểm nổi bật (Key Features)

- 🔒 **Bảo mật tuyệt đối (mTLS Encrypted)**: Mã hóa kênh truyền đầu cuối bằng TLS 1.3 với cơ chế ghim chứng chỉ số (Certificate Pinning) và xác thực ghép đôi PIN một lần, chống hoàn toàn nghe lén và tấn công Man-in-the-Middle (MitM).
- 🚀 **Tốc độ cao & Tiết kiệm tài nguyên**: Viết hoàn toàn bằng Rust gốc với giao diện `egui` (glow renderer). CPU khi nghỉ xấp xỉ 0.00%, bộ nhớ RAM dưới 100 MB, dung lượng tệp thực thi siêu gọn (~5.2 MB).
- 📦 **Khả chuyển (Portable - No Installer)**: Không cần cài đặt rườm rà, chạy trực tiếp dưới quyền người dùng thông thường (Standard User / Non-Admin). Không can thiệp Registry hay file hệ thống.
- 🛡️ **Tôn trọng quyền riêng tư (Zero-Telemetry & Safe)**:
  - Tuyệt đối không thu thập logs, dữ liệu cá nhân hay gửi telemetry ra Internet.
  - Không cài đặt Windows Service ngầm (No background service).
  - Không tự ý đăng ký khởi động cùng hệ thống (No autostart).
  - Nghiêm cấm tự động mở hoặc thực thi tệp nhận (No auto-open / No auto-execute), bảo vệ an toàn tối đa cho máy tính của bạn trước mã độc.
- 🌐 **Hỗ trợ mạng linh hoạt**: Tự động khám phá thiết bị trong mạng cục bộ (LAN) và kết nối mượt mà qua mạng riêng ảo cá nhân Tailscale (cùng tailnet).
- 🇻🇳 **Giao diện tiếng Việt chuẩn Windows**: Tích hợp trực tiếp phông chữ hệ thống Windows Segoe UI, hiển thị chữ tiếng Việt sắc nét, mượt mà.

---

## 📥 Tải về (Download)

Truy cập trang [**GitHub Releases**](https://github.com/ducancdt/androp-lite/releases/latest) để tải bản phát hành mới nhất:

| Tệp tải về | Định dạng | Mô tả |
| :--- | :--- | :--- |
| **[`androp-lite-windows-x64-v0.1.0-alpha.zip`](https://github.com/ducancdt/androp-lite/releases/latest)** | ZIP Archive | Gói nén di động đầy đủ (chứa tệp thực thi, hướng dẫn, launcher và thông cáo bản quyền) |
| **[`androp-desktop.exe`](https://github.com/ducancdt/androp-lite/releases/latest)** | Windows EXE | Tệp thực thi độc lập x64 trực tiếp |

---

## 🚀 Hướng dẫn sử dụng nhanh (Quick Start)

1. **Tải và giải nén**:
   Tải tệp `androp-lite-windows-x64-v0.1.0-alpha.zip` và giải nén vào bất kỳ thư mục nào trên máy tính của bạn (ví dụ: `Desktop`, `D:\Apps\ANDropLite`).
2. **Khởi chạy**:
   Nhấp đúp vào `androp-desktop.exe` (hoặc tệp `MO_APP_TAI_DAY.bat`).
3. **Kết nối mạng**:
   Đảm bảo các thiết bị cần truyền tệp đang kết nối cùng một mạng Wi-Fi/Ethernet hoặc cùng chung mạng Tailscale cá nhân.
4. **Ghép đôi thiết bị (Pairing)**:
   - Vào tab **Thiết bị (Devices)** trên ứng dụng.
   - Nhập mã xác nhận PIN tin cậy một lần hiển thị trên thiết bị đối tác để hoàn tất ghép đôi mTLS.
5. **Gửi & Nhận tệp (Transfer)**:
   - Chọn tab **Gửi (Send)**: Chọn tệp cần gửi và chọn thiết bị nhận trong danh sách đã ghép đôi.
   - Bên nhận sẽ xuất hiện hộp thoại xác nhận nhận tệp, bấm **Đồng ý** để bắt đầu truyền dữ liệu với thanh tiến trình trực quan theo thời gian thực.
   - Tệp sau khi nhận thành công sẽ nằm an toàn trong thư mục `Downloads/ANDrop`.

---

## 🔍 Kiểm tra tính toàn vẹn (SHA-256 Checksums)

Đối soát mã băm SHA-256 chính thức cho bản phát hành `v0.1.0-alpha`:

```text
598ab03f7101bae9a414170eff9a2651400acffe216164c029079bcd1e15b5c3  androp-desktop.exe
5377fde67361b367b12491948354831b61b15bdf1ac74c1f8cbcf1d75a6c4f88  androp-lite-windows-x64-v0.1.0-alpha.zip
2119b49cff40c354c7244d5c96b0cf6be21d06f61d956a58548f7e6ddef7cee8  README.txt
a27ed8a2e51169aeb09686bebdf63c4416c268102eddb0849178dc533badc094  THIRD_PARTY_NOTICES.md
2fd730fffc258fe999b4e3fdfaf791c1559c3ea995317b8306cc96ff9fa603bb  BUILD_METADATA.json
```

**Cách kiểm tra bằng PowerShell trên Windows:**
```powershell
Get-FileHash -Algorithm SHA256 androp-desktop.exe
```

---

## 💻 Yêu cầu hệ thống (System Requirements)

- **Hệ điều hành**: Windows 10 x64 (Build 19041 trở lên) hoặc Windows 11 x64.
- **Quyền hạn**: Tài khoản người dùng thông thường (Standard User, không yêu cầu quyền Administrator).
- **Phụ thuộc**: Microsoft Universal C Runtime (UCRT) và thư viện VC++ Runtime (đã tích hợp sẵn trên các bản Windows cập nhật).

---

## 📜 Bản quyền & Giấy phép (License & Notices)

- Ứng dụng ANDrop Lite © 2026 bởi **ducancdt**. Mọi quyền được bảo lưu (All rights reserved).
- Chi tiết thông cáo bản quyền của các thư viện mã nguồn mở bên thứ ba (Rust ecosystem, egui, rustls, ...) xem tại [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
