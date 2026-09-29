from datetime import datetime, timezone
from uuid import uuid4

from simulator.state import CarState


def build_telemetry_event(car: CarState) -> dict:
    telemetry = car.telemetry

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number,
        "speed_kmh": telemetry.speed_kmh,
        "rpm": telemetry.rpm,
        "throttle_pct": telemetry.throttle_pct,
        "brake_pct": telemetry.brake_pct,
        "gear": telemetry.gear,
        "engine_temperature_c": telemetry.engine_temperature_c,
        "brake_temperature_c": telemetry.brake_temperature_c,
        "battery_temperature_c": telemetry.battery_temperature_c,
        "fuel_kg": telemetry.fuel_kg,
        "energy_kwh": telemetry.energy_kwh,
        "location_km": telemetry.location_km,
    }