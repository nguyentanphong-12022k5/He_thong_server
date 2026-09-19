import customtkinter as ctk
import subprocess
import threading
import json
import os
import shutil
import time
from tkinter import messagebox

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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

        # Data initialization
        self.base_dir = "instances"
        self.db_path = "profiles.json"
        os.makedirs(self.base_dir, exist_ok=True)
        self.profiles = self.load_profiles()
        
        self.current_profile = None

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
                
            try:
                wsl = subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if wsl.returncode == 0 and "docker-desktop" not in wsl.stdout:
                    issues.append("- WSL2 Backend chưa được cấu hình cho Docker.")
            except FileNotFoundError:
                pass # Not all windows machines have wsl command easily accessible, or it might be older windows.
                
            if issues:
                msg = "Phát hiện lỗi môi trường:\n" + "\n".join(issues)
                self.after(0, lambda: messagebox.showwarning("Thiếu Điều Kiện", msg))
        
        threading.Thread(target=do_check, daemon=True).start()

    def setup_ui(self):
        # Configure Grid Layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ============ SIDEBAR ============
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Spacer

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
        
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Chế độ màu:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

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

        # 2. Placeholder for others
        for name, title in [("modstore", "Cửa Hàng Mod & Modpacks"), ("clientsync", "Đồng Bộ Mod Client-Side"), ("settings", "Cài Đặt Hệ Thống")]:
            frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
            lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=24, weight="bold"))
            lbl.pack(pady=20, padx=20, anchor="w")
            ctk.CTkLabel(frame, text="Tính năng đang được phát triển...").pack(pady=10)
            self.frames[name] = frame

        # Bật tab mặc định
        self.select_frame("dashboard")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def select_frame(self, name):
        for f in self.frames.values():
            f.grid_forget()
            
        # Reset buttons color
        self.btn_dashboard.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "dashboard" else "transparent")
        self.btn_modstore.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "modstore" else "transparent")
        self.btn_clientsync.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "clientsync" else "transparent")
        self.btn_settings.configure(fg_color=["#3B8ED0", "#1F6AA5"] if name == "settings" else "transparent")
        
        # Show selected frame
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
            
            ctk.CTkButton(btn_frame, text="▶ Khởi động", width=100, fg_color="#28a745", hover_color="#218838").pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="⚙️ Quản lý", width=100).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="🗑 Xóa", width=80, fg_color="#dc3545", hover_color="#c82333", command=lambda i=s_id: self.delete_server(i)).pack(side="left", padx=5)

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
        port_entry.insert(0, str(25565 + len(self.profiles))) # Auto increment port
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
