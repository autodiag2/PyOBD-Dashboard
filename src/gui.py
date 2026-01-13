import customtkinter as ctk
import json
import os
import time
from tkinter import filedialog, messagebox
from data_logger import DataLogger
from config_manager import ConfigManager
from diagnostic_engine import DiagnosticEngine  # Import our new Engine

# --- MASTER CONFIGURATION ---
# Format: "OBD_COMMAND": ("Display Name", "Unit", Default_Show, Default_Log, Default_Max_Threshold)
AVAILABLE_SENSORS = {
    "RPM": ("Engine RPM", "", True, True, 6000),
    "SPEED": ("Vehicle Speed", "km/h", True, True, 120),
    "COOLANT_TEMP": ("Coolant Temp", "°C", True, True, 110),
    "CONTROL_MODULE_VOLTAGE": ("Voltage", "V", True, False, 15),
    "ENGINE_LOAD": ("Engine Load", "%", True, False, 90),
    "THROTTLE_POS": ("Throttle Pos", "%", False, True, 100),
    "INTAKE_TEMP": ("Intake Air Temp", "°C", False, False, 60),
    "MAF": ("MAF Air Flow", "g/s", False, False, 100),
    "FUEL_LEVEL": ("Fuel Level", "%", False, False, 0),  # 0 means no max limit check
    "BAROMETRIC_PRESSURE": ("Barometric", "kPa", False, False, 0),
    "TIMING_ADVANCE": ("Timing Adv", "°", False, False, 0),
    "RUN_TIME": ("Run Time", "sec", False, False, 0)
}


