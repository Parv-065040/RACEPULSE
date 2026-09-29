"""
Streaming infrastructure monitor.

Checks Kafka consumer-group lag and database reachability, then writes a
small operational time series to MySQL. This is intentionally separate
from race analytics so an unhealthy analytics consumer cannot hide its own
health state.
"""
from __future__ import annotations
import time
from kafka import KafkaAdminClient, KafkaConsumer
from database.connection import get_connection

BOOTSTRAP="localhost:9092"
GROUPS=["performance-consumer","strategy-consumer","race-control-consumer","commercial-consumer"]
TOPICS=["race.timing","race.tyres","race.weather","race.pitstops","race.telemetry","race.incidents","business.fans","business.sponsors"]

def group_lag(admin, group):
    try:
        offsets=admin.list_consumer_group_offsets(group)
    except Exception:
        return None
    lag=0
    for tp,offset_meta in offsets.items():
        try:
            end=KafkaConsumer(bootstrap_servers=BOOTSTRAP).end_offsets([tp])[tp]
            lag += max(0,end-offset_meta.offset)
        except Exception:
            continue
    return lag

def run(interval=5):
    while True:
        observed=time.time()
        admin=KafkaAdminClient(bootstrap_servers=BOOTSTRAP,client_id="racepulse-health")
        try:
            conn=get_connection()
            with conn.cursor() as cur:
                for group in GROUPS:
                    lag=group_lag(admin,group)
                    status="healthy" if lag is not None and lag < 100 else "warning" if lag is not None else "unknown"
                    cur.execute(
                        "INSERT INTO stream_health(component,consumer_group,lag,status,message) VALUES (%s,%s,%s,%s,%s)",
                        ("kafka-consumer",group,lag,status,
                         "Consumer group lag within demo threshold." if status=="healthy" else "Review consumer health and Kafka lag.")
                    )
                conn.commit(); conn.close()
        finally:
            admin.close()
        time.sleep(interval)

if __name__=="__main__": run()
