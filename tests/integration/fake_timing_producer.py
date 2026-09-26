"""
Throwaway test producer for race.timing - now simulating 3 cars.
NOT the real producer; Awantika owns producers/timing/.
Each car has its own lap counter and its own gradual lap-time trend,
so per-car state in the KPI engine gets properly exercised.
"""
import json
import time
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: k,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

CARS = {
    "CAR_01": {"lap": 0, "base_ms": 90000, "degrade_ms": 150},
    "CAR_02": {"lap": 0, "base_ms": 91200, "degrade_ms": 80},
    "CAR_03": {"lap": 0, "base_ms": 89800, "degrade_ms": 220},
}

def make_event(car_id: str, lap_number: int, lap_time_ms: int) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car_id,
        "lap_number": lap_number,
        "lap_time_ms": lap_time_ms,
        "gap_to_leader_ms": 0,
        "position": 1,
    }

if __name__ == "__main__":
    while True:
        for car_id, state in CARS.items():
            state["lap"] += 1
            lap_time_ms = state["base_ms"] + (state["lap"] * state["degrade_ms"])
            event = make_event(car_id, state["lap"], lap_time_ms)
            producer.send("race.timing", key=car_id.encode("utf-8"), value=event)
            producer.flush()
            print(f"sent: {event}")
        time.sleep(2)