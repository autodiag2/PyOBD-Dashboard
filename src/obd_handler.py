import obd
from obd.utils import bytes_to_int
import random
import time
import re

class OBDHandler:
    def __init__(self, simulation=False, log_callback=None):
        self.simulation = simulation
        self.connection = None
        self.status = "Disconnected"
        self.log_callback = log_callback
        self.inter_command_delay = 0.05 
        
        # Store Pro Definitions here
        self.pro_defs = {} 

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        print(message)

    def set_pro_definitions(self, defs):
        """Receives the dictionary of custom sensors from the GUI"""
        self.pro_defs = defs

    def is_connected(self):
        return self.status == "Connected" or self.status == "Connected (SIMULATION)"

    def connect(self):
        self.log("Attempting connection...")
        if self.simulation:
            self.status = "Connected (SIMULATION)"
            self.log("SUCCESS: Simulation Mode Active")
            return True
        
        try:
            # fast=False ensures we initialize protocol slowly/safely
            self.connection = obd.OBD(fast=False) 
            if self.connection.is_connected():
                self.status = "Connected"
                self.log(f"SUCCESS: Connected to {self.connection.port_name}")
                return True
            else:
                self.status = "Failed"
                self.log("ERROR: Interface found, but no connection to ECU.")
                return False
        except Exception as e:
            self.status = "Error"
            self.log(f"CRITICAL ERROR: {e}")
            return False

    def disconnect(self):
        self.log("Disconnecting...")
        if self.connection:
            self.connection.close()
            self.connection = None
        self.status = "Disconnected"
        self.log("Disconnected.")

    def query_sensor(self, command_key):
        if not self.is_connected(): return None
        if self.simulation: return self._simulate_data(command_key)

        # 1. Check if it is a STANDARD Command
        if hasattr(obd.commands, command_key):
            cmd = getattr(obd.commands, command_key)
            time.sleep(self.inter_command_delay) 
            try:
                response = self.connection.query(cmd)
                if response.is_null(): return None
                return response.value.magnitude
            except:
                return None
        
        # 2. Check if it is a PRO Command (Custom PID)
        elif command_key in self.pro_defs:
            return self._query_custom_pid(command_key)

        return None

    def _query_custom_pid(self, key):
        """Executes a raw PID command and calculates the result using the formula"""
        # Definition format: [Name, Unit, Show, Log, Limit, PID, HEADER, FORMULA]
        definition = self.pro_defs[key]
        
        # We need at least index 7 (Formula) for this to work
        if len(definition) < 8: return None
        
        pid_hex = definition[5]
        header_hex = definition[6]
        formula = definition[7]

        time.sleep(self.inter_command_delay)

        try:
            # Set the Header (Target ECU)
            # 7E0 = Engine, 7E2 = Hybrid/Transmission usually
            if header_hex:
                self.connection.query(obd.commands.AT.SH + header_hex)

            # Send the Mode + PID (e.g., 21C3)
            # We construct a custom command
            mode = pid_hex[:2] # e.g. "21"
            pid = pid_hex[2:]  # e.g. "C3"
            
            # Send raw command
            raw_response = self.connection.query(obd.commands.mode(mode) + pid)
            
            if raw_response.is_null(): return None

            # Get the bytes (messages[0].data is the byte array)
            if not raw_response.messages: return None
            data_bytes = raw_response.messages[0].data 
            
            # Remove the Mode/PID echo from the start if present (usually first 2 bytes)
            # python-OBD usually handles this, but raw mode can be tricky.
            # We assume data_bytes starts with A.
            
            return self._calculate_formula(formula, data_bytes)

        except Exception as e:
            # self.log(f"Pro Query Error ({key}): {e}")
            return None

    def _calculate_formula(self, formula, data_bytes):
        """
        Parses Torque Pro style formulas: ((A*256)+B)/100
        A = bytes[0], B = bytes[1], etc.
        """
        # Create a dictionary for A, B, C... based on data_bytes
        # Torque uses A for 1st byte, B for 2nd...
        variables = {}
        for i, byte_val in enumerate(data_bytes):
            char_code = 65 + i # 65 is ASCII for 'A'
            if char_code > 90: break # Only go up to Z
            variables[chr(char_code)] = byte_val

        # Replace variables in formula with values
        # We iterate backwards from Z to A to prevent replacing "AA" with "ValueA"
        # Actually, simpler approach: use regex or safe eval context
        
        # Safe Eval Context
        try:
            # Allow math functions if needed
            allowed_names = {"min": min, "max": max, "abs": abs}
            allowed_names.update(variables)
            
            # Evaluate
            result = eval(formula, {"__builtins__": {}}, allowed_names)
            return float(result)
        except:
            return None

    def get_dtc(self):
        if not self.is_connected(): return []
        self.log("Querying DTCs...")
        if self.simulation: return [("P0300", "Random/Multiple Cylinder Misfire")]
        
        time.sleep(0.2)
        res = self.connection.query(obd.commands.GET_DTC)
        return res.value if not res.is_null() else []

    def get_freeze_frame_snapshot(self, sensor_list):
        self.log("Reading Freeze Frame Data...")
        snapshot = {}
        if self.simulation:
            time.sleep(1)
            return {"RPM": 4520, "SPEED": 110, "DTC": "P0300"}

        if self.connection and self.connection.is_connected():
            for name in sensor_list:
                val = self.query_sensor(name) # Reuse our smart query function
                if val is not None:
                    snapshot[name] = val
        return snapshot

    def clear_dtc(self):
        self.log("Attempting to Clear DTCs...")
        if self.simulation:
            time.sleep(1)
            self.log("SIMULATION: Codes Cleared.")
            return True
            
        if self.connection and self.connection.is_connected():
            try:
                self.connection.query(obd.commands.CLEAR_DTC)
                self.log("Command Sent: CLEAR_DTC")
                return True
            except Exception as e:
                self.log(f"Clear Failed: {e}")
                return False
        return False

    def _simulate_data(self, name):
        # Simulation Logic
        ranges = {
            'RPM': (800, 5000), 'SPEED': (0, 130),
            'COOLANT_TEMP': (80, 110), 'CONTROL_MODULE_VOLTAGE': (12.8, 14.5),
            'ENGINE_LOAD': (15, 80), 'THROTTLE_POS': (0, 100),
            'INTAKE_TEMP': (20, 50), 'MAF': (2, 50),
            'FUEL_LEVEL': (0, 100), 'BAROMETRIC_PRESSURE': (95, 105),
            'TIMING_ADVANCE': (-10, 40), 'RUN_TIME': (0, 9999)
        }
        
        # If it's a Pro Command (not in standard ranges), give random value
        if name not in ranges:
             return random.randint(0, 100)

        if name == 'SPEED':
            return 0 if random.random() < 0.1 else random.randint(0, 120)

        if name in ranges:
            val = random.uniform(*ranges[name])
            return int(val) if val > 10 else round(val, 2)
        return 0