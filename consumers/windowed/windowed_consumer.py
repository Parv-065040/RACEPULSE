"""
Windowed streaming consumer.

KPI-003:
Average Vehicle Speed per event-time tumbling window.

Pipeline:
Kafka -> ValidationGate -> TumblingWindow -> Watermark/Idle Flush
      -> KPI -> MySQL
"""

from __future__ import annotations
import os

import hashlib
import time
from datetime import datetime, timedelta, timezone

from kafka import KafkaConsumer

from database.writer import write_windowed_kpi_result
from engine.config.window_loader import (
    get_allowed_lateness_seconds,
    get_default_window_seconds,
    get_idle_flush_seconds,
    start_window_config_watcher,
)
from engine.formulas.window_average_speed import compute_average_speed
from engine.validation.gate import ValidationGate
from engine.windows.tumbling_window import TumblingWindow


BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "race.telemetry"
GROUP_ID = "windowed-performance-consumer"


def _window_id(car_id: str, window_start) -> str:
    raw = f"{car_id}|{window_start.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _parse_event_time(
    event_time: str | datetime,
) -> datetime:
    if isinstance(event_time, datetime):
        dt = event_time
    else:
        dt = datetime.fromisoformat(
            event_time.replace("Z", "+00:00")
        )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _save_completed_windows(
    completed_windows,
    window: TumblingWindow,
) -> None:
    for completed in completed_windows:
        average_speed = compute_average_speed(
            completed.events
        )

        window_id = _window_id(
            completed.entity_id,
            completed.window_start,
        )

        write_windowed_kpi_result(
            kpi_id="KPI-003",
            window_id=window_id,
            car_id=completed.entity_id,
            window_start=completed.window_start,
            window_end=completed.window_end,
            event_count=completed.count,
            value=average_speed,
            unit="km/h",
            severity="none",
            message=(
                "Average vehicle speed for the completed "
                f"{window.window_size}-second event-time window."
            ),
        )

        print(
            f"KPI-003  car={completed.entity_id}  "
            f"window={completed.window_start.isoformat()} -> "
            f"{completed.window_end.isoformat()}  "
            f"events={completed.count}  "
            f"avg_speed_kmh={average_speed:.2f}  "
            f"[saved]",
            flush=True,
        )


def process_event(
    gate: ValidationGate,
    window: TumblingWindow,
    message,
    latest_event_times: dict[str, datetime],
    last_event_received_at: dict[str, float],
) -> None:
    """
    Validate and process one Kafka telemetry event.
    """

    event = gate.check(
        message.topic,
        message.key,
        message.value,
    )

    if event is None:
        return

    current_window_seconds = (
        get_default_window_seconds()
    )

    if current_window_seconds != window.window_size:
        print(
            f"[windowed-consumer] resizing "
            f"{window.window_size}s -> "
            f"{current_window_seconds}s",
            flush=True,
        )

        window.resize(current_window_seconds)

    event_time = _parse_event_time(
        event["event_time"]
    )

    car_id = event["car_id"]

    previous_max = latest_event_times.get(car_id)

    if (
        previous_max is None
        or event_time > previous_max
    ):
        latest_event_times[car_id] = event_time

    # Track wall-clock arrival time separately from event time.
    last_event_received_at[car_id] = (
        time.monotonic()
    )

    results = window.add(
        car_id,
        event_time,
        event,
    )

    _save_completed_windows(
        results,
        window,
    )


def finalize_idle_windows(
    window: TumblingWindow,
    latest_event_times: dict[str, datetime],
    last_event_received_at: dict[str, float],
) -> None:
    """
    Finalize open windows when a telemetry stream becomes idle.

    The watermark is derived from the latest event-time observed
    for the car plus one complete window, minus/plus the configured
    lateness policy.

    With allowed_lateness_seconds = 0:

        watermark =
            latest_event_time + window_size

    This allows the final active window to be persisted when the
    producer stops sending events.
    """

    idle_flush_seconds = (
        get_idle_flush_seconds()
    )

    allowed_lateness_seconds = (
        get_allowed_lateness_seconds()
    )

    now = time.monotonic()

    for car_id, max_event_time in list(
        latest_event_times.items()
    ):
        last_received = (
            last_event_received_at.get(
                car_id,
                now,
            )
        )

        idle_for = now - last_received

        if idle_for < idle_flush_seconds:
            continue

        watermark = (
            max_event_time
            + timedelta(
                seconds=(
                    window.window_size
                    + allowed_lateness_seconds
                )
            )
        )

        results = window.advance_watermark(
            car_id,
            watermark,
        )

        if results:
            print(
                f"[windowed-consumer] idle finalization "
                f"car={car_id} "
                f"idle={idle_for:.1f}s "
                f"watermark={watermark.isoformat()}",
                flush=True,
            )

            _save_completed_windows(
                results,
                window,
            )

        # Prevent repeated processing of the same idle period.
        last_event_received_at[car_id] = now


def run() -> None:
    start_window_config_watcher()

    window = TumblingWindow(
        get_default_window_seconds()
    )

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=None,
        key_deserializer=lambda k: (
            k.decode("utf-8")
            if k
            else None
        ),
    )

    gate = ValidationGate()

    latest_event_times: dict[
        str,
        datetime,
    ] = {}

    last_event_received_at: dict[
        str,
        float,
    ] = {}

    print(
        f"[windowed-consumer] listening on {TOPIC} "
        f"with {window.window_size}s tumbling windows "
        f"| idle-flush="
        f"{get_idle_flush_seconds()}s "
        f"| lateness="
        f"{get_allowed_lateness_seconds()}s",
        flush=True,
    )

    try:
        while True:
            records = consumer.poll(
                timeout_ms=1000
            )

            for _tp, messages in records.items():
                for message in messages:
                    process_event(
                        gate=gate,
                        window=window,
                        message=message,
                        latest_event_times=(
                            latest_event_times
                        ),
                        last_event_received_at=(
                            last_event_received_at
                        ),
                    )

            finalize_idle_windows(
                window=window,
                latest_event_times=(
                    latest_event_times
                ),
                last_event_received_at=(
                    last_event_received_at
                ),
            )

    finally:
        consumer.close()


if __name__ == "__main__":
    run()

