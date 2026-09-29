from datetime import datetime, timezone
from uuid import uuid4

from simulator.state import CarState


def build_tyre_event(car: CarState) -> dict:
    tyre = car.tyre

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number,
        "compound": tyre.compound,
        "age_laps": tyre.age_laps,
        "wear": tyre.wear,
        "grip": tyre.grip,
        "degradation_per_lap": tyre.degradation_per_lap,
    }