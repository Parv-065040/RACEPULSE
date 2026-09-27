from datetime import datetime, timezone
from uuid import uuid4

from simulator.state import CarState


def build_incident_event(
    car: CarState,
    lap_number: int | None = None,
) -> dict:
    incident = car.incident

    event_lap = (
        car.lap_number
        if lap_number is None
        else lap_number
    )

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": event_lap,
        "incident_type": incident.incident_type,
        "active": incident.active,
        "severity": incident.severity,
        "description": incident.description,
    }