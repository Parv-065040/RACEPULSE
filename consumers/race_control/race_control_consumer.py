"""
Race-control consumer for telemetry, timing, weather and incident streams.

Mechanical-failure incidents mark a car retired; retired cars are excluded
from risk calculations and are explicitly exposed to the stale monitor.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from database.connection import get_connection
from engine.validation.gate import ValidationGate
from engine.alerts.stale_stream_monitor import mark_retired, mark_seen
from engine.config.loader import get_config, start_config_watcher

BOOTSTRAP="localhost:9092"
TOPICS=["race.telemetry","race.timing","race.weather","race.incidents"]
GROUP_ID="race-control-consumer"
STATE: dict[str,dict] = {}

INSERT_SQL = """
INSERT INTO race_control_results
    (kpi_id,event_id,car_id,lap_number,value,severity,message,event_time)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE value=VALUES(value), severity=VALUES(severity),
message=VALUES(message), event_time=VALUES(event_time)
"""

def sev(value, warning=0.6, critical=1.2):
    return "critical" if value>=critical else "warning" if value>=warning else "none"

def process_message(gate, message, alert_producer):
    event=gate.check(message.topic,message.key,message.value)
    if event is None: return
    car_id=event["car_id"]; st=STATE.setdefault(car_id,{})
    st[message.topic]=event
    mark_seen(car_id)
    if message.topic=="race.incidents" and event["active"] and event["incident_type"]=="MECHANICAL_FAILURE":
        st["retired"]=True
        mark_retired(car_id)
        print(f"[race-control] retired car={car_id}", flush=True)
        return
    if st.get("retired"): return
    telemetry=st.get("race.telemetry",{}); weather=st.get("race.weather",{}); timing=st.get("race.timing",{}); incident=st.get("race.incidents",{})
    track_risk=float(weather.get("track_wetness",0))*0.7 + max(0,1-float(weather.get("track_grip",1)))*0.7
    if incident.get("active") and incident.get("incident_type") in {"SAFETY_CAR","YELLOW_FLAG"}: track_risk += 0.5
    vehicle_risk=max(0,(float(telemetry.get("engine_temperature_c",0))-105)/30)+max(0,(float(telemetry.get("brake_temperature_c",0))-500)/250)+max(0,(float(telemetry.get("battery_temperature_c",0))-55)/20)
    if not timing: return
    cfg=get_config()["race_control"]
    signals=[("RC-001",track_risk,"Track conditions/race control indicate elevated operational risk.",cfg["track_risk"]["warning"],cfg["track_risk"]["critical"]),
             ("RC-002",vehicle_risk,"Vehicle telemetry indicates elevated thermal/operational risk.",cfg["vehicle_risk"]["warning"],cfg["vehicle_risk"]["critical"])]
    conn=get_connection()
    try:
        with conn.cursor() as cur:
            for kpi_id,value,msg in signals:
                level=sev(value); eid=str(uuid.uuid4())
                cur.execute(INSERT_SQL,(kpi_id,eid,car_id,event.get("lap_number",timing.get("lap_number",0)),
                                        round(value,4),level,msg,datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)))
                if level!="none":
                    alert_producer.send("analytics.alerts",key=car_id.encode(),value={
                        "kpi_id":kpi_id,"event_id":eid,"car_id":car_id,"severity":level,
                        "signal":msg,"value":round(value,4),"event_time":event["event_time"]})
        conn.commit(); alert_producer.flush()
    finally: conn.close()

def run():
    consumer=KafkaConsumer(*TOPICS,bootstrap_servers=BOOTSTRAP,group_id=GROUP_ID,
                           auto_offset_reset="latest",enable_auto_commit=True)
    producer=KafkaProducer(bootstrap_servers=BOOTSTRAP,key_serializer=lambda k:k,
                           value_serializer=lambda v:json.dumps(v).encode())
    gate=ValidationGate()
    print(f"[race-control-consumer] listening on {TOPICS}",flush=True)
    try:
        while True:
            for _tp,messages in consumer.poll(timeout_ms=1000).items():
                for message in messages: process_message(gate,message,producer)
    finally:
        consumer.close(); producer.close()

if __name__=="__main__": run()
