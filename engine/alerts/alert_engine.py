"""
Alert generation - Parv's ownership (engine/alerts/).
Two kinds of alerts:
  1. KPI-severity alerts (warning/critical lap pace delta)
  2. Stale-stream alerts (a car has stopped sending data)
Both publish to analytics.alerts AND persist to MySQL, idempotently.
"""
import json
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer
from database.connection import get_connection

_producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: k,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

_INSERT_ALERT = """
INSERT INTO alerts
    (kpi_id, event_id, car_id, severity, message, delta_ms, event_time)
VALUES
    (%s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    severity = VALUES(severity),
    message = VALUES(message),
    delta_ms = VALUES(delta_ms),
    event_time = VALUES(event_time)
"""

_connection = None

def _get_conn():
    global _connection
    if _connection is None or not _connection.open:
        _connection = get_connection()
    return _connection

def _publish_and_store(kpi_id, event_id, car_id, severity, message, delta_ms, event_time_iso):
    event_time = datetime.fromisoformat(event_time_iso).replace(tzinfo=None)

    alert_record = {
        "kpi_id": kpi_id,
        "event_id": event_id,
        "car_id": car_id,
        "severity": severity,
        "message": message,
        "delta_ms": delta_ms,
        "event_time": event_time_iso,
    }
    _producer.send("analytics.alerts", key=car_id.encode("utf-8"), value=alert_record)
    _producer.flush()

    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(_INSERT_ALERT, (
            kpi_id, event_id, car_id, severity, message, delta_ms, event_time,
        ))

def _build_message(kpi: dict) -> str:
    return (f"Car {kpi['car_id']} lap pace delta {kpi['delta_ms']}ms "
            f"({kpi['severity'].upper()}) vs best {kpi['best_lap_time_ms']}ms")

def raise_alert_if_needed(kpi: dict, event: dict) -> None:
    if kpi["severity"] == "none":
        return
    message = _build_message(kpi)
    _publish_and_store(
        kpi["kpi_id"], event["event_id"], kpi["car_id"],
        kpi["severity"], message, kpi["delta_ms"], event["event_time"],
    )

def raise_stale_stream_alert(car_id: str, seconds_since_last_seen: float) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())
    message = f"Car {car_id} stream is STALE - no data for {seconds_since_last_seen:.1f}s"
    _publish_and_store(
        "SYS-STALE", event_id, car_id, "critical", message,
        int(seconds_since_last_seen * 1000), now_iso,
    )