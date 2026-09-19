import customtkinter as ctk
import subprocess
import threading
import json
import os
import shutil
import time
import webbrowser
import re
from tkinter import messagebox, scrolledtext

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

RCON_PASSWORD = "super_secret_rcon_password_123"

COMPOSE_TEMPLATE = """services:
  mc-server:
    image: itzg/minecraft-server
    container_name: mc-server-{server_id}
    environment:
      EULA: "TRUE"
      TYPE: "{server_type}"
      VERSION: "{server_version}"
      INIT_MEMORY: "1G"
      MAX_MEMORY: "4G"
      USE_AIKAR_FLAGS: "true"
      ONLINE_MODE: "FALSE"
      ENABLE_RCON: "TRUE"
      RCON_PASSWORD: "super_secret_rcon_password_123"
      RCON_PORT: 25575
    ports:
      - "{port}:25565"
    volumes:
      - ./data:/data
    restart: unless-stopped

  playit:
    image: pepaondrugs/playitgg-docker:latest
    container_name: mc-playit-{server_id}
    network_mode: "service:mc-server"
    volumes:
      - ../../playit-data:/root/.config/playit_gg
    restart: unless-stopped
    depends_on:
      - mc-server
"""

class ServerManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, server_id, profile_data, base_dir):
        super().__init__(parent)
        self.server_id = server_id
        self.profile = profile_data
        self.instance_dir = os.path.abspath(os.path.join(base_dir, server_id))
        self.container_name = f"mc-server-{server_id}"
        self.playit_container = f"mc-playit-{server_id}"
        
        self.title(f"Quản lý: {self.profile['name']}")
        self.geometry("900x700")
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        
        self.watchdog_running = False
        self.claimed_links = set()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Thông tin chung
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        info_text = f"⚙️ {self.profile['name']}  |  Core: {self.profile['type']}  |  Version: {self.profile['version']}  |  Port: {self.profile['port']}"
        ctk.CTkLabel(header, text=info_text, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=15, pady=15)
        
        # Nút điều khiển
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=10, pady=5)
        
        self.btn_start = ctk.CTkButton(controls, text="▶ Bật Server", fg_color="#28a745", hover_color="#218838", command=self.start_server)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(controls, text="⏹ Tắt Server", fg_color="#dc3545", hover_color="#c82333", command=self.stop_server, state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        ctk.CTkButton(controls, text="📁 Mở Thư Mục", command=self.open_folder).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="🌐 Lấy IP (Playit)", fg_color="#9C27B0", hover_color="#7B1FA2", command=lambda: webbrowser.open("https://playit.gg/account")).pack(side="left", padx=5)
        
        # Console & Khung Log
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_box = scrolledtext.ScrolledText(log_frame, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 11))
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        
        cmd_frame = ctk.CTkFrame(self, fg_color="transparent")
        cmd_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cmd_frame, text="Lệnh (RCON):").pack(side="left")
        self.cmd_entry = ctk.CTkEntry(cmd_frame, width=500, font=ctk.CTkFont(family="Consolas"))
        self.cmd_entry.pack(side="left", padx=10)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        ctk.CTkButton(cmd_frame, text="Gửi", width=60, command=self.send_command).pack(side="left")
        
        # Hiệu năng
        perf_frame = ctk.CTkFrame(self, fg_color="transparent")
        perf_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(perf_frame, text="CPU:").pack(side="left", padx=5)
        self.cpu_bar = ctk.CTkProgressBar(perf_frame, width=200)
        self.cpu_bar.set(0)
        self.cpu_bar.pack(side="left", padx=5)
        self.lbl_cpu = ctk.CTkLabel(perf_frame, text="0%")
        self.lbl_cpu.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(perf_frame, text="RAM:").pack(side="left", padx=5)
        self.ram_bar = ctk.CTkProgressBar(perf_frame, width=200)
        self.ram_bar.set(0)
        self.ram_bar.pack(side="left", padx=5)
        self.lbl_ram = ctk.CTkLabel(perf_frame, text="0%")
        self.lbl_ram.pack(side="left", padx=5)

    def log(self, message):
        def _log():
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
        self.after(0, _log)
        
    def open_folder(self):
        os.startfile(self.instance_dir)
        
    def generate_compose(self):
        content = COMPOSE_TEMPLATE.format(
            server_id=self.server_id,
            server_type=self.profile['type'],
            server_version=self.profile['version'],
            port=self.profile['port']
        )
        with open(os.path.join(self.instance_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
            f.write(content)

    def start_server(self):
        self.btn_start.configure(state="disabled")
        self.generate_compose()
        self.log("Đang khởi động Server qua Docker Compose...")
        
        def run_compose():
            try:
                process = subprocess.Popen(["docker-compose", "up", "-d"], cwd=self.instance_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log("Khởi động thành công! Server đang chạy ngầm.")
                    self.after(0, lambda: self.btn_stop.configure(state="normal"))
                    
                    if not self.watchdog_running:
                        self.watchdog_running = True
                        threading.Thread(target=self.watchdog_thread, daemon=True).start()
                        threading.Thread(target=self.playit_scanner_thread, daemon=True).start()
                else:
                    self.log(f"Lỗi: {stderr}")
                    self.after(0, lambda: self.btn_start.configure(state="normal"))
            except Exception as e:
                self.log(f"Lỗi hệ thống: {e}")
                self.after(0, lambda: self.btn_start.configure(state="normal"))
                
        threading.Thread(target=run_compose, daemon=True).start()

    def playit_scanner_thread(self):
        self.log("[Mạng] Đang quét link Playit...")
        time.sleep(5)
        try:
            process = subprocess.Popen(["docker", "logs", "-f", self.playit_container], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in process.stdout:
                if not self.watchdog_running: break
                if "https://playit.gg/claim/" in line:
                    start = line.find("https://playit.gg/claim/")
                    end = line.find(" ", start)
                    link = line[start:end].strip() if end != -1 else line[start:].strip()
                    
                    if link not in self.claimed_links:
                        self.claimed_links.add(link)
                        self.log(f"\n[MẠNG] Đã bắt được Link xác thực Playit! Mở trình duyệt...\n👉 {link}\n")
                        webbrowser.open(link)
        except Exception:
            pass

    def stop_server(self):
        self.btn_stop.configure(state="disabled")
        self.log("Đang lưu game và tắt máy chủ...")
        
        def run_stop():
            try:
                subprocess.run(["docker", "exec", "-i", self.container_name, "rcon-cli", "--password", RCON_PASSWORD, "save-all"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(3)
                process = subprocess.Popen(["docker-compose", "stop"], cwd=self.instance_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                process.communicate()
                self.log("Máy chủ đã được tắt an toàn.")
            except Exception as e:
                self.log(f"Lỗi: {e}")
            finally:
                self.watchdog_running = False
                self.after(0, lambda: self.btn_start.configure(state="normal"))
                self.after(0, lambda: self.cpu_bar.set(0))
                self.after(0, lambda: self.ram_bar.set(0))
                self.after(0, lambda: self.lbl_cpu.configure(text="0%"))
                self.after(0, lambda: self.lbl_ram.configure(text="0%"))
                
        threading.Thread(target=run_stop, daemon=True).start()

    def send_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        if cmd.startswith("/"): cmd = cmd[1:]
        self.cmd_entry.delete(0, 'end')
        self.log(f"> /{cmd}")
        
        def run_cmd():
            try:
                res = subprocess.run(["docker", "exec", "-i", self.container_name, "rcon-cli", "--password", RCON_PASSWORD, cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if res.stdout: self.log(f"[Console] {res.stdout.strip()}")
            except Exception as e:
                self.log(f"Không thể gửi lệnh: {e}")
                
        threading.Thread(target=run_cmd, daemon=True).start()

    def watchdog_thread(self):
        while self.watchdog_running:
            time.sleep(2)
            if not self.watchdog_running: break
            
            try:
                stats_res = subprocess.run(["docker", "stats", "--no-stream", "--format", "json", self.container_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if stats_res.stdout:
                    lines = stats_res.stdout.strip().split("\n")
                    if lines:
                        data = json.loads(lines[0])
                        cpu_perc = float(data.get("CPUPerc", "0%").strip('%'))
                        mem_perc = float(data.get("MemPerc", "0%").strip('%'))
                        
                        def update_perf(c, r):
                            self.cpu_bar.set(min(c/100, 1.0))
                            self.lbl_cpu.configure(text=f"{c:.1f}%")
                            self.ram_bar.set(min(r/100, 1.0))
                            self.lbl_ram.configure(text=f"{r:.1f}%")
                        self.after(0, update_perf, cpu_perc, mem_perc)
            except Exception:
                pass


class MinecraftManagerV2(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Minecraft Smart Manager V2")
        self.geometry("1100x750")
        
        try:
            if os.path.exists("icon.ico"):
                self.iconbitmap("icon.ico")
        except:
            pass

        self.base_dir = "instances"
        self.db_path = "profiles.json"
        os.makedirs(self.base_dir, exist_ok=True)
        self.profiles = self.load_profiles()

        self.setup_ui()
        self.check_prerequisites()

    def load_profiles(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
        
    def save_profiles(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=4)

    def check_prerequisites(self):
        def do_check():
            issues = []
            try:
                res = subprocess.run(["docker", "info"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if res.returncode != 0:
                    issues.append("- Docker Desktop chưa được khởi động. Vui lòng bật Docker Desktop.")
            except FileNotFoundError:
                issues.append("- Chưa cài đặt Docker Desktop. Hệ thống yêu cầu Docker để chạy.")
                
            if issues:
                msg = "Phát hiện lỗi môi trường:\n" + "\n".join(issues) + "\n\n(Vui lòng lên Google tải Docker Desktop nếu bạn chưa có!)"
                self.after(0, lambda: messagebox.showwarning("Thiếu Điều Kiện", msg))
        
        threading.Thread(target=do_check, daemon=True).start()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ============ SIDEBAR ============
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Smart Manager\nV2", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="🖥️ Trang Chủ (Servers)", command=lambda: self.select_frame("dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_modstore = ctk.CTkButton(self.sidebar_frame, text="📦 Kho Mod / Plugins", command=lambda: self.select_frame("modstore"))
        self.btn_modstore.grid(row=2, column=0, padx=20, pady=10)

        self.btn_clientsync = ctk.CTkButton(self.sidebar_frame, text="🔄 Đồng bộ Client", command=lambda: self.select_frame("clientsync"))
        self.btn_clientsync.grid(row=3, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙️ Cài đặt", command=lambda: self.select_frame("settings"))
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)

        # ============ MAIN CONTENT FRAMES ============
        self.frames = {}

        # 1. Dashboard Frame
        self.dashboard_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.frames["dashboard"] = self.dashboard_frame
        
        self.lbl_dash = ctk.CTkLabel(self.dashboard_frame, text="Quản lý Các Máy Chủ (Multi-Server)", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_dash.pack(pady=(20, 10), padx=20, anchor="w")
        
        self.btn_new_server = ctk.CTkButton(self.dashboard_frame, text="+ Tạo Server Mới", font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", command=self.create_server_dialog)
        self.btn_new_server.pack(pady=10, padx=20, anchor="w")

        self.server_list_scroll = ctk.CTkScrollableFrame(self.dashboard_frame, corner_radius=10)
        self.server_list_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_server_list()

        # 2. Dummy Frames
        for name, title in [("modstore", "Cửa Hàng Mod & Modpacks"), ("clientsync", "Đồng Bộ Mod Client-Side"), ("settings", "Cài Đặt Hệ Thống")]:
            frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
            lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=24, weight="bold"))
            lbl.pack(pady=20, padx=20, anchor="w")
            ctk.CTkLabel(frame, text="Tính năng đang được phát triển...").pack(pady=10)
            self.frames[name] = frame

        self.select_frame("dashboard")

    def select_frame(self, name):
        for f in self.frames.values():
            f.grid_forget()
            
        self.btn_dashboard.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "dashboard" else "transparent")
        self.btn_modstore.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "modstore" else "transparent")
        self.btn_clientsync.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "clientsync" else "transparent")
        self.btn_settings.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "settings" else "transparent")
        
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def refresh_server_list(self):
        for widget in self.server_list_scroll.winfo_children():
            widget.destroy()
            
        if not self.profiles:
            ctk.CTkLabel(self.server_list_scroll, text="Chưa có máy chủ nào được tạo. Hãy bấm Tạo Server Mới!").pack(pady=30)
            return
            
        for s_id, data in self.profiles.items():
            card = ctk.CTkFrame(self.server_list_scroll, corner_radius=8, border_width=2, border_color="#333333")
            card.pack(fill="x", padx=10, pady=10)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
            
            ctk.CTkLabel(info_frame, text=data.get("name", "Unknown Server"), font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
            desc = f"Loại: {data.get('type')} | Phiên bản: {data.get('version')} | Port: {data.get('port')}"
            ctk.CTkLabel(info_frame, text=desc, text_color="gray").pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=15, pady=15)
            
            # Start and Manage combined into "Quản lý"
            ctk.CTkButton(btn_frame, text="⚙️ Quản Lý Server", width=120, fg_color="#007bff", hover_color="#0056b3", command=lambda i=s_id: self.open_server_manager(i)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="🗑 Xóa", width=80, fg_color="#dc3545", hover_color="#c82333", command=lambda i=s_id: self.delete_server(i)).pack(side="left", padx=5)

    def open_server_manager(self, server_id):
        profile = self.profiles[server_id]
        ServerManagerWindow(self, server_id, profile, self.base_dir)

    def create_server_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tạo Máy Chủ Mới")
        dialog.geometry("400x500")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="Tên Máy Chủ:").pack(pady=(20, 5), padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(padx=20, anchor="w")
        
        ctk.CTkLabel(dialog, text="Loại Server (Core):").pack(pady=(15, 5), padx=20, anchor="w")
        type_var = ctk.StringVar(value="PAPER")
        type_menu = ctk.CTkOptionMenu(dialog, variable=type_var, values=["PAPER", "FORGE", "FABRIC", "VANILLA"])
        type_menu.pack(padx=20, anchor="w")
        
        ctk.CTkLabel(dialog, text="Phiên bản:").pack(pady=(15, 5), padx=20, anchor="w")
        version_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Ví dụ: 1.20.4, LATEST")
        version_entry.pack(padx=20, anchor="w")
        
        ctk.CTkLabel(dialog, text="Cổng (Port) Minecraft:").pack(pady=(15, 5), padx=20, anchor="w")
        port_entry = ctk.CTkEntry(dialog, width=300)
        port_entry.insert(0, str(25565 + len(self.profiles))) 
        port_entry.pack(padx=20, anchor="w")
        
        def save():
            name = name_entry.get().strip()
            if not name: return
            
            s_id = name.lower().replace(" ", "_")
            if s_id in self.profiles:
                messagebox.showerror("Lỗi", "Tên máy chủ này đã tồn tại!")
                return
                
            self.profiles[s_id] = {
                "name": name,
                "type": type_var.get(),
                "version": version_entry.get().strip() or "LATEST",
                "port": port_entry.get().strip() or "25565",
                "created_at": time.time()
            }
            
            os.makedirs(os.path.join(self.base_dir, s_id, "data"), exist_ok=True)
            self.save_profiles()
            self.refresh_server_list()
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Tạo Mới", command=save, fg_color="#28a745", hover_color="#218838").pack(pady=30)

    def delete_server(self, s_id):
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa máy chủ '{self.profiles[s_id]['name']}' không?\n(Dữ liệu trong thư mục sẽ bị xóa vĩnh viễn)"):
            path = os.path.join(self.base_dir, s_id)
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
                
            del self.profiles[s_id]
            self.save_profiles()
            self.refresh_server_list()

if __name__ == "__main__":
    app = MinecraftManagerV2()
    app.mainloop()
