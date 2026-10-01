"""
Commercial analytics consumer for business.fans and business.sponsors.

KPIs:
  COM-001 Fan Engagement Rate
  COM-002 Sponsor Exposure Rate
  COM-003 Sponsor Conversion Rate

The consumer keeps the raw business streams intact and persists derived
rates for Grafana. Values are explicitly NULL-safe: no event is interpreted
as zero activity.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from database.connection import get_connection
from engine.validation.gate import ValidationGate
from engine.config.loader import get_config, start_config_watcher
from engine.rules.severity_rules import evaluate_severity

BOOTSTRAP="localhost:9092"
TOPICS=["business.fans","business.sponsors"]
GROUP_ID="commercial-consumer"
INSERT_SQL="""
INSERT INTO commercial_results
(kpi_id,event_id,car_id,entity_id,lap_number,value,unit,severity,message,event_time)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE value=VALUES(value), severity=VALUES(severity),
message=VALUES(message), event_time=VALUES(event_time)
"""

def commercial_severity(kpi_id, value):
    cfg = get_config()
    block = cfg["commercial"][kpi_id]
    return evaluate_severity(
        value,
        block["warning"],
        block["critical"],
    )


def process_message(gate, message, alert_producer):
    event=gate.check(message.topic,message.key,message.value)
    if event is None: return
    if message.topic=="business.fans":
        total=max(1,event["viewers"])
        interactions=event["likes"]+event["comments"]+event["shares"]+event["merch_clicks"]
        signals=[
            ("COM-001",interactions/total,"rate",
             "Fan engagement rate for the current event window."),
        ]
        entity_id=event["car_id"]
    else:
        impressions=max(1,event["impressions"])
        ctr=event["clicks"]/impressions
        cvr=event["conversions"]/max(1,event["clicks"])
        signals=[
            ("COM-002",event["visibility_seconds"],"seconds",
             "Sponsor visibility exposure for the current event window."),
            ("COM-003",cvr,"rate",
             "Sponsor conversion rate for the current event window."),
        ]
        entity_id=event["sponsor_id"]

    conn=get_connection()
    try:
        with conn.cursor() as cur:
            for kpi_id,value,unit,message_text in signals:
                eid=str(uuid.uuid4())
                severity = commercial_severity(kpi_id, value) if unit == "rate" else "none"
                cur.execute(INSERT_SQL,(
                    kpi_id,eid,event["car_id"],entity_id,event["lap_number"],
                    round(value,6),unit,severity,message_text,
                    datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)))
                if severity!="none":
                    alert_producer.send("analytics.alerts",key=event["car_id"].encode(),
                        value={"kpi_id":kpi_id,"event_id":eid,"car_id":event["car_id"],
                               "severity":severity,"signal":message_text,"value":round(value,6),
                               "event_time":event["event_time"]})
        conn.commit(); alert_producer.flush()
    finally:
        conn.close()

def run():
    consumer=KafkaConsumer(*TOPICS,bootstrap_servers=BOOTSTRAP,group_id=GROUP_ID,
                           auto_offset_reset="latest",enable_auto_commit=True)
    producer=KafkaProducer(bootstrap_servers=BOOTSTRAP,key_serializer=lambda k:k,
                           value_serializer=lambda v:json.dumps(v).encode())
    gate=ValidationGate()
    start_config_watcher()
    print(f"[commercial-consumer] listening on {TOPICS}",flush=True)
    try:
        while True:
            for _tp,messages in consumer.poll(timeout_ms=1000).items():
                for message in messages: process_message(gate,message,producer)
    finally:
        consumer.close(); producer.close()

if __name__=="__main__": run()
