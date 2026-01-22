import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from dyno_engine import DynoEngine
from ui.theme import ThemeManager


class DynoTab:
    def __init__(self, parent_frame, app_instance):
        self.frame = parent_frame
        self.app = app_instance
        self.dyno = DynoEngine()
        self.is_recording = False
        self.current_weight = 1600

        self.panel_left = ctk.CTkFrame(self.frame, width=250, fg_color=ThemeManager.get("CARD_BG"))
        self.panel_left.pack(side="left", fill="y", padx=10, pady=10)

        header_frame = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        header_frame.pack(fill="x", pady=20, padx=10)

        ctk.CTkLabel(header_frame, text="VIRTUAL DYNO", font=("Arial", 19, "bold"),
                     text_color=ThemeManager.get("ACCENT")).pack(side="left")
        ctk.CTkButton(header_frame, text="?", width=28, height=28, fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.show_help).pack(side="right")

        ctk.CTkLabel(self.panel_left, text="Car Weight (kg):", text_color=ThemeManager.get("TEXT_MAIN")).pack(
            pady=(10, 0))
        self.entry_weight = ctk.CTkEntry(self.panel_left, placeholder_text="e.g. 1500")
        self.entry_weight.insert(0, "1600")
        self.entry_weight.pack(pady=5)

        self.lbl_hp = ctk.CTkLabel(self.panel_left, text="0 HP", font=("Arial", 30, "bold"),
                                   text_color=ThemeManager.get("TEXT_MAIN"))
        self.lbl_hp.pack(pady=(30, 5))
        ctk.CTkLabel(self.panel_left, text="Peak Power", text_color=ThemeManager.get("TEXT_DIM")).pack()

        self.lbl_tq = ctk.CTkLabel(self.panel_left, text="0 Nm", font=("Arial", 30, "bold"),
                                   text_color=ThemeManager.get("TEXT_MAIN"))
        self.lbl_tq.pack(pady=(20, 5))
        ctk.CTkLabel(self.panel_left, text="Peak Torque", text_color=ThemeManager.get("TEXT_DIM")).pack()

        self.btn_record = ctk.CTkButton(
            self.panel_left,
            text="START RUN",
            fg_color=ThemeManager.get("ACCENT"),
            height=50,
            font=("Arial", 16, "bold"),
            command=self.toggle_recording
        )
        self.btn_record.pack(side="bottom", pady=20, padx=20, fill="x")

        self.panel_right = ctk.CTkFrame(self.frame, fg_color=ThemeManager.get("BACKGROUND"))
        self.panel_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.set_xlabel('RPM', color='white')
        self.ax.set_ylabel('Power (HP)', color=ThemeManager.get("ACCENT"), fontweight='bold')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, color='#404040', linestyle='--', alpha=0.5)

        self.line_hp, = self.ax.plot([], [], color=ThemeManager.get("ACCENT"), linewidth=2, label="HP")

        self.ax2 = self.ax.twinx()
        self.ax2.set_ylabel('Torque (Nm)', color=ThemeManager.get("WARNING"), fontweight='bold')
        self.ax2.tick_params(axis='y', labelcolor=ThemeManager.get("WARNING"), colors='white')
        self.ax2.spines['bottom'].set_color('white');
        self.ax2.spines['top'].set_color('white')
        self.ax2.spines['left'].set_color('white');
        self.ax2.spines['right'].set_color('white')

        self.line_tq, = self.ax2.plot([], [], color=ThemeManager.get("WARNING"), linewidth=2, label="Torque")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.panel_right)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.x_rpm = []
        self.y_hp = []
        self.y_tq = []

    def show_help(self):
        msg = (
            "HOW TO PERFORM A DYNO RUN:\n\n"
            "1. Find a flat, safe, private road.\n"
            "2. Enter your car's total weight (Car + Driver) in kg.\n"
            "3. Stop the car completely.\n"
            "4. Click 'START RUN'.\n"
            "5. Put car in 2nd or 3rd gear.\n"
            "6. Accelerate Full Throttle from low RPM to Redline.\n"
            "7. Click 'STOP' immediately after letting off gas.\n\n"
            "Note: Results are estimates based on physics (F=ma)."
        )
        messagebox.showinfo("Dyno Instructions", msg)

    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.btn_record.configure(text="START RUN", fg_color=ThemeManager.get("ACCENT"))
        else:
            try:
                weight = float(self.entry_weight.get())
            except ValueError:
                weight = 1600

            self.dyno.reset()
            self.x_rpm.clear()
            self.y_hp.clear()
            self.y_tq.clear()
            self.is_recording = True
            self.current_weight = weight
            self.btn_record.configure(text="STOP", fg_color=ThemeManager.get("WARNING"))

    def update_dyno(self, speed_kmh, rpm):
        if not self.is_recording: return

        hp, torque = self.dyno.calculate_step(self.current_weight, speed_kmh, rpm)

        self.lbl_hp.configure(text=f"{int(self.dyno.peak_hp)} HP")
        self.lbl_tq.configure(text=f"{int(self.dyno.peak_torque)} Nm")

        if rpm > 1000 and hp > 0:
            self.x_rpm.append(rpm)
            self.y_hp.append(hp)
            self.y_tq.append(torque)

            self.line_hp.set_data(self.x_rpm, self.y_hp)
            self.line_tq.set_data(self.x_rpm, self.y_tq)

            if self.x_rpm:
                self.ax.set_xlim(min(self.x_rpm), max(self.x_rpm) + 500)
                self.ax.set_ylim(0, max(self.y_hp) * 1.2)
                self.ax2.set_ylim(0, max(self.y_tq) * 1.2)

            self.canvas.draw_idle()