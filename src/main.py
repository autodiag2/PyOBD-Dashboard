from obd_handler import OBDHandler
from gui import DashboardApp

# SET THIS TO FALSE WHEN HARDWARE ARRIVES
SIMULATION_MODE = True 

if __name__ == "__main__":
    print("Starting PyOBD Dashboard...")

    handler = OBDHandler(simulation=SIMULATION_MODE)

    app = DashboardApp(handler)

    app.mainloop()