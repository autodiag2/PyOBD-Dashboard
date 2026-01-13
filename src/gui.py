import customtkinter as ctk
import json
import os
import time
from tkinter import filedialog, messagebox
from collections import deque 

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_logger import DataLogger
from config_manager import ConfigManager
from diagnostic_engine import DiagnosticEngine

# --- 1. DEFINE STANDARD (FREE) SENSORS ---
STANDARD_SENSORS = {
    "RPM": ("Engine RPM", "", True, True, 6000),
    "SPEED": ("Vehicle Speed", "km/h", True, True, 160),
    "COOLANT_TEMP": ("Coolant Temp", "°C", True, True, 120),
    "CONTROL_MODULE_VOLTAGE": ("Voltage", "V", True, False, 16),
    "ENGINE_LOAD": ("Engine Load", "%", True, False, 100),
    "THROTTLE_POS": ("Throttle Pos", "%", False, True, 100),
    "INTAKE_TEMP": ("Intake Air Temp", "°C", False, False, 80),
    "MAF": ("MAF Air Flow", "g/s", False, False, 200),
    "FUEL_LEVEL": ("Fuel Level", "%", False, False, 100),
    "BAROMETRIC_PRESSURE": ("Barometric", "kPa", False, False, 200),
    "TIMING_ADVANCE": ("Timing Adv", "°", False, False, 60),
    "RUN_TIME": ("Run Time", "sec", False, False, 3600)
}

PRO_PACK_DIR = "pro_packs"

