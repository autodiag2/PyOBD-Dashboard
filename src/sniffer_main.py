from ui.sniffer_window import SnifferApp
import customtkinter as ctk

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    app = SnifferApp()
    app.mainloop()