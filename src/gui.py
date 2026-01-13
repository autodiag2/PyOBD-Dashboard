import customtkinter as ctk


class DashboardApp(ctk.CTk):
    def __init__(self, obd_handler):
        super().__init__()
        self.obd = obd_handler

        # Window Setup
        self.title("PyOBD Dashboard")
        self.geometry("700x500")  # Made it slightly bigger
        ctk.set_appearance_mode("dark")

        # Layout Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- HEADER ---
        self.lbl_status = ctk.CTkLabel(self, text="Status: Waiting...", font=("Arial", 14))
        self.lbl_status.grid(row=0, column=0, columnspan=2, pady=10)

        # --- GAUGES ---
        self.frame_rpm = ctk.CTkFrame(self)
        self.frame_rpm.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_rpm, text="RPM", font=("Arial", 16, "bold")).pack(pady=5)
        self.lbl_rpm_value = ctk.CTkLabel(self.frame_rpm, text="0", font=("Arial", 30), text_color="#3498db")
        self.lbl_rpm_value.pack(pady=5)

        self.frame_speed = ctk.CTkFrame(self)
        self.frame_speed.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_speed, text="SPEED", font=("Arial", 16, "bold")).pack(pady=5)
        self.lbl_speed_value = ctk.CTkLabel(self.frame_speed, text="0", font=("Arial", 30), text_color="#e74c3c")
        self.lbl_speed_value.pack(pady=5)

        # --- DIAGNOSTICS AREA ---
        self.frame_dtc = ctk.CTkFrame(self)
        self.frame_dtc.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.btn_scan = ctk.CTkButton(self.frame_dtc, text="SCAN FOR FAULT CODES", fg_color="red",
                                      command=self.scan_codes)
        self.btn_scan.pack(pady=10)

        self.txt_dtc = ctk.CTkTextbox(self.frame_dtc, height=100)
        self.txt_dtc.pack(fill="x", padx=10, pady=10)

        # --- FOOTER ---
        self.btn_connect = ctk.CTkButton(self, text="Connect to Car", command=self.start_connection)
        self.btn_connect.grid(row=3, column=0, columnspan=2, pady=10)

        # Start the update loop
        self.update_dashboard()

    def start_connection(self):
        self.lbl_status.configure(text="Connecting...", text_color="yellow")
        self.update()
        if self.obd.connect():
            self.lbl_status.configure(text=f"Status: {self.obd.status}", text_color="green")
        else:
            self.lbl_status.configure(text="Connection Failed", text_color="red")

    def update_dashboard(self):
        rpm = self.obd.get_rpm()
        speed = self.obd.get_speed()
        self.lbl_rpm_value.configure(text=str(int(rpm)))
        self.lbl_speed_value.configure(text=str(int(speed)))
        self.after(500, self.update_dashboard)

    def scan_codes(self):
        self.txt_dtc.delete("1.0", "end")  # Clear previous text
        self.txt_dtc.insert("end", "Scanning...\n")
        self.update()

        codes = self.obd.get_dtc()

        self.txt_dtc.delete("1.0", "end")
        if not codes:
            self.txt_dtc.insert("end", "No Fault Codes Detected.")
        else:
            for code in codes:
                # code[0] is the P-code, code[1] is the description
                self.txt_dtc.insert("end", f"{code[0]}: {code[1]}\n")