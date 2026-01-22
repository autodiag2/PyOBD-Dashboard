import json
import os
import time


class CanSessionManager:
    def __init__(self):
        self.filename = None
        self.saved_commands = []
        self.sniff_history = []

    def create_new_session(self):
        self.filename = None
        self.saved_commands = []
        self.sniff_history = []

    def save_command(self, name, can_id, data):
        cmd = {
            "name": name,
            "id": can_id,
            "data": data,
            "timestamp": time.time()
        }
        self.saved_commands.append(cmd)

    def save_session_to_file(self, filepath):
        data = {
            "meta": {
                "created": time.time(),
                "app_version": "1.1"
            },
            "commands": self.saved_commands
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            self.filename = filepath
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session_from_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.saved_commands = data.get("commands", [])
            self.filename = filepath
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False