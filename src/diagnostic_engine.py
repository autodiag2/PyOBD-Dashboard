class DiagnosticEngine:
    @staticmethod
    def analyze(data, thresholds):
        """
        Analyzes current sensor data for potential issues based on logic rules.
        data: dict of current values (e.g., {'RPM': 4000, 'COOLANT_TEMP': 95})
        thresholds: dict of user limits from GUI (strings)
        """
        issues = []

        # Helper to safely get numbers
        def get_val(key):
            return float(data.get(key, 0))

        # --- RULE 1: OVERHEATING ---
        # Simple threshold check
        temp = get_val("COOLANT_TEMP")

        # Safely convert threshold string to float
        try:
            limit_temp = float(thresholds.get("COOLANT_TEMP", 110))
        except ValueError:
            limit_temp = 110.0  # Default fallback if setting is invalid

        if temp > limit_temp:
            issues.append(f"CRITICAL: Engine Overheating! ({temp}°C > {limit_temp}°C)")

        # --- RULE 2: BATTERY HEALTH ---
        # Voltage logic depends on engine state
        volts = get_val("CONTROL_MODULE_VOLTAGE")
        rpm = get_val("RPM")

        if rpm > 500:  # Engine is running
            if volts < 13.0:
                issues.append("WARNING: Alternator output low (<13V) while engine running.")
            elif volts > 15.0:
                issues.append("WARNING: Voltage Regulator failure (High Voltage > 15V).")
        else:  # Engine is off
            if 0 < volts < 11.8:
                issues.append("WARNING: Battery charge is critically low (<11.8V).")

        # --- RULE 3: HIGH RPM ON COLD ENGINE (The "Driver Abuse" Rule) ---
        # Combination: High RPM + Low Temp
        if rpm > 3500 and temp < 60 and temp > 0:
            issues.append("ADVICE: High RPM detected on cold engine. Risk of wear.")

        # --- RULE 4: HIGH LOAD AT IDLE (Stalling Risk) ---
        # Combination: High Load + Low Speed + Low RPM
        load = get_val("ENGINE_LOAD")
        speed = get_val("SPEED")
        if speed == 0 and load > 50 and rpm < 1000 and rpm > 0:
            issues.append("WARNING: High Engine Load at idle. Possible stalling or vacuum leak.")

        # --- RULE 5: USER THRESHOLD EXCEEDED ---
        # Generic check for user-defined limits (RPM, Speed, etc.)
        for sensor, limit_str in thresholds.items():
            try:
                # 1. Convert the String from GUI to a Float
                limit_val = float(limit_str)

                # 2. Only check if limit is > 0 (0 means disabled)
                if limit_val > 0:
                    val = get_val(sensor)
                    if val > limit_val:
                        # We already handled Coolant separately, avoid duplicate
                        if sensor != "COOLANT_TEMP":
                            issues.append(f"ALERT: {sensor} exceeded limit ({val} > {limit_val})")
            except ValueError:
                # If the user typed "abc" or left it empty in settings, skip this rule
                continue

        return issues