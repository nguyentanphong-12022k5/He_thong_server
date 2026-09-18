import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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

COMPOSE_TEMPLATE = """services:
  mc-server:
    image: itzg/minecraft-server
    container_name: mc-server
    environment:
      EULA: "TRUE"
      TYPE: "{server_type}"
      VERSION: "{server_version}"
      INIT_MEMORY: "1G"
      MAX_MEMORY: "{ram_size}G"
      USE_AIKAR_FLAGS: "true"
      ENABLE_RCON: "TRUE"
      RCON_PASSWORD: "super_secret_rcon_password_123"
      RCON_PORT: 25575
    ports:
      - "25565:25565"
    volumes:
      - ./data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: {ram_limit}G

  playit:
    image: ghcr.io/playit-cloud/playit-agent:latest
    container_name: mc-playit
    network_mode: "service:mc-server"
    volumes:
      - ./playit-data:/data
    restart: unless-stopped
    depends_on:
      - mc-server
"""

class MinecraftServerManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minecraft Smart Server Manager")
        self.geometry("700x600")
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
        # Style cho Label và text
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Arial", 10))
        
        # === Khung Cấu hình (Config Frame) ===
        config_frame = tk.LabelFrame(self, text=" Cấu hình Máy chủ ", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        config_frame.pack(fill="x", padx=10, pady=10)

        # Loại Server
        ttk.Label(config_frame, text="Loại Server:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.type_var = tk.StringVar(value="PAPER")
        self.combo_type = ttk.Combobox(config_frame, textvariable=self.type_var, values=["PAPER", "FABRIC", "FORGE", "VANILLA"], state="readonly", width=15)
        self.combo_type.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Phiên bản
        ttk.Label(config_frame, text="Phiên bản:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.version_var = tk.StringVar(value="LATEST")
        self.combo_version = ttk.Combobox(config_frame, textvariable=self.version_var, values=["LATEST", "1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.12.2"], width=15)
        self.combo_version.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        # RAM Slider
        ttk.Label(config_frame, text="RAM (GB):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ram_var = tk.IntVar(value=4)
        self.scale_ram = tk.Scale(config_frame, from_=2, to=16, orient="horizontal", variable=self.ram_var, bg="#2b2b2b", fg="white", highlightthickness=0, length=200)
        self.scale_ram.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        # === Khung Nút Bấm (Button Frame) ===
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(pady=5)

        self.btn_start = tk.Button(btn_frame, text=" Bật Server ", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=self.start_server, width=15)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame, text=" Tắt Server ", font=("Arial", 11, "bold"), bg="#f44336", fg="white", command=self.stop_server, width=15)
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.btn_mod = tk.Button(btn_frame, text=" Mở Data/Mod ", font=("Arial", 11), bg="#2196F3", fg="white", command=self.open_data_folder, width=15)
        self.btn_mod.grid(row=0, column=2, padx=10)

        # === Khung Nhập Lệnh (Console Frame) ===
        cmd_frame = tk.Frame(self, bg="#2b2b2b")
        cmd_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(cmd_frame, text="Nhập lệnh (/):").pack(side="left", padx=(0, 5))
        self.cmd_entry = tk.Entry(cmd_frame, font=("Consolas", 11), width=45)
        self.cmd_entry.pack(side="left", padx=5)
        self.cmd_entry.bind("<Return>", lambda event: self.send_command()) # Hỗ trợ nhấn Enter
        
        self.btn_send = tk.Button(cmd_frame, text="Gửi", bg="#FF9800", fg="white", font=("Arial", 9, "bold"), command=self.send_command)
        self.btn_send.pack(side="left", padx=5)

        # === Khung Log ===
        self.log_box = scrolledtext.ScrolledText(self, width=80, height=15, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_box.pack(padx=10, pady=10, expand=True, fill="both")

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        
    def generate_docker_compose(self):
        # Tạo nội dung docker-compose.yml dựa trên UI
        s_type = self.type_var.get()
        s_version = self.version_var.get()
        ram = self.ram_var.get()
        limit = ram + 1 # Cấp dư cho docker 1GB để khỏi crash

        content = COMPOSE_TEMPLATE.format(
            server_type=s_type,
            server_version=s_version,
            ram_size=ram,
            ram_limit=limit
        )
        
        with open("docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Đã lưu cấu hình: {s_type} {s_version} - {ram}GB RAM")

    def start_server(self):
        # 1. Ghi đè file compose
        self.generate_docker_compose()
        
        self.log("Đang khởi động Server qua Docker Compose...")
        self.btn_start.config(state=tk.DISABLED)
        self.combo_type.config(state=tk.DISABLED)
        self.combo_version.config(state=tk.DISABLED)
        self.scale_ram.config(state=tk.DISABLED)
        
        def run_compose():
            try:
                process = subprocess.Popen(["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log("Máy chủ đã bật thành công!")
                    self.log("Vui lòng xem log Playit bằng lệnh: docker logs mc-playit (nếu chưa cấu hình mạng).")
                    
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
                self.log("Gửi lệnh lưu game (save-all)...")
                subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, "save-all"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(3)
                
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
                self.watchdog_running = False
                
                # Mở khóa các tùy chọn cấu hình
                self.combo_type.config(state="readonly")
                self.combo_version.config(state="normal")
                self.scale_ram.config(state="normal")

        threading.Thread(target=run_stop, daemon=True).start()
        
    def send_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
            
        # Loại bỏ dấu / ở đầu nếu người dùng lỡ nhập
        if cmd.startswith("/"):
            cmd = cmd[1:]
            
        self.cmd_entry.delete(0, tk.END)
        self.log(f"> /{cmd}")
        
        def run_cmd():
            try:
                result = subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.stdout:
                    self.log(f"[Console] {result.stdout.strip()}")
                if result.stderr:
                    self.log(f"[Console Error] {result.stderr.strip()}")
            except Exception as e:
                self.log(f"Không thể gửi lệnh. Đảm bảo server đang chạy. Lỗi: {e}")
                
        threading.Thread(target=run_cmd, daemon=True).start()

    def open_data_folder(self):
        data_path = os.path.abspath("data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        os.startfile(data_path)

    def watchdog_thread(self):
        self.log("Watchdog (Tự động tắt) đã khởi động. Kiểm tra mỗi phút...")
        self.empty_time = 0
        
        while self.watchdog_running:
            time.sleep(60)
            if not self.watchdog_running:
                break
                
            try:
                result = subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, "list"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout
                
                if "There are" in output and "players online" in output:
                    try:
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
                pass

if __name__ == "__main__":
    app = MinecraftServerManager()
    app.mainloop()
