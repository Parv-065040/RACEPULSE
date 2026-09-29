"""
Strategy analytics consumer for tyres, weather, timing and pit-stop streams.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from database.connection import get_connection
from engine.validation.gate import ValidationGate

BOOTSTRAP = "localhost:9092"
TOPICS = ["race.timing", "race.tyres", "race.weather", "race.pitstops"]
GROUP_ID = "strategy-consumer"
STATE: dict[str, dict] = {}

INSERT_SQL = """
INSERT INTO strategy_results
    (kpi_id, event_id, car_id, lap_number, value, severity, message, event_time)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    value=VALUES(value), severity=VALUES(severity),
    message=VALUES(message), event_time=VALUES(event_time)
"""

def severity(value: float, warning: float, critical: float) -> str:
    if value >= critical: return "critical"
    if value >= warning: return "warning"
    return "none"

def compute_signals(state: dict) -> list[dict]:
    timing, tyres = state.get("timing"), state.get("tyres")
    if not timing or not tyres:
        return []
    weather = state.get("weather") or {}
    pit = state.get("pitstops") or {}
    best = state.get("best_lap_time_ms", timing["lap_time_ms"])
    pace_delta_s = max(0.0, (timing["lap_time_ms"] - best) / 1000.0)
    grip_loss = max(0.0, 1.0 - float(tyres["grip"]))
    degradation = float(tyres["degradation_per_lap"])
    wetness = float(weather.get("track_wetness", 0.0))
    risk = degradation * 5.0 + grip_loss * 2.0 + pace_delta_s * 0.4 + wetness * 0.5
    pit_signal = min(1.0, risk / 2.0 + (0.5 if pit.get("pit_stop") else 0.0))
    return [
        {"kpi_id":"STR-001","value":risk,"warn":0.75,"crit":1.5,
         "message":"Tyre, pace and track conditions indicate increasing strategy risk."},
        {"kpi_id":"STR-002","value":pit_signal,"warn":0.6,"crit":0.85,
         "message":"Current race context warrants pit-window review."},
    ]

def process_message(gate: ValidationGate, message, alert_producer: KafkaProducer) -> None:
    event = gate.check(message.topic, message.key, message.value)
    if event is None: return
    car_id = event["car_id"]
    state = STATE.setdefault(car_id, {})
    state[message.topic.split(".",1)[1]] = event
    if message.topic == "race.timing":
        state["timing"] = event
        old = state.get("best_lap_time_ms")
        state["best_lap_time_ms"] = event["lap_time_ms"] if old is None else min(old, event["lap_time_ms"])
    signals = compute_signals(state)
    if not signals: return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for s in signals:
                sev = severity(s["value"], s["warn"], s["crit"])
                event_id = str(uuid.uuid4())
                cur.execute(INSERT_SQL, (s["kpi_id"], event_id, car_id, event["lap_number"],
                                         round(s["value"],4), sev, s["message"],
                                         datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)))
                if sev != "none":
                    alert_producer.send("analytics.alerts", key=car_id.encode(), value={
                        "kpi_id":s["kpi_id"],"event_id":event_id,"car_id":car_id,
                        "severity":sev,"signal":s["message"],"value":round(s["value"],4),
                        "event_time":event["event_time"]})
        conn.commit()
        alert_producer.flush()
    finally:
        conn.close()

def run() -> None:
    consumer = KafkaConsumer(*TOPICS, bootstrap_servers=BOOTSTRAP, group_id=GROUP_ID,
                             auto_offset_reset="latest", enable_auto_commit=True)
    alert_producer = KafkaProducer(bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k:k, value_serializer=lambda v:json.dumps(v).encode())
    gate = ValidationGate()
    print(f"[strategy-consumer] listening on {TOPICS}", flush=True)
    try:
        while True:
            for _tp, messages in consumer.poll(timeout_ms=1000).items():
                for message in messages:
                    process_message(gate, message, alert_producer)
    finally:
        consumer.close(); alert_producer.close()

if __name__ == "__main__": run()
