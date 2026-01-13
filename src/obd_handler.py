import obd
import random


class OBDHandler:
    def __init__(self, simulation=False):
        self.simulation = simulation
        self.connection = None
        self.status = "Disconnected"

    def connect(self):
        if self.simulation:
            self.status = "Connected (SIMULATION)"
            return True

        try:
            self.connection = obd.OBD()
            if self.connection.is_connected():
                self.status = "Connected"
                return True
            else:
                self.status = "Failed to Connect"
                return False
        except Exception as e:
            self.status = f"Error: {e}"
            return False

    def get_rpm(self):
        if self.simulation:
            return random.randint(800, 3000)

        if self.connection and self.connection.is_connected():
            return self.connection.query(obd.commands.RPM).value.magnitude
        return 0

    def get_speed(self):
        if self.simulation:
            return random.randint(0, 120)

        if self.connection and self.connection.is_connected():
            return self.connection.query(obd.commands.SPEED).value.magnitude
        return 0

    def get_dtc(self):
        """Reads Diagnostic Trouble Codes (Check Engine Light)"""
        if self.simulation:
            # Return a fake error code for testing
            return [("P0300", "Random/Multiple Cylinder Misfire Detected")]

        if self.connection and self.connection.is_connected():
            response = self.connection.query(obd.commands.GET_DTC)
            if not response.is_null():
                return response.value  # Returns a list of codes
        return []