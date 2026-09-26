"""
Performance consumer - Parv's ownership.
Reads race.timing, validates against the event contract, computes
Lap Pace Delta KPI per car, prints each result.
"""
import json
from kafka import KafkaConsumer
from engine.formulas.lap_pace_delta import compute_lap_pace_delta

REQUIRED_FIELDS = {
    "event_id": str,
    "event_time": str,
    "car_id": str,
    "lap_number": int,
    "lap_time_ms": int,
    "gap_to_leader_ms": int,
    "position": int,
}

def validate(event: dict) -> list[str]:
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in event:
            errors.append(f"missing field: {field}")
        elif not isinstance(event[field], expected_type):
            errors.append(f"wrong type for {field}: expected {expected_type.__name__}, got {type(event[field]).__name__}")
    return errors

def main():
    consumer = KafkaConsumer(
        "race.timing",
        bootstrap_servers="localhost:9092",
        group_id="performance-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )

    print("performance-consumer listening on race.timing ...")
    for message in consumer:
        event = message.value
        errors = validate(event)
        if errors:
            print(f"INVALID event from key={message.key}: {errors}")
            continue

        kpi = compute_lap_pace_delta(event["car_id"], event["lap_time_ms"])
        print(f"KPI-001  car={kpi['car_id']}  lap={event['lap_number']}  "
              f"lap_time_ms={kpi['lap_time_ms']}  best={kpi['best_lap_time_ms']}  "
              f"delta_ms={kpi['delta_ms']}  severity={kpi['severity']}")

if __name__ == "__main__":
    main()
