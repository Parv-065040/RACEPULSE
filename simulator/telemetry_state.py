from dataclasses import dataclass


@dataclass
class TelemetryState:
    speed_kmh: float = 210.0
    rpm: int = 9000
    throttle_pct: float = 80.0
    brake_pct: float = 0.0
    gear: int = 7
    engine_temperature_c: float = 95.0
    brake_temperature_c: float = 450.0
    battery_temperature_c: float = 40.0
    fuel_kg: float = 100.0
    energy_kwh: float = 4.0
    location_km: float = 0.0

    def update(
        self,
        lap_time_ms: int,
        track_grip: float,
    ) -> "TelemetryState":
        grip = max(0.0, min(1.0, track_grip))

        performance_factor = max(
            0.7,
            min(
                1.1,
                90000 / lap_time_ms,
            ),
        )

        self.speed_kmh = (
            210.0
            * performance_factor
            * (0.85 + 0.15 * grip)
        )

        self.rpm = int(
            8500
            + (self.speed_kmh - 180.0) * 20
        )

        self.rpm = max(
            6000,
            min(12000, self.rpm),
        )

        self.throttle_pct = max(
            50.0,
            min(
                100.0,
                70.0 + (self.speed_kmh - 180.0) * 0.4,
            ),
        )

        self.brake_pct = max(
            0.0,
            min(
                40.0,
                (210.0 - self.speed_kmh) * 0.5,
            ),
        )

        self.gear = max(
            4,
            min(
                8,
                int(self.speed_kmh / 35),
            ),
        )

        self.engine_temperature_c += (
            self.throttle_pct * 0.01
        )

        self.brake_temperature_c += (
            self.brake_pct * 0.8
        )

        self.battery_temperature_c += (
            self.throttle_pct * 0.002
        )

        self.fuel_kg = max(
            0.0,
            self.fuel_kg - 1.2,
        )

        self.energy_kwh = max(
            0.0,
            self.energy_kwh - 0.08,
        )

        self.location_km += 5.0

        return self


def create_default_telemetry() -> TelemetryState:
    return TelemetryState()