"""
Dead Letter Queue writer - shared responsibility (Parv/Navroop).
Wraps a malformed/invalid event with metadata about why it failed
and publishes it to system.dlq for later inspection.

The KafkaProducer is created lazily (on first send_to_dlq call), not
at import time. This was changed after discovering that a module-level
KafkaProducer() made this module un-importable without Kafka already
running - which broke automated test collection, and is generally bad
practice (importing a module should never have network side effects).
"""
import json
from datetime import datetime, timezone
from kafka import KafkaProducer

_producer = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


def send_to_dlq(source_topic: str, raw_key, raw_value, errors: list[str]) -> None:
    dlq_record = {
        "source_topic": source_topic,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "key": raw_key,
        "raw_value": raw_value,
        "errors": errors,
    }
    producer = _get_producer()
    producer.send("system.dlq", value=dlq_record)
    producer.flush()
