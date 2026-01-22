import time


class DynoEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = None
        self.last_time = None
        self.last_speed_ms = 0
        self.peak_hp = 0
        self.peak_torque = 0
        self.data_points = []  # List of (RPM, HP, Torque)

    def calculate_step(self, weight_kg, speed_kmh, rpm):
        current_time = time.time()

        # Convert Speed to Meters per Second (m/s)
        speed_ms = speed_kmh / 3.6

        if self.last_time is None:
            self.last_time = current_time
            self.last_speed_ms = speed_ms
            return 0, 0

        # Calculate Delta
        dt = current_time - self.last_time
        dv = speed_ms - self.last_speed_ms

        # Avoid division by zero or tiny timestamps
        if dt < 0.1:
            return 0, 0

        # 1. Acceleration (m/s^2)
        accel = dv / dt

        # 2. Force (Newtons) -> F = ma
        # We add 15% for aerodynamic drag and rolling resistance approximation
        # (A real dyno would measure coast-down loss, we just estimate)
        force = (weight_kg * accel) * 1.15

        # 3. Power (Watts) -> P = F * v
        power_watts = force * speed_ms

        # 4. Horsepower
        hp = power_watts / 745.7

        # 5. Torque (Nm) -> Torque = (HP * 5252) / RPM * (Unit conversion)
        # Easier metric formula: Power(kW) = Torque(Nm) * RPM / 9549
        kw = power_watts / 1000
        if rpm > 0:
            torque = (kw * 9549) / rpm
        else:
            torque = 0

        # Filter noise (ignore negative power when shifting gears)
        if hp < 0: hp = 0
        if torque < 0: torque = 0

        # Store Peaks
        if hp > self.peak_hp: self.peak_hp = hp
        if torque > self.peak_torque: self.peak_torque = torque

        # Update State
        self.last_time = current_time
        self.last_speed_ms = speed_ms

        # Return values for Graphing
        return hp, torque