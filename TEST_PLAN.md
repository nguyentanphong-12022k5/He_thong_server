# Test Plan & Checklist - Minecraft Smart Server Management

Bảng checklist dưới đây giúp kiểm thử đảm bảo hệ thống hoạt động đúng theo các yêu cầu đề ra.

## 1. Triển khai & Cấu trúc (Docker)
- [ ] Lệnh `start-server.sh` (hoặc `docker-compose up -d`) khởi chạy thành công, không báo lỗi.
- [ ] Container `mc-server` và `mc-playit` đang ở trạng thái `Running`.
- [ ] Thư mục `data/` (chứa dữ liệu server) và `playit-data/` được tự động sinh ra trong thư mục host.
- [ ] File `eula.txt` trong thư mục `data/` được tự động set `true`.

## 2. Quản lý Mod/Plugin
- [ ] **Kiểm tra Plugin (Paper):** 
  - Đặt một file plugin .jar (ví dụ: ClearLag) vào `data/plugins/`.
  - Khởi động lại `mc-server`.
  - Vào game, gõ lệnh `/plugins` và xác nhận plugin hiển thị màu xanh lá cây.
- [ ] **Kiểm tra đổi loại Server:**
  - Sửa biến `TYPE` trong `docker-compose.yml` thành `FABRIC`.
  - Xóa hoặc di chuyển thư mục `data/` (để tránh xung đột map nếu cần).
  - Khởi động lại và kiểm tra log xem Fabric loader có được tải không.

## 3. Mạng và Kết nối (Playit.gg Tunnel)
- [ ] Đọc log `mc-playit` (`docker logs mc-playit`) và claim link thành công trên Playit.gg.
- [ ] Host 1 (Máy tính chạy Docker) và Host 2 (Máy tính người chơi kết nối qua 4G/Wifi khác mạng).
- [ ] Người chơi (Host 2) thêm địa chỉ IP do Playit.gg cung cấp vào phần Multiplayer.
- [ ] Người chơi đăng nhập thành công vào server, không bị timeout hoặc lỗi connection.
- [ ] Người chơi không bị lag bất thường so với ping mạng chuẩn.

## 4. Cơ chế Watchdog (Auto-shutdown)
- [ ] Kiểm tra tiến trình watchdog có chạy dưới nền không (`ps aux | grep watchdog`).
- [ ] Mở log watchdog (`tail -f watchdog.log`), đảm bảo watchdog có thể query số lượng người chơi (không báo lỗi auth RCON).
- [ ] **Test Reset bộ đếm:** Có một người chơi trong game. Theo dõi log watchdog, đảm bảo nó hiển thị "Có 1 người chơi. Reset bộ đếm thời gian."
- [ ] **Test Auto-shutdown:**
  - Đảm bảo server trống (0 người chơi).
  - Cài đặt tạm thời biến `MAX_EMPTY_TIME` trong `watchdog.sh` thành `2` phút thay vì 20 phút để test nhanh.
  - Sau 2 phút trống, quan sát log Minecraft xem có nhận được thông báo "Saved the game" hay không.
  - Quan sát trạng thái container (`docker ps`), đảm bảo cả `mc-server` và `mc-playit` đều đã ngừng (Exited).
