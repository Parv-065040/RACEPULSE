"""
Sends one deliberately malformed event to race.timing, to test DLQ routing.
Throwaway test tool - not part of the real pipeline.
"""
import json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: k,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

bad_event = {
    "event_id": "bad-event-001",
    "event_time": "2026-09-26T18:00:00.000Z",
    "car_id": "CAR_01",
    "lap_number": "not-a-number",
    "lap_time_ms": 90000,
    "gap_to_leader_ms": 0,
    "position": 1,
}

producer.send("race.timing", key=b"CAR_01", value=bad_event)
producer.flush()
print("sent malformed event:", bad_event)