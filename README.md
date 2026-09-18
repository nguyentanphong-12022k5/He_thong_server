# Minecraft Smart Server Management (Bản Chuẩn - V3)

Hệ thống quản lý máy chủ Minecraft tự động với giao diện trực quan (GUI) thân thiện dành cho Windows. Hệ thống sử dụng Docker để cô lập môi trường, tự động hóa mọi thiết lập (RAM, Properties) và tích hợp mạng xuyên NAT Playit.gg siêu tiện lợi.

## Tính năng nổi bật
1. **Giao diện App (GUI) Toàn năng**: Không cần đụng vào file code! Chọn Loại Server (Paper/Forge/Fabric), Phiên bản, RAM và Các thuộc tính Game (Crack, PVP, Max Players) ngay trên App.
2. **Auto-Playit (Tự bắt Link Mạng)**: App sẽ tự đọc Log và **mở trình duyệt web xác thực** ngay khi Playit.gg sẵn sàng.
3. **Bảng Điều Khiển Console (Khung Lệnh)**: Gõ lệnh trực tiếp vào Server (như `/op`, `/time`) thông qua ô nhập lệnh trên giao diện.
4. **Watchdog Thông Minh**: Tự động giám sát số lượng người chơi và tự động lưu Map rồi tắt máy chủ nếu không có ai chơi trong 20 phút.

---

## 📖 Hướng Dẫn Sử Dụng (Từ A - Z)

### Bước 1: Yêu cầu bắt buộc (Prerequisites)
- Máy tính chạy Windows 10/11.
- Máy tính (người làm Host) **BẮT BUỘC** phải cài đặt phần mềm **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** và đang bật nó chạy ngầm.

### Bước 2: Khởi chạy Ứng dụng Quản lý (App)
Nếu bạn nhận được file nén chứa `manager_app.exe` và `docker-compose.yml`, hãy để chúng ở chung một thư mục.
- Click đúp vào file **`manager_app.exe`** để mở bảng điều khiển.

### Bước 3: Cấu hình Server (Chỉ 5 giây)
Trên giao diện App:
1. Chọn **Loại Server** (Ví dụ: `PAPER` nếu muốn cài Plugin, `FORGE` nếu cài Mod nặng).
2. Chọn **Phiên bản** (Ví dụ: `1.20.4`).
3. Kéo thanh **RAM** (Khuyến nghị để 4GB trở lên).
4. **Cài đặt Game (Properties):** 
   - Nếu bạn và bạn bè chơi qua TLauncher/Legacy Launcher (Crack), **BẮT BUỘC phải TÍCH vào ô "Cho phép bản Crack (Online Mode = False)"**.
5. Bấm nút **Bật Server** (Màu Xanh).

### Bước 4: Mở Mạng cho Bạn Bè (Playit.gg)
1. Sau khi bấm Bật Server, hãy chờ khoảng 1-2 phút. Khung Log của App sẽ báo `[Mạng] Bắt đầu quét...`
2. Vài giây sau, **trình duyệt Web của bạn sẽ tự động bật lên** trang `playit.gg`.
3. Bạn tiến hành Đăng nhập (hoặc Đăng ký) tài khoản Playit.
4. Chọn "Add Agent" -> Làm theo chỉ dẫn để lấy được địa chỉ IP Tĩnh dạng chữ (Ví dụ: `hoat-hinh.auto.playit.gg`).
*(Lưu ý: App lưu cấu hình mạng vào thư mục `playit-data`. Lần sau bật lại App, bạn sẽ không cần phải quét hay xác thực link nữa, IP tĩnh vẫn giữ nguyên).*

### Bước 5: Cách vào Game (Dành cho bản Crack/Legacy Launcher)
1. Mở phần mềm Legacy Launcher.
2. Ở ô Tên người dùng, nhập tên viết liền không dấu (Vd: `TuanMinh99`).
3. Ở ô Phiên bản, hãy chọn phiên bản **khớp chính xác 100%** với cấu hình bạn chọn ở Bước 3. (Vd: Ở App chọn FORGE 1.20.4 thì Legacy cũng phải chọn Forge 1.20.4).
4. Vào Game -> Multiplayer (Chơi mạng) -> Add Server (Thêm máy chủ).
5. Dán địa chỉ IP Tĩnh (`hoat-hinh.auto.playit.gg`) vào ô Server Address và vào chơi!

---

## 🛠 Hướng dẫn cho Lập Trình Viên (Cách Build file .exe)

Nếu bạn có mã nguồn gốc (`manager_app.py`, `build.bat`) và muốn tự đóng gói ra file `.exe`:

1. Máy tính cần cài đặt sẵn **Python**.
2. Click đúp vào file **`build.bat`**.
3. Hệ thống sẽ tự cài `PyInstaller` và biên dịch mã nguồn.
4. Sau khi xong, vào thư mục `dist`, bạn sẽ thấy file `.exe` của mình ở đó. Copy nó ra ngoài và gửi cho bạn bè (nhớ gửi kèm file `docker-compose.yml`).
