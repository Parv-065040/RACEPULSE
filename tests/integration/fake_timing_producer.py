"""
Throwaway test producer for race.timing -- NOT the real producer.
Awantika owns the real one under producers/timing/. This exists only
to unblock consumer development before her producer is ready.
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

CAR_ID = "CAR_01"

def make_event(lap_number: int, lap_time_ms: int) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": CAR_ID,
        "lap_number": lap_number,
        "lap_time_ms": lap_time_ms,
        "gap_to_leader_ms": 0,
        "position": 1,
    }

if __name__ == "__main__":
    lap = 1
    while True:
        event = make_event(lap, lap_time_ms=90000 + (lap * 150))
        producer.send("race.timing", key=CAR_ID.encode("utf-8"), value=event)
        producer.flush()
        print(f"sent: {event}")
        lap += 1
        time.sleep(2)