class DashboardApp(ctk.CTk):
    def __init__(self, obd_handler):
        super().__init__()
        self.obd = obd_handler
        self.logger = DataLogger()
        self.obd.log_callback = self.append_debug_log

        self.config = ConfigManager.load_config()
        self.sensor_state = {}

        # Window Setup
        self.title("PyOBD Professional - Mechanic AI Edition")
        self.geometry("1000x700")  # Made wider for the new settings columns
        ctk.set_appearance_mode("dark")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_dash = self.tabview.add("Dashboard")
        self.tab_diag = self.tabview.add("Diagnostics")
        self.tab_settings = self.tabview.add("Settings")
        self.tab_debug = self.tabview.add("Debug Log")

        self._init_sensor_state()
        self._setup_dashboard_tab()
        self._setup_diagnostics_tab()
        self._setup_settings_tab()
        self._setup_debug_tab()

        if "log_dir" in self.config:
            self.logger.set_directory(self.config["log_dir"])
            self.lbl_path.configure(text=f"Save Path: {self.logger.log_dir}")

        self.rebuild_dashboard_grid()
        self.update_loop()

    def _init_sensor_state(self):
        saved_sensors = self.config.get("sensors", {})

        for cmd, (name, unit, def_show, def_log, def_limit) in AVAILABLE_SENSORS.items():
            # Load defaults or saved values
            saved = saved_sensors.get(cmd, {})

            self.sensor_state[cmd] = {
                "name": name,
                "unit": unit,
                "show_var": ctk.BooleanVar(value=saved.get("show", def_show)),
                "log_var": ctk.BooleanVar(value=saved.get("log", def_log)),
                "limit_var": ctk.StringVar(value=str(saved.get("limit", def_limit))),  # User defined limit
                "widget_value_label": None
            }

    # --- DASHBOARD TAB ---
    def _setup_dashboard_tab(self):
        self.frame_controls = ctk.CTkFrame(self.tab_dash, height=50)
        self.frame_controls.pack(fill="x", padx=10, pady=5)
        self.btn_connect = ctk.CTkButton(self.frame_controls, text="CONNECT", fg_color="green",
                                         command=self.toggle_connection)
        self.btn_connect.pack(pady=10)
        self.dash_scroll = ctk.CTkScrollableFrame(self.tab_dash)
        self.dash_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def rebuild_dashboard_grid(self):
        for widget in self.dash_scroll.winfo_children(): widget.destroy()
        active_sensors = [k for k, v in self.sensor_state.items() if v["show_var"].get()]
        cols = 3
        for i, cmd in enumerate(active_sensors):
            row = i // cols;
            col = i % cols
            card = ctk.CTkFrame(self.dash_scroll)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.dash_scroll.grid_columnconfigure(col, weight=1)

            title = f"{self.sensor_state[cmd]['name']}"
            if self.sensor_state[cmd]['unit']: title += f" ({self.sensor_state[cmd]['unit']})"

            ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), text_color="gray").pack(pady=(10, 0))
            val_lbl = ctk.CTkLabel(card, text="--", font=("Arial", 32, "bold"), text_color="#3498db")
            val_lbl.pack(pady=(0, 10))
            self.sensor_state[cmd]['widget_value_label'] = val_lbl

    # --- SETTINGS TAB ---
    def _setup_settings_tab(self):
        lbl = ctk.CTkLabel(self.tab_settings, text="Sensor Configuration & Warnings", font=("Arial", 18, "bold"))
        lbl.pack(pady=10)

        header_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        header_frame.pack(fill="x", padx=20)
        # Columns
        ctk.CTkLabel(header_frame, text="Sensor Name", width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="Max Limit", width=80).pack(side="right", padx=5)  # New Column
        ctk.CTkLabel(header_frame, text="Log", width=50).pack(side="right", padx=10)
        ctk.CTkLabel(header_frame, text="Show", width=50).pack(side="right", padx=10)

        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings)
        self.settings_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        for cmd, data in self.sensor_state.items():
            row = ctk.CTkFrame(self.settings_scroll)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=data["name"], width=200, anchor="w").pack(side="left", padx=10)

            # Show Checkbox
            ctk.CTkCheckBox(row, text="", variable=data["show_var"], command=self.rebuild_dashboard_grid,
                            width=20).pack(side="right", padx=15)
            # Log Checkbox
            ctk.CTkCheckBox(row, text="", variable=data["log_var"], width=20).pack(side="right", padx=15)
            # Threshold Entry
            entry = ctk.CTkEntry(row, textvariable=data["limit_var"], width=60)
            entry.pack(side="right", padx=5)

        frame_log = ctk.CTkFrame(self.tab_settings)
        frame_log.pack(fill="x", padx=20, pady=20)
        self.lbl_path = ctk.CTkLabel(frame_log, text=f"Save Path: {self.logger.log_dir}")
        self.lbl_path.pack(side="left", padx=10)
        ctk.CTkButton(frame_log, text="Change Folder", command=self.change_log_folder).pack(side="right", padx=10)

    # --- DIAGNOSTICS TAB ---
    def _setup_diagnostics_tab(self):
        btn_frame = ctk.CTkFrame(self.tab_diag, fg_color="transparent")
        btn_frame.pack(pady=20)

        # New "Analyze" Button
        self.btn_analyze = ctk.CTkButton(btn_frame, text="RUN ANALYSIS", fg_color="purple", width=150,
                                         command=self.run_analysis)
        self.btn_analyze.pack(side="left", padx=10)

        self.btn_scan = ctk.CTkButton(btn_frame, text="SCAN CODES", fg_color="blue", width=150, command=self.scan_codes)
        self.btn_scan.pack(side="left", padx=10)
        self.btn_backup = ctk.CTkButton(btn_frame, text="FULL BACKUP", fg_color="orange", width=150,
                                        command=self.perform_full_backup)
        self.btn_backup.pack(side="left", padx=10)
        self.btn_clear = ctk.CTkButton(btn_frame, text="CLEAR CODES", fg_color="red", width=150,
                                       command=self.confirm_clear_codes)
        self.btn_clear.pack(side="left", padx=10)

        self.txt_dtc = ctk.CTkTextbox(self.tab_diag, width=700, height=350)
        self.txt_dtc.pack(pady=10)
        self.txt_dtc.insert("1.0",
                            "Ready.\nUse 'Run Analysis' to check sensor data for logic problems.\nUse 'Scan Codes' to check ECU errors.")

    def _setup_debug_tab(self):
        self.txt_debug = ctk.CTkTextbox(self.tab_debug, width=700, height=400, font=("Consolas", 12))
        self.txt_debug.pack(pady=10, fill="both", expand=True)

    def on_close(self):
        data_to_save = {"log_dir": self.logger.log_dir, "sensors": {}}
        for cmd, state in self.sensor_state.items():
            data_to_save["sensors"][cmd] = {
                "show": state["show_var"].get(),
                "log": state["log_var"].get(),
                "limit": state["limit_var"].get()  # Save the user threshold
            }
        ConfigManager.save_config(data_to_save)
        self.destroy()

    def update_loop(self):
        if self.obd.is_connected():
            data_snapshot = {}
            current_speed = 0

            for cmd, state in self.sensor_state.items():
                if state["show_var"].get() or state["log_var"].get() or cmd == "SPEED":
                    val = self.obd.query_sensor(cmd)
                    if val is not None:
                        data_snapshot[cmd] = val
                        if cmd == "SPEED": current_speed = val

                        # Update UI
                        if state["show_var"].get() and state["widget_value_label"]:
                            state["widget_value_label"].configure(text=str(val))

                            # --- COLOR CODING LOGIC ---
                            try:
                                limit = float(state["limit_var"].get())
                                # Special case for Voltage (Low is bad too)
                                if cmd == "CONTROL_MODULE_VOLTAGE" and (val < 11.5 or val > 15.5):
                                    state["widget_value_label"].configure(text_color="red")
                                # Standard Max Limit check
                                elif limit > 0 and val > limit:
                                    state["widget_value_label"].configure(text_color="red")
                                else:
                                    state["widget_value_label"].configure(text_color="#3498db")  # Default Blue
                            except ValueError:
                                pass  # Ignore if user typed text instead of numbers in settings

            if current_speed > 0:
                self.btn_clear.configure(state="disabled", text="MOVING...")
            else:
                self.btn_clear.configure(state="normal", text="CLEAR CODES")

            self.logger.write_row(data_snapshot)
        self.after(500, self.update_loop)

    # --- NEW FEATURE: ANALYSIS ---
    def run_analysis(self):
        """Gather data and run the Diagnostic Engine"""
        if not self.obd.is_connected():
            self.txt_dtc.delete("1.0", "end")
            self.txt_dtc.insert("end", "Error: Connect to car first.")
            return

        self.txt_dtc.delete("1.0", "end")
        self.txt_dtc.insert("end", "Gathering data for analysis...\n")
        self.update()

        # 1. Gather Snapshot of ALL sensors (even hidden ones)
        snapshot = {}
        thresholds = {}
        for cmd, state in self.sensor_state.items():
            val = self.obd.query_sensor(cmd)
            snapshot[cmd] = val
            thresholds[cmd] = state["limit_var"].get()

        # 2. Run Engine
        self.txt_dtc.insert("end", "Analyzing Logic...\n\n")
        issues = DiagnosticEngine.analyze(snapshot, thresholds)

        # 3. Report
        if not issues:
            self.txt_dtc.insert("end",
                                "✅ System Analysis Passed.\nNo obvious logic problems detected based on current sensor readings.")
        else:
            self.txt_dtc.insert("end", f"⚠️ Found {len(issues)} Potential Issues:\n", "bold")
            for issue in issues:
                self.txt_dtc.insert("end", f"• {issue}\n")

    # ... (Rest of the standard methods: toggle_connection, change_log_folder, append_debug_log, scan_codes, perform_full_backup, confirm_clear_codes) ...
    def toggle_connection(self):
        if self.obd.is_connected():
            self.obd.disconnect()
            self.btn_connect.configure(text="CONNECT", fg_color="green")
            for cmd in self.sensor_state:
                lbl = self.sensor_state[cmd]['widget_value_label']
                if lbl: lbl.configure(text="--")
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
            if self.logger.set_directory(new_dir):
                self.lbl_path.configure(text=f"Save Path: {new_dir}")

    def append_debug_log(self, message):
        self.txt_debug.insert("end", message + "\n")
        self.txt_debug.see("end")

    def scan_codes(self):
        if not self.obd.is_connected():
            self.txt_dtc.delete("1.0", "end")
            self.txt_dtc.insert("end", "Error: Not Connected to Car.")
            return
        self.txt_dtc.delete("1.0", "end")
        self.txt_dtc.insert("end", "Scanning...\n")
        self.update()
        codes = self.obd.get_dtc()
        self.txt_dtc.delete("1.0", "end")
        if not codes:
            self.txt_dtc.insert("end", "No Fault Codes Found (Green Light!)")
        else:
            self.txt_dtc.insert("end", f"Found {len(codes)} Faults:\n", "bold")
            for c in codes: self.txt_dtc.insert("end", f"• {c[0]}: {c[1]}\n")

    def perform_full_backup(self):
        if not self.obd.is_connected():
            messagebox.showerror("Error", "Connect to car first!")
            return
        self.txt_dtc.delete("1.0", "end")
        self.txt_dtc.insert("end", "Reading System Data... (This may take 10s)\n")
        self.update()
        codes = self.obd.get_dtc()
        snapshot = self.obd.get_freeze_frame_snapshot(list(self.sensor_state.keys()))
        report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "fault_codes": codes, "freeze_frame_data": snapshot}
        filename = f"Backup_{int(time.time())}.json"
        filepath = os.path.join(self.logger.log_dir, filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=4)
            self.txt_dtc.insert("end", f"SUCCESS: Backup saved to:\n{filepath}\n\n")
            self.txt_dtc.insert("end", f"Snapshot Data: {json.dumps(snapshot, indent=2)}")
        except Exception as e:
            self.txt_dtc.insert("end", f"Error saving backup: {e}")

    def confirm_clear_codes(self):
        if not self.obd.is_connected():
            messagebox.showerror("Error", "Connect to car first!")
            return
        answer = messagebox.askyesno("WARNING: Clear Codes?",
                                     "Have you performed a FULL BACKUP yet?\n\nClearing codes will PERMANENTLY erase Freeze Frame data.\nProceed?")
        if answer:
            self.txt_dtc.delete("1.0", "end")
            self.txt_dtc.insert("end", "Attempting to clear codes...\n")
            self.update()
            if self.obd.clear_dtc():
                self.txt_dtc.insert("end", "\nSUCCESS: Codes cleared.\n")
                messagebox.showinfo("Success", "Codes have been cleared.")
            else:
                self.txt_dtc.insert("end", "\nFAILED: Could not clear codes.")