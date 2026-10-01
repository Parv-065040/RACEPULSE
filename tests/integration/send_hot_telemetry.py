"""
Throwaway test producer - sends one overheated telemetry event plus
matching weather and timing, to verify RC-002 Vehicle Risk without
waiting 30+ laps for the simulator's normal thermal drift to reach it.
Not part of the real pipeline - for verification only.
"""
import json
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: k.encode(),
    value_serializer=lambda v: json.dumps(v).encode(),
)

CAR_ID = "CAR_01"
now = datetime.now(timezone.utc).isoformat()

def base(lap_number):
    return {"event_id": str(uuid.uuid4()), "event_time": now, "car_id": CAR_ID, "lap_number": lap_number}

weather_event = {
    **base(1),
    "condition": "DRY",
    "rain_intensity": 0.0,
    "track_wetness": 0.0,
    "track_grip": 1.0,
}

telemetry_event = {
    **base(1),
    "speed_kmh": 200.0,
    "rpm": 9000,
    "throttle_pct": 80.0,
    "brake_pct": 10.0,
    "gear": 7,
    "engine_temperature_c": 140.0,
    "brake_temperature_c": 750.0,
    "battery_temperature_c": 90.0,
    "fuel_kg": 80.0,
    "energy_kwh": 3.0,
    "location_km": 5.0,
}

timing_event = {
    **base(1),
    "lap_time_ms": 90000,
    "gap_to_leader_ms": 0,
    "position": 1,
}

for topic, event in [("race.weather", weather_event), ("race.telemetry", telemetry_event), ("race.timing", timing_event)]:
    producer.send(topic, key=CAR_ID, value=event)
    producer.flush()
    print(f"sent to {topic}: {event}")

print("\nExpected: RC-001 (track_risk) severity=none (dry weather), RC-002 (vehicle_risk) severity=critical (overheated)")