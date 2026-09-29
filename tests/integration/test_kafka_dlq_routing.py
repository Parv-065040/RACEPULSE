"""
Integration test: DLQ routing actually publishes to Kafka.

Tests engine.validation.dlq.send_to_dlq directly against the real
Kafka broker - not the full consumer pipeline (that was already proven
manually: a malformed event sent to race.timing correctly appeared on
system.dlq and never reached MySQL). This test isolates just the DLQ
publish step so it can run without needing consumers.performance
running as a separate process.

Requires the real Docker Kafka container running with system.dlq
already created (kafka-topics --create --topic system.dlq ...).

Run with: pytest tests/integration/test_kafka_dlq_routing.py -v
"""
import json
import time
import uuid
from kafka import KafkaConsumer
from conftest import requires_kafka
from engine.validation.dlq import send_to_dlq


@requires_kafka
def test_send_to_dlq_publishes_a_readable_message():
    marker = str(uuid.uuid4())  # unique per test run so we can find our own message
    fake_errors = [f"wrong type for lap_number: expected int, got str ({marker})"]
    fake_raw_value = {"event_id": "bad-event", "lap_number": "not-a-number", "_test_marker": marker}

    send_to_dlq("race.timing", "CAR_TEST", fake_raw_value, fake_errors)

    consumer = KafkaConsumer(
        "system.dlq",
        bootstrap_servers="localhost:9092",
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,  # stop waiting after 5s if nothing new arrives
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    found = False
    for message in consumer:
        record = message.value
        if record.get("raw_value", {}).get("_test_marker") == marker:
            found = True
            assert record["source_topic"] == "race.timing"
            assert record["key"] == "CAR_TEST"
            assert marker in record["errors"][0]
            break
    consumer.close()

    assert found, "did not find our test DLQ message on system.dlq within the timeout"
