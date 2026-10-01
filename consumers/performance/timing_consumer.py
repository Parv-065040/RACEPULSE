"""
Performance consumer - Parv's ownership.
Reads race.timing, validates against the central ValidationGate,
computes KPI-001 (Lap Pace Delta) and KPI-002 (Gap Trend) per car,
persists results to MySQL, raises alerts on warning/critical severity,
routes invalid events to system.dlq, monitors stale streams, and
live-reloads thresholds from config/thresholds.yaml.
"""
from kafka import KafkaConsumer

from engine.config.loader import start_config_watcher
from engine.formulas.lap_pace_delta import compute_lap_pace_delta
from engine.formulas.gap_trend import compute_gap_trend
from engine.alerts.alert_engine import raise_alert_if_needed
from engine.alerts.stale_stream_monitor import (
    mark_seen,
    mark_retired,
    check_for_stale_cars,
)
from engine.validation.gate import ValidationGate
from database.writer import write_kpi_result, write_gap_trend_result

POLL_TIMEOUT_MS = 5000


def process_event(gate: ValidationGate, message) -> None:
    # Central validation handles:
    # - raw bytes / JSON parsing
    # - schema validation
    # - known entity validation
    # - duplicate detection
    # - DLQ routing
    event = gate.check(
        message.topic,
        message.key,
        message.value,
    )

    if event is None:
        return

    mark_seen(event["car_id"])

    pace_kpi = compute_lap_pace_delta(
        event["car_id"],
        event["lap_time_ms"],
    )
    write_kpi_result(pace_kpi, event)

    if pace_kpi["severity"] != "none":
        raise_alert_if_needed(pace_kpi, event)

    gap_kpi = compute_gap_trend(
        event["car_id"],
        event["gap_to_leader_ms"],
    )
    write_gap_trend_result(gap_kpi, event)

    pace_flag = (
        " [ALERT RAISED]"
        if pace_kpi["severity"] != "none"
        else ""
    )

    print(
        f"KPI-001  car={pace_kpi['car_id']}  "
        f"lap={event['lap_number']}  "
        f"lap_time_ms={pace_kpi['lap_time_ms']}  "
        f"best={pace_kpi['best_lap_time_ms']}  "
        f"delta_ms={pace_kpi['delta_ms']}  "
        f"severity={pace_kpi['severity']}  [saved]{pace_flag}"
    )

    print(
        f"KPI-002  car={gap_kpi['car_id']}  "
        f"lap={event['lap_number']}  "
        f"gap_ms={gap_kpi['gap_to_leader_ms']}  "
        f"trend_ms_per_lap={gap_kpi['trend_ms_per_lap']}  "
        f"severity={gap_kpi['severity']}  [saved]"
    )


def main():
    start_config_watcher()

    consumer = KafkaConsumer(
        "race.timing",
        "race.incidents",
        bootstrap_servers="localhost:9092",
        group_id="performance-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=None,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
    )

    gate = ValidationGate()

    print(
        f"performance-consumer listening on race.timing "
        f"(polling every {POLL_TIMEOUT_MS}ms) ..."
    )

    while True:
        records = consumer.poll(timeout_ms=POLL_TIMEOUT_MS)

        if not records:
            check_for_stale_cars()
            continue

        for _topic_partition, messages in records.items():
            for message in messages:
                process_event(gate, message)

        check_for_stale_cars()


if __name__ == "__main__":
    main()
