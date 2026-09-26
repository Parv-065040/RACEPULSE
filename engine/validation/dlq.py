"""
Dead Letter Queue writer - shared responsibility (Parv/Navroop).
Wraps a malformed/invalid event with metadata about why it failed
and publishes it to system.dlq for later inspection.
"""
import json
from datetime import datetime, timezone
from kafka import KafkaProducer

_producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def send_to_dlq(source_topic: str, raw_key, raw_value, errors: list[str]) -> None:
    dlq_record = {
        "source_topic": source_topic,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "key": raw_key,
        "raw_value": raw_value,
        "errors": errors,
    }
    _producer.send("system.dlq", value=dlq_record)
    _producer.flush()