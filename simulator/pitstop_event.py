from datetime import datetime, timezone
from uuid import uuid4

from simulator.state import CarState


def build_pitstop_event(car: CarState) -> dict:
    pitstop = car.pitstop

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number,
        "pit_entry": pitstop.pit_entry,
        "pit_stop": pitstop.pit_stop,
        "tyre_change": pitstop.tyre_change,
        "repair": pitstop.repair,
        "pit_exit": pitstop.pit_exit,
    }