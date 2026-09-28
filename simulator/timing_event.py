from datetime import datetime, timezone
from uuid import uuid4

from simulator.state import CarState


def build_timing_event(car: CarState) -> dict:
    """
    Convert the current car state into a race.timing event.

    The returned structure follows docs/event-contract.md.
    """

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number,
        "lap_time_ms": car.lap_time_ms,
        "gap_to_leader_ms": car.gap_to_leader_ms,
        "position": car.position,
    }