# Minecraft Smart Server Management (App Edition)

Hệ thống quản lý máy chủ Minecraft tự động với giao diện trực quan (GUI) trên Windows. Hệ thống sử dụng Docker để cô lập môi trường, hỗ trợ kết nối mạng vượt NAT (qua Playit.gg) và tự động tắt khi không có người chơi.

## Tính năng chính
1. **Giao diện App (GUI)**: Mọi thao tác Bật/Tắt server, xem log, mở thư mục Mod đều được thực hiện qua một cửa sổ ứng dụng duy nhất, không cần gõ lệnh.
2. **Kiểm tra Docker thông minh**: Tự động cảnh báo và dẫn link tải Docker Desktop nếu người dùng chưa cài đặt.
3. **Quản lý Mod/Plugin**: Hỗ trợ Paper, Fabric, Forge. Mở nhanh thư mục mod từ giao diện App.
4. **Kết nối Cross-Network**: Sử dụng [Playit.gg](https://playit.gg) để mở mạng ra ngoài mà không cần cấu hình Port Forwarding.
5. **Auto-shutdown (Watchdog)**: App chạy ngầm tính năng kiểm tra người chơi. Nếu server trống liên tục 20 phút, App sẽ tự động lưu map (save-all) và tắt hệ thống để tiết kiệm tài nguyên.

---

## 1. Yêu cầu hệ thống
- Hệ điều hành: Windows 10/11.
- Phần mềm: **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Bắt buộc phải cài và đang mở chạy ngầm).

## 2. Hướng dẫn sử dụng App

Nếu bạn nhận được file nén chứa `manager_app.exe` và `docker-compose.yml`, hãy làm theo các bước sau:

1. Chạy phần mềm Docker Desktop trên máy tính của bạn trước.
2. Click đúp vào file **`manager_app.exe`** để mở bảng điều khiển (Control Panel).
3. Bấm nút **Bật Server** (Màu xanh). Đợi một lúc để hệ thống tự động tải dữ liệu và khởi động.
4. Quan sát khung Log. Ở lần chạy đầu tiên, bạn sẽ thấy một thông báo yêu cầu xác thực Playit.gg. 
   - Hãy copy đường link xác thực đó và dán vào trình duyệt web.
   - Đăng nhập/Đăng ký Playit.gg và cấu hình mạng (như cấp IP tĩnh `tencuaban.auto.playit.gg`).
   - Gửi IP này cho bạn bè để họ vào game.

## 3. Quản lý Mod/Plugin và Dữ liệu
Toàn bộ map (world), mod, và plugin được lưu trực tiếp vào thư mục `data` nằm chung chỗ với file App.

1. Từ giao diện App, bấm nút **Mở Thư mục Mod/Data** (Màu xanh dương).
2. Tùy thuộc vào loại server (Paper/Fabric/Forge) được thiết lập trong file `docker-compose.yml`, bạn hãy thả các file `.jar` vào thư mục `data/plugins/` hoặc `data/mods/`.
3. Nếu muốn đổi loại server (VD: từ Paper sang Fabric):
   - Mở file `docker-compose.yml` bằng Notepad.
   - Tìm dòng `TYPE: PAPER` và đổi thành `TYPE: FABRIC`.
   - Tắt server và bật lại từ App.

## 4. Dành cho lập trình viên (Cách Build file .exe)

Nếu bạn có mã nguồn gốc (`manager_app.py`, `build.bat`) và muốn tự xuất ra file `.exe`:

1. Máy tính cần cài đặt sẵn **Python** (Check mục "Add to PATH" khi cài).
2. Click đúp vào file **`build.bat`**.
3. Kịch bản sẽ tự tải thư viện `PyInstaller` và biên dịch mã nguồn.
4. Sau khi xong, vào thư mục `dist` mới xuất hiện, bạn sẽ thấy file `.exe` của mình ở đó. Copy nó ra ngoài và gửi cho bạn bè (cùng với `docker-compose.yml`).
