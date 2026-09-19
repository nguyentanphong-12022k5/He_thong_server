import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import webbrowser
import sys
import urllib.request
import urllib.parse
import json
import ssl

# Bỏ qua xác thực SSL để sửa lỗi CERTIFICATE_VERIFY_FAILED trên Windows
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

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
      ONLINE_MODE: "{online_mode}"
      PVP: "{pvp}"
      ENABLE_COMMAND_BLOCK: "{command_blocks}"
      MAX_PLAYERS: "{max_players}"
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
    image: pepaondrugs/playitgg-docker:latest
    container_name: mc-playit
    network_mode: "service:mc-server"
    volumes:
      - ./playit-data:/root/.config/playit_gg
    restart: unless-stopped
    depends_on:
      - mc-server
"""

class MinecraftServerManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minecraft Smart Server Manager")
        self.geometry("850x800") 
        self.configure(bg="#2b2b2b")
        
        # Load Icon
        try:
            if os.path.exists("icon.ico"):
                self.iconbitmap("icon.ico")
        except:
            pass
        
        self.empty_time = 0
        self.watchdog_running = False
        self.claimed_links = set()

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
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Arial", 10))
        style.configure("TCheckbutton", background="#2b2b2b", foreground="white")
        
        # === Khung Cấu hình Server (Hardware) ===
        config_frame = tk.LabelFrame(self, text=" Cấu hình Máy chủ ", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="Loại Server:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.type_var = tk.StringVar(value="PAPER")
        self.combo_type = ttk.Combobox(config_frame, textvariable=self.type_var, values=["PAPER", "FABRIC", "FORGE", "VANILLA"], state="readonly", width=15)
        self.combo_type.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(config_frame, text="Phiên bản:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.version_var = tk.StringVar(value="LATEST")
        self.combo_version = ttk.Combobox(config_frame, textvariable=self.version_var, values=["LATEST", "1.21.1", "1.20.4", "1.19.4", "1.18.2", "1.12.2"], width=15)
        self.combo_version.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        ttk.Label(config_frame, text="RAM (GB):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ram_var = tk.IntVar(value=4)
        self.scale_ram = tk.Scale(config_frame, from_=2, to=16, orient="horizontal", variable=self.ram_var, bg="#2b2b2b", fg="white", highlightthickness=0, length=200)
        self.scale_ram.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        # === Khung Cài đặt Trò chơi (Properties) ===
        prop_frame = tk.LabelFrame(self, text=" Cài đặt Trò chơi (Properties) ", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        prop_frame.pack(fill="x", padx=10, pady=5)

        self.crack_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_frame, text="Cho phép bản Crack (Online Mode = False)", variable=self.crack_var).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.pvp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_frame, text="Bật PVP (Đánh nhau)", variable=self.pvp_var).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.cmd_block_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prop_frame, text="Bật Command Blocks", variable=self.cmd_block_var).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        ttk.Label(prop_frame, text="Số người chơi tối đa:").grid(row=1, column=1, padx=10, pady=5, sticky="e")
        self.max_players_var = tk.IntVar(value=20)
        tk.Entry(prop_frame, textvariable=self.max_players_var, width=5).grid(row=1, column=2, padx=(0,10), pady=5, sticky="w")

        # === Khung Nút Bấm (Button Frame) ===
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(pady=5)

        self.btn_start = tk.Button(btn_frame, text=" Bật Server ", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=self.start_server, width=12)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(btn_frame, text=" Tắt Server ", font=("Arial", 11, "bold"), bg="#f44336", fg="white", command=self.stop_server, width=12)
        self.btn_stop.grid(row=0, column=1, padx=5)

        self.btn_mod = tk.Button(btn_frame, text=" Mở Data/Mod ", font=("Arial", 11), bg="#2196F3", fg="white", command=self.open_data_folder, width=12)
        self.btn_mod.grid(row=0, column=2, padx=5)
        
        self.btn_playit = tk.Button(btn_frame, text=" Lấy IP (Mạng) ", font=("Arial", 11), bg="#9C27B0", fg="white", command=lambda: webbrowser.open("https://playit.gg/account"), width=12)
        self.btn_playit.grid(row=0, column=3, padx=5)
        
        self.btn_store = tk.Button(btn_frame, text=" 🛒 Cửa hàng Mod ", font=("Arial", 11, "bold"), bg="#FF9800", fg="white", command=self.open_mod_store, width=15)
        self.btn_store.grid(row=0, column=4, padx=5)

        # === Khung Nhập Lệnh (Console Frame) ===
        cmd_frame = tk.Frame(self, bg="#2b2b2b")
        cmd_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(cmd_frame, text="Nhập lệnh (/):").pack(side="left", padx=(0, 5))
        self.cmd_entry = tk.Entry(cmd_frame, font=("Consolas", 11), width=45)
        self.cmd_entry.pack(side="left", padx=5)
        self.cmd_entry.bind("<Return>", lambda event: self.send_command())
        
        self.btn_send = tk.Button(cmd_frame, text="Gửi", bg="#FF9800", fg="white", font=("Arial", 9, "bold"), command=self.send_command)
        self.btn_send.pack(side="left", padx=5)

        # === Khung Hiển thị Trạng thái (Log & Player List) ===
        status_frame = tk.Frame(self, bg="#2b2b2b")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Log Box
        self.log_box = scrolledtext.ScrolledText(status_frame, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_box.pack(side="left", expand=True, fill="both", padx=(0, 5))
        
        # Player List Box
        player_frame = tk.LabelFrame(status_frame, text=" Người Chơi Online ", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        player_frame.pack(side="right", fill="y", padx=(5, 0))
        
        self.list_players = tk.Listbox(player_frame, bg="#1e1e1e", fg="yellow", font=("Consolas", 11), width=20)
        self.list_players.pack(expand=True, fill="both", padx=5, pady=5)

        # === Khung Hiệu Năng (Performance Monitor) ===
        perf_frame = tk.Frame(self, bg="#2b2b2b")
        perf_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(perf_frame, text="CPU:").pack(side="left", padx=(0, 5))
        self.cpu_bar = ttk.Progressbar(perf_frame, orient="horizontal", length=200, mode="determinate")
        self.cpu_bar.pack(side="left", padx=5)
        self.lbl_cpu = ttk.Label(perf_frame, text="0%")
        self.lbl_cpu.pack(side="left", padx=(0, 20))
        
        ttk.Label(perf_frame, text="RAM:").pack(side="left", padx=(0, 5))
        self.ram_bar = ttk.Progressbar(perf_frame, orient="horizontal", length=200, mode="determinate")
        self.ram_bar.pack(side="left", padx=5)
        self.lbl_ram = ttk.Label(perf_frame, text="0%")
        self.lbl_ram.pack(side="left", padx=5)

    def log(self, message):
        def _log():
            self.log_box.insert(tk.END, message + "\n")
            self.log_box.see(tk.END)
        self.after(0, _log)
        
    def update_player_ui(self, player_names):
        self.list_players.delete(0, tk.END)
        for name in player_names:
            if name.strip():
                self.list_players.insert(tk.END, name.strip())
                
    def update_perf_ui(self, cpu_val, ram_val):
        self.cpu_bar["value"] = min(cpu_val, 100)
        self.lbl_cpu.config(text=f"{cpu_val:.1f}%")
        self.ram_bar["value"] = min(ram_val, 100)
        self.lbl_ram.config(text=f"{ram_val:.1f}%")

    def generate_docker_compose(self):
        s_type = self.type_var.get()
        s_version = self.version_var.get()
        ram = self.ram_var.get()
        limit = ram + 1

        online_mode = "FALSE" if self.crack_var.get() else "TRUE"
        pvp = "TRUE" if self.pvp_var.get() else "FALSE"
        cmd_blocks = "TRUE" if self.cmd_block_var.get() else "FALSE"
        max_players = str(self.max_players_var.get())

        content = COMPOSE_TEMPLATE.format(
            server_type=s_type,
            server_version=s_version,
            ram_size=ram,
            ram_limit=limit,
            online_mode=online_mode,
            pvp=pvp,
            command_blocks=cmd_blocks,
            max_players=max_players
        )
        
        with open("docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"Đã cập nhật cấu hình và thuộc tính Game!")

    def start_server(self):
        self.generate_docker_compose()
        
        self.log("Đang khởi động Server qua Docker Compose...")
        self.btn_start.config(state=tk.DISABLED)
        
        def run_compose():
            try:
                process = subprocess.Popen(["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    self.log("Máy chủ đã bật thành công!")
                    
                    if not self.watchdog_running:
                        self.watchdog_running = True
                        threading.Thread(target=self.watchdog_thread, daemon=True).start()
                        threading.Thread(target=self.playit_scanner_thread, daemon=True).start()
                else:
                    self.log(f"Lỗi khi bật máy chủ:\n{stderr}")
            except Exception as e:
                self.log(f"Đã xảy ra lỗi: {e}")
            finally:
                self.btn_start.config(state=tk.NORMAL)

        threading.Thread(target=run_compose, daemon=True).start()

    def playit_scanner_thread(self):
        self.log("[Mạng] Bắt đầu quét đường dẫn Playit tự động...")
        time.sleep(5)
        try:
            process = subprocess.Popen(["docker", "logs", "-f", "mc-playit"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in process.stdout:
                if not self.watchdog_running:
                    break
                
                if "https://playit.gg/claim/" in line:
                    start = line.find("https://playit.gg/claim/")
                    end = line.find(" ", start)
                    if end == -1: end = len(line)
                    link = line[start:end].strip()
                    
                    if link not in self.claimed_links:
                        self.claimed_links.add(link)
                        self.log(f"\n[MẠNG] Đã bắt được Link xác thực Playit! Đang mở trình duyệt...\n👉 {link}\n")
                        webbrowser.open(link)
        except Exception as e:
            pass

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
                    self.after(0, self.update_player_ui, []) 
                    self.after(0, self.update_perf_ui, 0.0, 0.0)
                else:
                    self.log(f"Lỗi khi tắt:\n{stderr}")
            except Exception as e:
                self.log(f"Lỗi: {e}")
            finally:
                self.btn_stop.config(state=tk.NORMAL)
                self.watchdog_running = False

        threading.Thread(target=run_stop, daemon=True).start()
        
    def send_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
            
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
        self.log("Watchdog và Bộ giám sát hiệu năng đã khởi động...")
        self.empty_time = 0
        
        last_check_time = time.time()
        
        while self.watchdog_running:
            time.sleep(2)
            if not self.watchdog_running:
                break
                
            # Lấy thông số CPU/RAM
            try:
                stats_res = subprocess.run(["docker", "stats", "--no-stream", "--format", "json", CONTAINER_NAME], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if stats_res.stdout:
                    # Output form: {"CPUPerc":"0.05%","MemPerc":"1.2%"}
                    lines = stats_res.stdout.strip().split("\n")
                    if lines:
                        data = json.loads(lines[0])
                        cpu_perc = float(data.get("CPUPerc", "0%").strip('%'))
                        mem_perc = float(data.get("MemPerc", "0%").strip('%'))
                        self.after(0, self.update_perf_ui, cpu_perc, mem_perc)
            except Exception:
                pass
                
            # Kiểm tra số người chơi mỗi 60s
            current_time = time.time()
            if current_time - last_check_time >= 60:
                last_check_time = current_time
                try:
                    result = subprocess.run(["docker", "exec", "-i", CONTAINER_NAME, "rcon-cli", "--password", RCON_PASSWORD, "list"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    output = result.stdout.strip()
                    
                    import re
                    
                    if "players online" in output.lower() or "online:" in output.lower():
                        try:
                            # Tìm số lượng người chơi (thường nằm sau chữ 'are' hoặc đứng trước chữ 'out of' / 'of a max')
                            # Ví dụ: "There are 1 of a max of 20 players online" -> bắt số 1
                            match = re.search(r'(?:There are |online: )(\d+)', output, re.IGNORECASE)
                            if match:
                                players = int(match.group(1))
                            else:
                                # Fallback nếu không bắt được
                                players = 1 if ":" in output and len(output.split(":")[1].strip()) > 0 else 0
                                
                            # Cố gắng bắt danh sách tên người chơi sau dấu hai chấm
                            player_names = []
                            if ":" in output:
                                names_str = output.split(":", 1)[1].strip()
                                if names_str:
                                    player_names = [n.strip() for n in names_str.split(",") if n.strip()]
                            
                            self.after(0, self.update_player_ui, player_names)
                            
                            if len(player_names) == 0 and players == 0:
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
                except Exception:
                    pass

    # === Cửa hàng Mod/Plugin ===
    def open_mod_store(self):
        store_win = tk.Toplevel(self)
        store_win.title("Cửa hàng Modrinth")
        store_win.geometry("500x500")
        store_win.configure(bg="#2b2b2b")
        
        ttk.Label(store_win, text="Tìm kiếm Mod/Plugin:").pack(pady=(10, 0))
        
        search_frame = tk.Frame(store_win, bg="#2b2b2b")
        search_frame.pack(fill="x", padx=10, pady=5)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=40)
        search_entry.pack(side="left", padx=5)
        
        list_results = tk.Listbox(store_win, font=("Arial", 10), height=15)
        list_results.pack(fill="both", expand=True, padx=10, pady=5)
        
        projects = [] # Lưu project metadata
        
        def on_search():
            query = search_var.get().strip()
            if not query: return
            list_results.delete(0, tk.END)
            list_results.insert(tk.END, "Đang tìm kiếm...")
            
            def do_search():
                try:
                    url = f"https://api.modrinth.com/v2/search?query={urllib.parse.quote(query)}&limit=15"
                    req = urllib.request.Request(url, headers={'User-Agent': 'MinecraftSmartManager/1.0'})
                    with urllib.request.urlopen(req, context=ssl_ctx) as res:
                        data = json.loads(res.read().decode())
                        
                    projects.clear()
                    store_win.after(0, lambda: list_results.delete(0, tk.END))
                    for hit in data.get("hits", []):
                        projects.append(hit)
                        title = hit.get("title", "Unknown")
                        author = hit.get("author", "Unknown")
                        store_win.after(0, lambda t=title, a=author: list_results.insert(tk.END, f"{t} (bởi {a})"))
                        
                    if not projects:
                        store_win.after(0, lambda: list_results.insert(tk.END, "Không tìm thấy kết quả nào."))
                except Exception as e:
                    store_win.after(0, lambda: list_results.insert(tk.END, f"Lỗi: {e}"))
                    
            threading.Thread(target=do_search, daemon=True).start()
            
        btn_search = tk.Button(search_frame, text="Tìm", bg="#2196F3", fg="white", command=on_search)
        btn_search.pack(side="left")
        search_entry.bind("<Return>", lambda e: on_search())
        
        def on_download():
            sel = list_results.curselection()
            if not sel:
                messagebox.showinfo("Thông báo", "Vui lòng chọn 1 Mod/Plugin trong danh sách!")
                return
                
            proj = projects[sel[0]]
            proj_id = proj.get("project_id")
            proj_title = proj.get("title")
            server_type = self.type_var.get()
            
            def do_download(s_type):
                try:
                    # Lấy danh sách version
                    url = f"https://api.modrinth.com/v2/project/{proj_id}/version"
                    req = urllib.request.Request(url, headers={'User-Agent': 'MinecraftSmartManager/1.0'})
                    with urllib.request.urlopen(req, context=ssl_ctx) as res:
                        versions = json.loads(res.read().decode())
                        
                    if not versions:
                        store_win.after(0, lambda: messagebox.showerror("Lỗi", "Không tìm thấy file nào cho Project này!"))
                        return
                        
                    # Lấy file đầu tiên (mới nhất)
                    file_info = versions[0]["files"][0]
                    file_url = file_info["url"]
                    file_name = file_info["filename"]
                    
                    # Xác định thư mục
                    if s_type == "PAPER":
                        dest_dir = os.path.join("data", "plugins")
                    else:
                        dest_dir = os.path.join("data", "mods")
                        
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, file_name)
                    
                    # Tải file
                    self.log(f"[Cửa Hàng] Đang tải {proj_title}...")
                    dl_req = urllib.request.Request(file_url, headers={'User-Agent': 'MinecraftSmartManager/1.0'})
                    with urllib.request.urlopen(dl_req, context=ssl_ctx) as response, open(dest_path, 'wb') as out_file:
                        out_file.write(response.read())
                    
                    self.log(f"[Cửa Hàng] Tải thành công: {file_name} vào thư mục {dest_dir}!")
                    store_win.after(0, lambda: messagebox.showinfo("Thành công", f"Đã tải {file_name} thành công!\n(Hãy Khởi động lại Server để áp dụng)"))
                except Exception as e:
                    self.log(f"[Cửa Hàng] Lỗi tải: {e}")
                    store_win.after(0, lambda err=e: messagebox.showerror("Lỗi tải", f"Đã có lỗi xảy ra: {err}"))
            
            threading.Thread(target=do_download, args=(server_type,), daemon=True).start()
            
        btn_dl = tk.Button(store_win, text="⬇ Tải Về & Cài Đặt", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", command=on_download)
        btn_dl.pack(pady=10)

if __name__ == "__main__":
    app = MinecraftServerManager()
    app.mainloop()
