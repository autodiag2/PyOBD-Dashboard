class DiagnosticEngine:
    @staticmethod
    def analyze(data, thresholds):
        issues = []

        def get_val(key):
            try:
                return float(data.get(key, 0))
            except (ValueError, TypeError):
                return 0.0

        temp = get_val("COOLANT_TEMP")
        volts = get_val("CONTROL_MODULE_VOLTAGE")
        rpm = get_val("RPM")
        speed = get_val("SPEED")
        load = get_val("ENGINE_LOAD")
        run_time = get_val("RUN_TIME")
        intake_temp = get_val("INTAKE_TEMP")
        throttle = get_val("THROTTLE_POS")
        maf = get_val("MAF")

        try:
            limit_temp = float(thresholds.get("COOLANT_TEMP", 110))
        except ValueError:
            limit_temp = 110.0

        if temp > limit_temp:
            issues.append(f"CRITICAL: Engine Overheating! ({temp}°C > {limit_temp}°C)")

        if run_time > 600 and 0 < temp < 70:
            issues.append(f"ADVICE: Thermostat likely stuck OPEN. Engine is not warming up ({temp}°C after 10 mins).")

        if rpm > 500:
            if volts < 13.0:
                issues.append("WARNING: Alternator output low (<13V). Check Alternator.")
            elif volts > 15.5:
                issues.append("CRITICAL: Voltage Regulator failure (>15.5V). Risk of frying ECU.")
        else:
            if 0 < volts < 11.8:
                issues.append("WARNING: Battery charge critically low (<11.8V). Car may not start.")

        if rpm > 3500 and 0 < temp < 60:
            issues.append("ADVICE: High RPM detected on cold engine. High risk of wear.")

        if speed == 0 and load > 50 and 0 < rpm < 1000:
            issues.append("WARNING: High Engine Load at idle. Possible vacuum leak or AC compressor seize.")

        if load > 80 and throttle < 5 and rpm > 1000:
            issues.append("WARNING: TPS Mismatch. Load is high (80%+) but Throttle reads closed.")

        if throttle > 80 and rpm > 3000 and 0 < maf < 10:
            issues.append("CRITICAL: MAF Sensor reading extremely low under load. Sensor likely dead.")

        if speed > 80 and intake_temp > 70:
            issues.append("ADVICE: High Intake Temp while moving. Check Intercooler or Cold Air Intake heat shielding.")

        for sensor, limit_str in thresholds.items():
            try:
                limit_val = float(limit_str)
                if limit_val > 0 and sensor != "COOLANT_TEMP":
                    val = get_val(sensor)
                    if val > limit_val:
                        issues.append(f"ALERT: {sensor} exceeded limit ({val} > {limit_val})")
            except ValueError:
                continue

        return issues