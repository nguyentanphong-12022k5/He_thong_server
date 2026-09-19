# 🎮 Minecraft Smart Server Manager (V2.0)

Một phần mềm quản lý Máy chủ Minecraft chuyên nghiệp, giao diện đồ họa hiện đại (CustomTkinter), và hoàn toàn tự động hóa. Công cụ được thiết kế để giúp bất kỳ ai (dù không biết IT) cũng có thể tạo và quản lý máy chủ Minecraft có cài Mod/Modpack dễ dàng thông qua Docker.

![Version](https://img.shields.io/badge/Version-2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)
![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)

---

## ✨ Tính Năng Nổi Bật
- **🖥️ Giao diện Hiện Đại:** Thiết kế giao diện bóng bẩy với CustomTkinter (Dark Mode mặc định).
- **🗂️ Quản lý Đa Máy Chủ:** Tạo không giới hạn số lượng Server (Sinh tồn, Modpack, Vanilla...) độc lập nhau.
- **⚙️ Cài Đặt Chuyên Sâu Trực Quan:** Chỉnh sửa RAM (2G -> 16G), bật/tắt Crack (Online Mode), bật/tắt PVP cực kỳ dễ dàng qua nút gạt.
- **📦 Cửa Hàng Mod (ModStore):** Tìm kiếm và tải trực tiếp hàng ngàn Mod từ Modrinth. Hệ thống tự động lọc Mod tương thích với Phiên bản và Loại Server (Forge/Fabric).
- **🚀 1-Click Modpack Installer:** Tích hợp bộ cài Modpack tự động. Chỉ cần dán Link Modpack Modrinth vào lúc tạo Server, phần mềm sẽ tự động tải và cấu hình toàn bộ.
- **🤝 Chia Sẻ Mod Cho Bạn Bè (ClientSync):** Nén toàn bộ thư mục `mods` của Server thành một file Zip siêu chuẩn chỉ bằng 1 nút bấm để gửi cho bạn bè cài đặt.
- **🛡️ Playit.gg Tích Hợp Sâu:** Chia sẻ IP tĩnh toàn cầu, bạn bè có thể vào chơi mà không cần bạn mở Port modem (Port Forwarding). Tất cả các Server dùng chung 1 IP tĩnh duy nhất.
- **🤖 Watchdog Thông Minh:** Tự động giám sát người chơi. Nếu Server trống quá 30 phút, Watchdog sẽ tự động Save game và Tắt Server để tiết kiệm tài nguyên máy tính.
- **🧹 Máy Hút Bụi Server:** Dọn dẹp rác Docker chỉ với 1 Click.

---

## 🚀 Hướng Dẫn Cài Đặt

### Yêu Cầu Hệ Thống:
1. Máy tính cài đặt sẵn [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Và nhớ bật chạy ngầm Docker).
2. [Python 3.10+](https://www.python.org/downloads/)

### Bước 1: Tải mã nguồn
Clone dự án này về máy của bạn:
```bash
git clone https://github.com/nguyentanphong-12022k5/He_thong_server.git
cd He_thong_server
```

### Bước 2: Cài đặt Thư viện
```bash
pip install customtkinter requests urllib3 pyyaml
```

### Bước 3: Khởi chạy Phần mềm
Chỉ cần chạy lệnh sau để mở giao diện:
```bash
python v2_app.py
```
*(Hoặc chạy file `build.bat` để đóng gói phần mềm thành 1 file `.exe` duy nhất có thể gửi cho bạn bè).*

---

## 🕹️ Cách Sử Dụng Căn Bản
1. **Tạo Server:** Bấm `+ Tạo Server Mới`, chọn Loại Server (Paper/Forge/Fabric), nhập Phiên bản (ví dụ `1.20.1`) và bấm Tạo. *(Nếu muốn chơi Modpack, hãy dán Link Modpack vào ô tùy chọn).*
2. **Cấu hình:** Bấm vào biểu tượng `🔧 Cài Đặt` để chỉnh RAM cho Server.
3. **Mở Mạng:** Lần đầu tiên chạy, bạn cần vào `🌐 Lấy IP (Playit)` để xác thực danh tính mạng. Sau đó, máy chủ sẽ có một IP tĩnh cố định (VD: `abc-xyz.auto.playit.gg`) vĩnh viễn.
4. **Tải Mod:** Qua tab `Cửa Hàng Mod`, tìm Mod muốn cài và ấn Tải Xuống.
5. **Gửi cho bạn bè:** Qua tab `Đồng Bộ Bạn Bè`, ấn nút Đóng Gói để lấy file Zip gửi cho bạn bè cài vào máy của họ.

---

## 🛠 Tác giả & Bản quyền
Phát triển bởi **Nguyễn Tấn Phong** kết hợp cùng **Google DeepMind AI**.
Mã nguồn mở miễn phí. Chúc các bạn có những giờ phút sinh tồn cùng đồng bọn thật vui vẻ! 🎮
