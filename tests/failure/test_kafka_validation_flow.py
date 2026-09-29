"""
Failure test against the REAL Kafka stack: bad messages published to
business.fans are read as raw bytes, rejected by ValidationGate and
appear on system.dlq. Skipped automatically if Kafka is not running.

Prerequisites: docker compose up -d, and topics business.fans and
system.dlq created (see docs/event-contract.md / the PR description).

Run with: pytest tests/failure/test_kafka_validation_flow.py -v
"""
import json
import socket
import uuid

import pytest
from kafka import KafkaConsumer, KafkaProducer

from engine.validation.gate import ValidationGate


def _port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


requires_kafka = pytest.mark.skipif(
    not _port_open("localhost", 9092), reason="Kafka not reachable on localhost:9092 - run 'docker compose up -d'"
)


@requires_kafka
def test_bad_business_messages_end_up_on_system_dlq():
    marker = f"navroop-{uuid.uuid4()}"
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    producer.send("business.fans", key=b"CAR_01", value=f'{{"broken json {marker}'.encode())
    producer.send("business.fans", key=b"CAR_99", value=json.dumps({
        "event_id": str(uuid.uuid4()), "event_time": "2026-09-26T10:15:30.000Z", "car_id": "CAR_99",
        "lap_number": 1, "viewers": 1, "app_sessions": 1, "searches": 1, "likes": 1,
        "comments": 1, "shares": 1, "merch_clicks": 1, "_marker": marker,
    }).encode())
    producer.flush()
    producer.close()

    gate = ValidationGate()  # real DLQ sender
    consumer = KafkaConsumer(
        "business.fans", bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest", consumer_timeout_ms=8000,
    )
    for message in consumer:
        if marker.encode() in message.value:
            assert gate.check(message.topic, message.key, message.value) is None
    consumer.close()
    assert gate.stats["invalid"] == 2, "did not see both bad messages - does topic business.fans exist?"

    dlq_consumer = KafkaConsumer(
        "system.dlq", bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest", consumer_timeout_ms=8000,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    found = [m.value for m in dlq_consumer if marker in json.dumps(m.value)]
    dlq_consumer.close()

    assert len(found) == 2, "expected 2 DLQ records for this run's bad messages"
    assert all(r["source_topic"] == "business.fans" for r in found)
    assert all(isinstance(r["raw_value"], dict) for r in found)