class DashboardApp(ctk.CTk):
    def __init__(self, obd_handler):
        super().__init__()
        self.obd = obd_handler
        self.logger = DataLogger()
        self.obd.log_callback = self.append_debug_log
        
        self.config = ConfigManager.load_config()
        self.sensor_state = {} 
        self.available_sensors = {}
        self.sensor_sources = {} 
        self.dashboard_dirty = False 

        # GRAPH DATA STORAGE 
        self.history_rpm = deque([0]*60, maxlen=60)
        self.history_speed = deque([0]*60, maxlen=60)

        # Window Setup
        self.title("PyOBD Professional - Performance Edition")
        self.geometry("1100x800") 
        ctk.set_appearance_mode("dark")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_dash = self.tabview.add("Dashboard")
        self.tab_graph = self.tabview.add("Live Graph")
        self.tab_diag = self.tabview.add("Diagnostics")
        self.tab_settings = self.tabview.add("Settings")
        self.tab_debug = self.tabview.add("Debug Log")
        
        # 1. Load Sensors
        self.reload_sensor_definitions()

        # 2. UI Setup
        self._setup_dashboard_tab()
        self._setup_graph_tab()
        self._setup_diagnostics_tab()
        self._setup_settings_tab()
        self._setup_debug_tab()
        
        if "log_dir" in self.config:
            self.logger.set_directory(self.config["log_dir"])
            self.lbl_path.configure(text=f"Save Path: {self.logger.log_dir}")
        
        self.rebuild_dashboard_grid()
        self.update_loop()

    # --- SENSOR LOADING LOGIC ---
    def reload_sensor_definitions(self):
        """Rebuilds the master sensor list"""
        self.available_sensors = STANDARD_SENSORS.copy()
        self.sensor_sources = {k: "Standard" for k in STANDARD_SENSORS}
        
        enabled_packs = self.config.get("enabled_packs", [])
        
        if os.path.exists(PRO_PACK_DIR):
            for root, dirs, files in os.walk(PRO_PACK_DIR):
                for f in files:
                    if f.endswith(".json"):
                        full = os.path.join(root, f)
                        rel = os.path.relpath(full, PRO_PACK_DIR)
                        
                        # Normalize path separators for config compatibility
                        # (Windows uses \, Config might store /)
                        # We just check if the relative path ends with the stored config string
                        # or direct match
                        
                        match = False
                        for p in enabled_packs:
                            if os.path.normpath(p) == os.path.normpath(rel):
                                match = True
                                break
                        
                        if match:
                            try:
                                with open(full, 'r') as json_file:
                                    pro_data = json.load(json_file)
                                    for key, val in pro_data.items():
                                        self.available_sensors[key] = tuple(val[:5])
                                        self.sensor_sources[key] = rel # Tag source
                                    print(f"Loaded Pack: {rel}")
                            except Exception as e:
                                print(f"Error loading {rel}: {e}")
        
        self.obd.set_pro_definitions(self.available_sensors)
        self._init_sensor_state()

    def _init_sensor_state(self):
        old_state = self.sensor_state if hasattr(self, 'sensor_state') else {}
        self.sensor_state = {}
        
        saved_sensors = self.config.get("sensors", {})
        
        for cmd, (name, unit, def_show, def_log, def_limit) in self.available_sensors.items():
            if cmd in old_state:
                is_show = old_state[cmd]["show_var"].get()
                is_log = old_state[cmd]["log_var"].get()
                limit_val = old_state[cmd]["limit_var"].get()
                # Preserve widget references (Cache)
                card = old_state[cmd].get("card_widget", None)
                val_lbl = old_state[cmd].get("widget_value_label", None)
                bar = old_state[cmd].get("widget_progress_bar", None)
            else:
                saved = saved_sensors.get(cmd, {})
                is_show = saved.get("show", def_show)
                is_log = saved.get("log", def_log)
                limit_val = str(saved.get("limit", def_limit))
                card, val_lbl, bar = None, None, None

            self.sensor_state[cmd] = {
                "name": name, "unit": unit,
                "show_var": ctk.BooleanVar(value=is_show),
                "log_var": ctk.BooleanVar(value=is_log),
                "limit_var": ctk.StringVar(value=limit_val),
                "card_widget": card,
                "widget_value_label": val_lbl,
                "widget_progress_bar": bar
            }

    # --- DASHBOARD TAB (OPTIMIZED CACHE) ---
    def _setup_dashboard_tab(self):
        self.frame_controls = ctk.CTkFrame(self.tab_dash, height=50)
        self.frame_controls.pack(fill="x", padx=10, pady=5)
        self.btn_connect = ctk.CTkButton(self.frame_controls, text="CONNECT", fg_color="green", command=self.toggle_connection)
        self.btn_connect.pack(pady=10)
        self.dash_scroll = ctk.CTkScrollableFrame(self.tab_dash)
        self.dash_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def mark_dashboard_dirty(self):
        self.dashboard_dirty = True

    def rebuild_dashboard_grid(self):
        """OPTIMIZED: Hides/Shows widgets instead of destroying them."""
        # 1. Unmap all existing cards (don't destroy)
        for cmd, state in self.sensor_state.items():
            if state["card_widget"]:
                state["card_widget"].grid_forget()

        # 2. Map only the active ones
        active_sensors = [k for k, v in self.sensor_state.items() if v["show_var"].get()]
        cols = 3
        
        for i, cmd in enumerate(active_sensors):
            row = i // cols; col = i % cols
            state = self.sensor_state[cmd]
            
            # Check Cache
            card = state["card_widget"]
            
            if card is None:
                # Create if doesn't exist
                card = ctk.CTkFrame(self.dash_scroll)
                self.dash_scroll.grid_columnconfigure(col, weight=1)
                
                title = f"{state['name']}"
                if state['unit']: title += f" ({state['unit']})"
                ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10,0))
                
                val_lbl = ctk.CTkLabel(card, text="--", font=("Arial", 32, "bold"), text_color="#3498db")
                val_lbl.pack(pady=(0,5))
                
                bar = ctk.CTkProgressBar(card, width=200, height=10, progress_color="#3498db")
                bar.set(0)
                bar.pack(pady=(0,15))
                
                # Store in Cache
                state["card_widget"] = card
                state["widget_value_label"] = val_lbl
                state["widget_progress_bar"] = bar

            # Place it
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
        self.dashboard_dirty = False 

    # --- LIVE GRAPH TAB ---
    def _setup_graph_tab(self):
        self.fig, self.ax1 = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b') 
        self.ax1.set_facecolor('#2b2b2b')
        self.ax1.set_ylabel('RPM', color='#3498db', fontsize=12, fontweight='bold')
        self.ax1.tick_params(axis='y', labelcolor='#3498db', colors='white')
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.grid(True, color='#404040', linestyle='--', alpha=0.5)
        self.ax1.set_ylim(0, 7000)
        self.ax2 = self.ax1.twinx()
        self.ax2.set_ylabel('Speed (km/h)', color='#e74c3c', fontsize=12, fontweight='bold')
        self.ax2.tick_params(axis='y', labelcolor='#e74c3c', colors='white')
        self.ax2.spines['bottom'].set_color('white'); self.ax2.spines['top'].set_color('white') 
        self.ax2.spines['left'].set_color('white'); self.ax2.spines['right'].set_color('white')
        self.ax2.set_ylim(0, 160)
        self.line_rpm, = self.ax1.plot([], [], color='#3498db', linewidth=2, label="RPM")
        self.line_speed, = self.ax2.plot([], [], color='#e74c3c', linewidth=2, label="Speed")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_graph)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def update_graph(self):
        x_data = list(range(len(self.history_rpm)))
        self.line_rpm.set_data(x_data, self.history_rpm)
        self.line_speed.set_data(x_data, self.history_speed)
        self.ax1.set_xlim(0, len(self.history_rpm))
        self.ax2.set_xlim(0, len(self.history_speed))
        self.canvas.draw_idle()

    # --- SETTINGS TAB (OPTIMIZED & FILTERED) ---
    def _setup_settings_tab(self):
        frame_top = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)
        
        self.filter_var = ctk.StringVar(value="Standard")
        ctk.CTkLabel(frame_top, text="Show Pack:", font=("Arial", 12)).pack(side="left", padx=5)
        self.combo_filter = ctk.CTkOptionMenu(frame_top, variable=self.filter_var, values=["Standard"], command=self.refresh_settings_list)
        self.combo_filter.pack(side="left", padx=5)

        ctk.CTkButton(frame_top, text="Manage Pro Packs", fg_color="purple", width=150, command=self.open_pack_manager).pack(side="right")

        header_frame = ctk.CTkFrame(self.tab_settings, fg_color="#404040")
        header_frame.pack(fill="x", padx=20)
        
        frame_all_show = ctk.CTkFrame(header_frame, fg_color="transparent")
        frame_all_show.pack(side="right", padx=5)
        ctk.CTkButton(frame_all_show, text="All", width=30, height=15, font=("Arial", 8), command=lambda: self.toggle_all("show", True)).pack()
        ctk.CTkButton(frame_all_show, text="None", width=30, height=15, font=("Arial", 8), fg_color="gray", command=lambda: self.toggle_all("show", False)).pack()
        ctk.CTkLabel(header_frame, text="Show", width=30).pack(side="right")

        frame_all_log = ctk.CTkFrame(header_frame, fg_color="transparent")
        frame_all_log.pack(side="right", padx=5)
        ctk.CTkButton(frame_all_log, text="All", width=30, height=15, font=("Arial", 8), command=lambda: self.toggle_all("log", True)).pack()
        ctk.CTkButton(frame_all_log, text="None", width=30, height=15, font=("Arial", 8), fg_color="gray", command=lambda: self.toggle_all("log", False)).pack()
        ctk.CTkLabel(header_frame, text="Log", width=30).pack(side="right")

        ctk.CTkLabel(header_frame, text="Limit", width=80).pack(side="right", padx=5)
        ctk.CTkLabel(header_frame, text="Sensor Name", width=200, anchor="w").pack(side="left", padx=10)

        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings)
        self.settings_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        self.settings_scroll.grid_columnconfigure(0, weight=1) 
        self.settings_scroll.grid_columnconfigure(1, minsize=80) 
        self.settings_scroll.grid_columnconfigure(2, minsize=60) 
        self.settings_scroll.grid_columnconfigure(3, minsize=60) 

        self.refresh_settings_list()

        frame_log = ctk.CTkFrame(self.tab_settings)
        frame_log.pack(fill="x", padx=20, pady=20)
        self.lbl_path = ctk.CTkLabel(frame_log, text=f"Save Path: {self.logger.log_dir}")
        self.lbl_path.pack(side="left", padx=10)
        ctk.CTkButton(frame_log, text="Change Folder", command=self.change_log_folder).pack(side="right", padx=10)

    def update_filter_options(self):
        packs = sorted(list(set(self.sensor_sources.values())))
        if "Standard" in packs:
            packs.remove("Standard")
            packs.insert(0, "Standard")
        packs.insert(0, "All (Slow)")
        self.combo_filter.configure(values=packs)
        if self.filter_var.get() not in packs:
            self.filter_var.set("Standard")

    def refresh_settings_list(self, choice=None):
        for widget in self.settings_scroll.winfo_children(): widget.destroy()
        
        target_pack = self.filter_var.get()
        row_idx = 0
        
        items_to_show = []
        for cmd, data in self.sensor_state.items():
            src = self.sensor_sources.get(cmd, "Standard")
            if target_pack == "All (Slow)" or src == target_pack:
                items_to_show.append((cmd, data))
        
        for cmd, data in items_to_show:
            ctk.CTkLabel(self.settings_scroll, text=data["name"], anchor="w").grid(row=row_idx, column=0, sticky="w", padx=10, pady=2)
            ctk.CTkEntry(self.settings_scroll, textvariable=data["limit_var"], width=60).grid(row=row_idx, column=1, padx=5, pady=2)
            ctk.CTkCheckBox(self.settings_scroll, text="", variable=data["log_var"], width=20).grid(row=row_idx, column=2, padx=15, pady=2)
            ctk.CTkCheckBox(self.settings_scroll, text="", variable=data["show_var"], command=self.mark_dashboard_dirty, width=20).grid(row=row_idx, column=3, padx=15, pady=2)
            row_idx += 1
            if row_idx % 20 == 0: self.update_idletasks()

    def toggle_all(self, type_str, state):
        target_pack = self.filter_var.get()
        for cmd, data in self.sensor_state.items():
            src = self.sensor_sources.get(cmd, "Standard")
            if target_pack == "All (Slow)" or src == target_pack:
                if type_str == "show": data["show_var"].set(state)
                elif type_str == "log": data["log_var"].set(state)
        
        if type_str == "show": self.mark_dashboard_dirty()

    # --- PACK MANAGER POPUP (AUTO-CLOSE FIX) ---
    def open_pack_manager(self):
        window = ctk.CTkToplevel(self)
        window.title("Manage Pro Packs")
        window.geometry("400x350")
        window.attributes("-topmost", True)
        ctk.CTkLabel(window, text="Enable/Disable Car Models", font=("Arial", 16, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(window)
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        footer = ctk.CTkFrame(window, height=50)
        footer.pack(fill="x", side="bottom")

        enabled_packs = self.config.get("enabled_packs", [])
        
        available_files = []
        if os.path.exists(PRO_PACK_DIR):
            for root, dirs, files in os.walk(PRO_PACK_DIR):
                for f in files:
                    if f.endswith(".json"):
                        full = os.path.join(root, f)
                        rel = os.path.relpath(full, PRO_PACK_DIR)
                        available_files.append(rel)
        
        if not available_files:
            ctk.CTkLabel(scroll, text="No .json files found in /pro_packs").pack()
        
        pack_vars = {} 

        def on_save():
            new_enabled = [f for f, var in pack_vars.items() if var.get()]
            self.config["enabled_packs"] = new_enabled
            ConfigManager.save_config(self.config)
            
            # 1. Close Popup Immediately
            window.destroy()
            
            # 2. Show Loading on Main App
            self.configure(cursor="watch")
            self.update()
            
            # 3. Heavy Lifting
            self.reload_sensor_definitions()
            self.update_filter_options() 
            self.refresh_settings_list()
            self.mark_dashboard_dirty()
            
            # 4. Done
            self.configure(cursor="")
            self.append_debug_log("Packs Reloaded Successfully.")

        for f in available_files:
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=2)
            is_checked = f in enabled_packs
            var = ctk.BooleanVar(value=is_checked)
            pack_vars[f] = var
            ctk.CTkCheckBox(row, text=f, variable=var).pack(side="left", padx=10, pady=5)

        ctk.CTkButton(footer, text="Save & Reload", fg_color="green", command=on_save).pack(pady=10)

    # --- DIAGNOSTICS TAB ---
    def _setup_diagnostics_tab(self):
        btn_frame = ctk.CTkFrame(self.tab_diag, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.btn_analyze = ctk.CTkButton(btn_frame, text="RUN ANALYSIS", fg_color="purple", width=150, command=self.run_analysis)
        self.btn_analyze.pack(side="left", padx=10)
        self.btn_scan = ctk.CTkButton(btn_frame, text="SCAN CODES", fg_color="blue", width=150, command=self.scan_codes)
        self.btn_scan.pack(side="left", padx=10)
        self.btn_backup = ctk.CTkButton(btn_frame, text="FULL BACKUP", fg_color="orange", width=150, command=self.perform_full_backup)
        self.btn_backup.pack(side="left", padx=10)
        self.btn_clear = ctk.CTkButton(btn_frame, text="CLEAR CODES", fg_color="red", width=150, command=self.confirm_clear_codes)
        self.btn_clear.pack(side="left", padx=10)
        self.txt_dtc = ctk.CTkTextbox(self.tab_diag, width=700, height=350)
        self.txt_dtc.pack(pady=10)
        self.txt_dtc.insert("1.0", "Ready.\nUse 'Run Analysis' to check sensor data for logic problems.\nUse 'Scan Codes' to check ECU errors.")

    def _setup_debug_tab(self):
        self.txt_debug = ctk.CTkTextbox(self.tab_debug, width=700, height=400, font=("Consolas", 12))
        self.txt_debug.pack(pady=10, fill="both", expand=True)

    def on_close(self):
        data_to_save = {
            "log_dir": self.logger.log_dir, 
            "enabled_packs": self.config.get("enabled_packs", []), 
            "sensors": {}
        }
        for cmd, state in self.sensor_state.items():
            data_to_save["sensors"][cmd] = {"show": state["show_var"].get(), "log": state["log_var"].get(), "limit": state["limit_var"].get()}
        ConfigManager.save_config(data_to_save)
        plt.close('all') 
        self.destroy()

    def update_loop(self):
        if self.dashboard_dirty and self.tabview.get() == "Dashboard":
            self.rebuild_dashboard_grid()

        if self.obd.is_connected():
            data_snapshot = {}
            current_speed = 0

            for cmd, state in self.sensor_state.items():
                # Optimized Query: Only query if visible OR logging OR critical
                is_visible = state["show_var"].get()
                is_logging = state["log_var"].get()
                
                if is_visible or is_logging or cmd in ["SPEED", "RPM", "CONTROL_MODULE_VOLTAGE"]:
                    val = self.obd.query_sensor(cmd)
                    if val is not None:
                        data_snapshot[cmd] = val
                        if cmd == "SPEED": current_speed = val
                        
                        if is_visible:
                            if state["widget_value_label"]:
                                state["widget_value_label"].configure(text=str(val))
                            
                            try:
                                limit = float(state["limit_var"].get())
                                color = "#3498db" 
                                if cmd == "CONTROL_MODULE_VOLTAGE" and (val < 11.5 or val > 15.5): color = "red"
                                elif limit > 0 and val > limit: color = "red"
                                
                                if state["widget_value_label"]: state["widget_value_label"].configure(text_color=color)
                                
                                if state["widget_progress_bar"] and limit > 0:
                                    progress = min(val / limit, 1.0) 
                                    state["widget_progress_bar"].set(progress)
                                    state["widget_progress_bar"].configure(progress_color=color)

                            except ValueError: pass

            rpm_val = data_snapshot.get("RPM", 0)
            speed_val = data_snapshot.get("SPEED", 0)
            self.history_rpm.append(rpm_val)
            self.history_speed.append(speed_val)
            
            if self.tabview.get() == "Live Graph":
                self.update_graph()

            if current_speed > 0:
                self.btn_clear.configure(state="disabled", text="MOVING...")
            else:
                self.btn_clear.configure(state="normal", text="CLEAR CODES")

            self.logger.write_row(data_snapshot)
        self.after(500, self.update_loop)

    def run_analysis(self):
        if not self.obd.is_connected():
            self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Error: Connect to car first.")
            return
        self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Gathering data for analysis...\n")
        self.update()
        snapshot = {}
        thresholds = {}
        for cmd, state in self.sensor_state.items():
            snapshot[cmd] = self.obd.query_sensor(cmd)
            thresholds[cmd] = state["limit_var"].get()
        issues = DiagnosticEngine.analyze(snapshot, thresholds)
        if not issues: self.txt_dtc.insert("end", "✅ System Analysis Passed.")
        else:
            self.txt_dtc.insert("end", f"⚠️ Found {len(issues)} Potential Issues:\n", "bold")
            for issue in issues: self.txt_dtc.insert("end", f"• {issue}\n")

    def toggle_connection(self):
        if self.obd.is_connected():
            self.obd.disconnect()
            self.btn_connect.configure(text="CONNECT", fg_color="green")
            for cmd in self.sensor_state:
                lbl = self.sensor_state[cmd]['widget_value_label']
                if lbl: lbl.configure(text="--")
                bar = self.sensor_state[cmd]['widget_progress_bar']
                if bar: bar.set(0)
        else:
            self.btn_connect.configure(text="CONNECTING...", state="disabled")
            self.update()
            if self.obd.connect():
                self.btn_connect.configure(text="DISCONNECT", fg_color="red")
                log_sensors = [k for k, v in self.sensor_state.items() if v["log_var"].get()]
                self.logger.start_new_log(log_sensors)
                self.append_debug_log(f"Started logging: {len(log_sensors)} sensors.")
            else:
                self.btn_connect.configure(text="RETRY CONNECT", fg_color="orange")
            self.btn_connect.configure(state="normal")

    def change_log_folder(self):
        new_dir = filedialog.askdirectory()
        if new_dir:
            if self.logger.set_directory(new_dir): self.lbl_path.configure(text=f"Save Path: {new_dir}")

    def append_debug_log(self, message):
        self.txt_debug.insert("end", message + "\n"); self.txt_debug.see("end")

    def scan_codes(self):
        if not self.obd.is_connected(): self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Error: Not Connected."); return
        self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Scanning...\n"); self.update()
        codes = self.obd.get_dtc()
        self.txt_dtc.delete("1.0", "end")
        if not codes: self.txt_dtc.insert("end", "No Fault Codes Found (Green Light!)")
        else:
            self.txt_dtc.insert("end", f"Found {len(codes)} Faults:\n", "bold")
            for c in codes: self.txt_dtc.insert("end", f"• {c[0]}: {c[1]}\n")

    def perform_full_backup(self):
        if not self.obd.is_connected(): messagebox.showerror("Error", "Connect to car first!"); return
        self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Reading System Data...\n"); self.update()
        codes = self.obd.get_dtc()
        snapshot = self.obd.get_freeze_frame_snapshot(list(self.sensor_state.keys()))
        report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "fault_codes": codes, "freeze_frame_data": snapshot}
        filename = f"Backup_{int(time.time())}.json"
        filepath = os.path.join(self.logger.log_dir, filename)
        try:
            with open(filepath, 'w') as f: json.dump(report, f, indent=4)
            self.txt_dtc.insert("end", f"SUCCESS: Backup saved to:\n{filepath}\n\n"); self.txt_dtc.insert("end", f"Snapshot: {json.dumps(snapshot, indent=2)}")
        except Exception as e: self.txt_dtc.insert("end", f"Error saving backup: {e}")

    def confirm_clear_codes(self):
        if not self.obd.is_connected(): messagebox.showerror("Error", "Connect to car first!"); return
        answer = messagebox.askyesno("WARNING", "Have you performed a FULL BACKUP yet?\n\nClearing codes will PERMANENTLY erase Freeze Frame data.\nProceed?")
        if answer:
            self.txt_dtc.delete("1.0", "end"); self.txt_dtc.insert("end", "Clearing codes...\n"); self.update()
            if self.obd.clear_dtc(): self.txt_dtc.insert("end", "\nSUCCESS: Codes cleared.\n"); messagebox.showinfo("Success", "Codes cleared.")
            else: self.txt_dtc.insert("end", "\nFAILED: Could not clear codes.")