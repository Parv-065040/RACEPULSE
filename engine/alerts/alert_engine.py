"""
Alert generation - Parv's ownership (engine/alerts/).
When a KPI result crosses warning/critical severity, this publishes
an alert event to analytics.alerts AND persists it to MySQL, idempotently.
"""
import json
from datetime import datetime
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

def _build_message(kpi: dict) -> str:
    return (f"Car {kpi['car_id']} lap pace delta {kpi['delta_ms']}ms "
            f"({kpi['severity'].upper()}) vs best {kpi['best_lap_time_ms']}ms")

def raise_alert_if_needed(kpi: dict, event: dict) -> None:
    if kpi["severity"] == "none":
        return

    message = _build_message(kpi)
    event_time = datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)

    alert_record = {
        "kpi_id": kpi["kpi_id"],
        "event_id": event["event_id"],
        "car_id": kpi["car_id"],
        "severity": kpi["severity"],
        "message": message,
        "delta_ms": kpi["delta_ms"],
        "event_time": event["event_time"],
    }
    _producer.send("analytics.alerts", key=kpi["car_id"].encode("utf-8"), value=alert_record)
    _producer.flush()

    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(_INSERT_ALERT, (
            kpi["kpi_id"],
            event["event_id"],
            kpi["car_id"],
            kpi["severity"],
            message,
            kpi["delta_ms"],
            event_time,
        ))