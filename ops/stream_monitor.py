import os
"""Kafka consumer lag and MySQL health monitor."""
import time
from kafka import KafkaAdminClient, KafkaConsumer
from database.connection import get_connection

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUPS=["performance-consumer","strategy-consumer","race-control-consumer","commercial-consumer"]
LAG_WARNING=100

def group_lag(admin,group):
    try:
        offsets=admin.list_consumer_group_offsets(group)
    except Exception:
        return None
    consumer=KafkaConsumer(bootstrap_servers=BOOTSTRAP)
    try:
        end_offsets=consumer.end_offsets(list(offsets))
        return sum(max(0,end_offsets[tp]-meta.offset) for tp,meta in offsets.items())
    finally:
        consumer.close()

def run(interval=5):
    while True:
        admin=KafkaAdminClient(bootstrap_servers=BOOTSTRAP,client_id="racepulse-health")
        conn=None
        try:
            conn=get_connection()
            with conn.cursor() as cur:
                for group in GROUPS:
                    lag=group_lag(admin,group)
                    status="healthy" if lag is not None and lag<LAG_WARNING else "warning" if lag is not None else "unknown"
                    message=("Consumer group lag within threshold." if status=="healthy"
                             else "Consumer lag requires investigation." if status=="warning"
                             else "Consumer group offsets unavailable.")
                    cur.execute(
                        "INSERT INTO stream_health(component,consumer_group,lag,status,message) VALUES (%s,%s,%s,%s,%s)",
                        ("kafka-consumer",group,lag,status,message))
                    if status!="healthy":
                        cur.execute(
                            "INSERT INTO infra_alerts(signal,severity,component,message) VALUES (%s,%s,%s,%s)",
                            ("CONSUMER_LAG","warning" if status=="warning" else "critical",
                             group,message))
                conn.commit()
        except Exception as exc:
            if conn:
                conn.rollback()
            print(f"[stream-monitor] health check failed: {exc}",flush=True)
        finally:
            if conn: conn.close()
            admin.close()
        time.sleep(interval)

if __name__=="__main__": run()

