import customtkinter as ctk
from ui.tooltip import ToolTip
from ui.theme import ThemeManager
from ui.widgets.analog_gauge import AnalogGauge


class DashboardTab:
    def __init__(self, parent_frame, app_instance):
        self.frame = parent_frame
        self.app = app_instance

        self.frame_controls = ctk.CTkFrame(self.frame, height=50, fg_color=ThemeManager.get("BACKGROUND"))
        self.frame_controls.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.frame_controls, text="Port:", font=("Arial", 12),
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left", padx=(10, 5))

        self.app.var_port = ctk.StringVar(value="Auto")
        self.combo_ports = ctk.CTkOptionMenu(
            self.frame_controls,
            variable=self.app.var_port,
            values=self.app.get_serial_ports(),
            width=120,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("ACCENT"),
            button_color=ThemeManager.get("ACCENT_DIM")
        )
        self.combo_ports.pack(side="left", padx=5)

        ctk.CTkButton(self.frame_controls, text="⟳", width=30, fg_color=ThemeManager.get("CARD_BG"),
                      command=self.app.refresh_ports).pack(side="left", padx=2)

        self.app.btn_connect = ctk.CTkButton(
            self.frame_controls,
            text="CONNECT",
            fg_color=ThemeManager.get("ACCENT"),
            text_color=ThemeManager.get("BACKGROUND"),
            hover_color=ThemeManager.get("ACCENT_DIM"),
            command=self.app.on_connect_click,
            width=200
        )
        self.app.btn_connect.pack(side="left", padx=50)

        self.dash_scroll = ctk.CTkScrollableFrame(self.frame, fg_color=ThemeManager.get("BACKGROUND"))
        self.dash_scroll.pack(fill="both", expand=True, padx=0, pady=0)

    def rebuild_grid(self):
        # 1. Hide existing
        for cmd, state in self.app.sensor_state.items():
            if state["card_widget"]:
                state["card_widget"].grid_forget()

        active_sensors = [k for k, v in self.app.sensor_state.items() if v["show_var"].get()]
        cols = 3

        for i, cmd in enumerate(active_sensors):
            row = i // cols;
            col = i % cols
            state = self.app.sensor_state[cmd]

            container = state["card_widget"]

            if container is None:
                try:
                    limit = float(state['limit_var'].get())
                except:
                    limit = 100

                container = ctk.CTkFrame(self.dash_scroll, fg_color=ThemeManager.get("CARD_BG"))

                lbl_title = ctk.CTkLabel(
                    container,
                    text=state['name'],
                    font=("Arial", 14, "bold"),
                    text_color=ThemeManager.get("TEXT_MAIN")
                )
                lbl_title.pack(pady=(10, 0))

                gauge = AnalogGauge(
                    container,
                    width=180,
                    height=180,
                    min_val=0,
                    max_val=limit,
                    unit=state['unit']
                )
                gauge.pack(pady=5)

                state["card_widget"] = container
                state["widget_progress_bar"] = gauge
                state["widget_title_label"] = lbl_title

                tooltip_text = state.get("description", state['name'])
                ToolTip(container, text=tooltip_text, delay=1000)

            state["card_widget"].grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            self.dash_scroll.grid_columnconfigure(col, weight=1)