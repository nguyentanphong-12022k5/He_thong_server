import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import time
import os
import webbrowser
import sys

# Cấu hình Watchdog
MAX_EMPTY_TIME = 20  # phút
RCON_PASSWORD = "super_secret_rcon_password_123"
CONTAINER_NAME = "mc-server"

class MinecraftServerManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minecraft Smart Server Manager")
        self.geometry("600x400")
        self.configure(bg="#2b2b2b")
        
        self.empty_time = 0
        self.watchdog_running = False

        self.create_widgets()
        self.check_docker()

    def check_docker(self):
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log("Docker đã được cài đặt và sẵn sàng.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("LỖI: Không tìm thấy Docker trên hệ thống!")
            response = messagebox.askyesno("Thiếu Docker", 
                                           "Ứng dụng yêu cầu Docker Desktop để chạy máy chủ.\nBạn có muốn tải Docker Desktop ngay bây giờ không?")
            if response:
                webbrowser.open("https://www.docker.com/products/docker-desktop/")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.DISABLED)

    def create_widgets(self):
        # Frame Buttons
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(btn_frame, text=" Bật Server ", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.start_server)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame, text=" Tắt Server ", font=("Arial", 12, "bold"), bg="#f44336", fg="white", command=self.stop_server)
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.btn_mod = tk.Button(btn_frame, text=" Mở Thư mục Mod/Data ", font=("Arial", 12), bg="#2196F3", fg="white", command=self.open_data_folder)
        self.btn_mod.grid(row=0, column=2, padx=10)

        # Log Text Box
        self.log_box = scrolledtext.ScrolledText(self, width=70, height=15, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_box.pack(padx=10, pady=10)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def start_server(self):
        self.log("Đang khởi động Server qua Docker Compose...")
        self.btn_start.config(state=tk.DISABLED)
        
        def run_compose():
            try:
                # Chạy docker-compose up
                process = subprocess.Popen(["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log("Máy chủ đã bật thành công!")
                    self.log("Vui lòng xem log mc-playit bằng lệnh: docker logs mc-playit để lấy link cấu hình mạng.")
                    
                    # Bắt đầu Watchdog
                    if not self.watchdog_running:
                        self.watchdog_running = True
                        threading.Thread(target=self.watchdog_thread, daemon=True).start()
                else:
                    self.log(f"Lỗi khi bật máy chủ:\n{stderr}")
            except Exception as e:
                self.log(f"Đã xảy ra lỗi: {e}")
            finally:
                self.btn_start.config(state=tk.NORMAL)

        threading.Thread(target=run_compose, daemon=True).start()

    def stop_server(self):
        self.log("Đang tiến hành lưu map và tắt server...")
        self.btn_stop.config(state=tk.DISABLED)
        
        def run_stop():
            try:
                # Gửi lệnh save-all trước nếu container đang chạy
                self.log("Gửi lệnh lưu game (save-all)...")
                subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, "save-all"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(3)
                
                # Tắt docker-compose
                self.log("Đang dừng Docker container...")
                process = subprocess.Popen(["docker-compose", "stop"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log("Đã tắt máy chủ thành công!")
                else:
                    self.log(f"Lỗi khi tắt:\n{stderr}")
            except Exception as e:
                self.log(f"Lỗi: {e}")
            finally:
                self.btn_stop.config(state=tk.NORMAL)
                self.watchdog_running = False # Dừng watchdog

        threading.Thread(target=run_stop, daemon=True).start()

    def open_data_folder(self):
        # Tạo thư mục data nếu chưa có
        data_path = os.path.abspath("data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        os.startfile(data_path)

    def watchdog_thread(self):
        self.log("Watchdog (Tự động tắt) đã khởi động. Kiểm tra mỗi phút...")
        self.empty_time = 0
        
        while self.watchdog_running:
            time.sleep(60) # Chờ 1 phút
            if not self.watchdog_running:
                break
                
            try:
                # Gọi rcon-cli trong container
                result = subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, "list"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout
                
                # output có dạng "There are 0 of a max of 20 players online: "
                if "There are" in output and "players online" in output:
                    try:
                        # Lấy số lượng người chơi
                        parts = output.split(" ")
                        players = int(parts[2])
                        
                        if players == 0:
                            self.empty_time += 1
                            self.log(f"[Watchdog] Server đang trống ({self.empty_time}/{MAX_EMPTY_TIME} phút).")
                            
                            if self.empty_time >= MAX_EMPTY_TIME:
                                self.log("[Watchdog] Đã quá thời gian trống cho phép. Tự động tắt server!")
                                self.stop_server()
                                break
                        else:
                            if self.empty_time > 0:
                                self.log(f"[Watchdog] Có {players} người chơi. Đã reset bộ đếm.")
                            self.empty_time = 0
                    except ValueError:
                        pass
            except Exception as e:
                pass # Bỏ qua lỗi nếu container chưa chạy hẳn

if __name__ == "__main__":
    app = MinecraftServerManager()
    app.mainloop()
