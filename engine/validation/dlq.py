"""Dead-letter queue publisher with a best-effort MySQL audit record."""
import json
from datetime import datetime, timezone
from kafka import KafkaProducer
from database.connection import get_connection

_producer=None

def _get_producer():
    global _producer
    if _producer is None:
        _producer=KafkaProducer(bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode())
    return _producer

def send_to_dlq(source_topic, raw_key, raw_value, errors):
    failed_at=datetime.now(timezone.utc)
    record={"source_topic":source_topic,"failed_at":failed_at.isoformat(),
            "key":raw_key,"raw_value":raw_value,"errors":errors}
    _get_producer().send("system.dlq",value=record)
    _get_producer().flush()
    try:
        conn=get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO dlq_events(source_topic,raw_key,errors,failed_at) VALUES (%s,%s,%s,%s)",
                (source_topic,raw_key,json.dumps(errors),failed_at.replace(tzinfo=None)))
        conn.commit(); conn.close()
    except Exception as exc:
        print(f"DLQ audit write failed (Kafka DLQ already published): {exc}",flush=True)
