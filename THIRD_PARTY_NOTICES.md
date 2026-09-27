# Thông cáo Bản quyền Phần mềm Bên thứ ba (Third-Party Notices & Licenses Inventory)

## 1. Bản quyền Sản phẩm ANDrop Lite
- **Ứng dụng**: ANDrop Lite (Windows-first Baseline V2)
- **Bản quyền**: © 2026 ANDrop Lite Contributors. All rights reserved.
- **Giấy phép sản phẩm**: Giấy phép phần mềm chính thức của sản phẩm do chủ sở hữu dự án quyết định. Bộ tài liệu này không tự ý áp đặt hoặc bịa đặt giấy phép sản phẩm (R032).

---

## 2. Yêu cầu Môi trường Thực thi (Runtime Requirements)
- **Hệ điều hành**: Microsoft Windows 10 (Version 2004 / Build 19041 trở lên) hoặc Windows 11 x64 (Non-Admin context).
- **Thư viện C Runtime**:
  - Microsoft Universal C Runtime (`ucrtbase.dll` / `api-ms-win-crt-*.dll`): Tích hợp sẵn mặc định trong hệ điều hành Windows 10 và Windows 11.
  - Microsoft Visual C++ 2015-2022 Redistributable (`vcruntime140.dll`): Có sẵn trên hầu hết các máy tính Windows hiện đại, hoặc tải trực tiếp từ Microsoft Support nếu chưa có.
- **Tính khả chuyển (Portability)**: Ứng dụng là tệp thực thi di động độc lập (`androp-desktop.exe`), không yêu cầu quyền Quản trị viên (Administrator), không cài đặt driver ngầm, không tạo Windows Service hay Scheduled Task.

---

## 3. Danh mục Thư viện Phụ thuộc (Dependencies Inventory)

Toàn bộ các thư viện bên thứ ba được sử dụng trong ANDrop Lite đều là mã nguồn mở với các giấy phép tự do tương thích cao (MIT, Apache-2.0, ISC, BSD-3-Clause). Dưới đây là danh mục chi tiết từ `Cargo.lock` đã khóa:

| Crate / Thư viện | Phiên bản | Giấy phép (SPDX) | Mục đích sử dụng | Nguồn cung cấp |
|---|---|---|---|---|
| **eframe / egui** | 0.31.1 | MIT OR Apache-2.0 | Giao diện đồ họa người dùng native (Immediate Mode GUI) | [crates.io/crates/eframe](https://crates.io/crates/eframe) |
| **rustls** | 0.23.45 | Apache-2.0 OR ISC OR MIT | Giao thức mã hóa TLS 1.3 bảo vệ kênh truyền | [crates.io/crates/rustls](https://crates.io/crates/rustls) |
| **rustls-pki-types** | 1.15.1 | MIT OR Apache-2.0 | Cấu trúc dữ liệu chứng chỉ số PKI cho TLS | [crates.io/crates/rustls-pki-types](https://crates.io/crates/rustls-pki-types) |
| **rcgen** | 0.13.2 | MIT OR Apache-2.0 | Sinh cặp khóa và chứng chỉ X.509 tự ký nội bộ | [crates.io/crates/rcgen](https://crates.io/crates/rcgen) |
| **sha2** | 0.10.9 | MIT OR Apache-2.0 | Thuật toán băm mã hóa SHA-256 đối soát tệp | [crates.io/crates/sha2](https://crates.io/crates/sha2) |
| **uuid** | 1.26.1 | Apache-2.0 OR MIT | Định danh phiên truyền và đối tác (UUID v4) | [crates.io/crates/uuid](https://crates.io/crates/uuid) |
| **serde** | 1.0.229 | MIT OR Apache-2.0 | Khung tuần tự hóa / giải tuần tự hóa dữ liệu | [crates.io/crates/serde](https://crates.io/crates/serde) |
| **serde_json** | 1.0.151 | MIT OR Apache-2.0 | Xử lý định dạng JSON an toàn cho journal/cấu hình | [crates.io/crates/serde_json](https://crates.io/crates/serde_json) |
| **thiserror** | 2.0.21 | MIT OR Apache-2.0 | Định nghĩa kiểu lỗi định kiểu rõ ràng (Typed Errors) | [crates.io/crates/thiserror](https://crates.io/crates/thiserror) |
| **windows-sys** | 0.59.0 | MIT OR Apache-2.0 | Giao tiếp Win32 API (DPAPI, Filesystem attributes) | [crates.io/crates/windows-sys](https://crates.io/crates/windows-sys) |

---

## 4. Văn bản Giấy phép Bản quyền (License Texts)

### 4.1. The MIT License
```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 4.2. Apache License, Version 2.0
```text
                              Apache License
                        Version 2.0, January 2004
                     http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.
   "License" shall mean the terms and conditions for use, reproduction,
   and distribution as defined by Sections 1 through 9 of this document.

   "Licensor" shall mean the copyright owner or entity authorized by
   the copyright owner that is granting the License.

   "Legal Entity" shall mean the union of the acting entity and all
   other entities that control, are controlled by, or are under common
   control with that entity.

2. Grant of Copyright License. Subject to the terms and conditions of
   this License, each Contributor hereby grants to You a perpetual,
   worldwide, non-exclusive, no-charge, royalty-free, irrevocable
   copyright license to reproduce, prepare Derivative Works of,
   publicly display, publicly perform, sublicense, and distribute the
   Work and such Derivative Works in Source or Object form.

3. Grant of Patent License. Subject to the terms and conditions of
   this License, each Contributor hereby grants to You a perpetual,
   worldwide, non-exclusive, no-charge, royalty-free, irrevocable
   patent license to make, have made, use, offer to sell, sell, import,
   and otherwise transfer the Work.

4. Redistribution. You may reproduce and distribute copies of the
   Work or Derivative Works thereof in any medium, with or without
   modifications, and in Source or Object form, provided that You
   meet the following conditions:
   (a) You must give any other recipients of the Work or Derivative Works
       a copy of this License; and
   (b) You must cause any modified files to carry prominent notices stating
       that You changed the files; and
   (c) You must retain, in the Source form of any Derivative Works that
       You distribute, all copyright, patent, trademark, and attribution
       notices from the Source form of the Work; and
   (d) If the Work includes a "NOTICE" text file as part of its distribution,
       then any Derivative Works that You distribute must include a readable
       copy of the attribution notices contained within such NOTICE file.

5. Disclaimer of Warranty. Unless required by applicable law or agreed to
   in writing, Licensor provides the Work (and each Contributor provides
   its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
   OF ANY KIND, either express or implied.
```

### 4.3. The ISC License
```text
Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```
