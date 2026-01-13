from obd_handler import OBDHandler
from gui import DashboardApp

# SET THIS TO FALSE WHEN HARDWARE ARRIVES
SIMULATION_MODE = True 

if __name__ == "__main__":
    print("Starting PyOBD Dashboard...")
    
    # Initialize the backend
    handler = OBDHandler(simulation=SIMULATION_MODE)
    
    # Initialize the frontend and pass the backend to it
    app = DashboardApp(handler)

    app.mainloop()