"""
Unit tests for ValidationGate and safe_publish (fake DLQ, no Kafka needed).
Run with: pytest tests/unit/test_validation_gate.py -v
"""
import json
from uuid import uuid4

from engine.validation.gate import ValidationGate
from engine.validation.safe_publish import safe_publish


class FakeDLQ:
    def __init__(self):
        self.records = []

    def __call__(self, source_topic, key, raw_value, errors):
        self.records.append(
            {"source_topic": source_topic, "key": key, "raw_value": raw_value, "errors": errors}
        )


def good_fan(**overrides):
    event = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z",
        "car_id": "CAR_01", "lap_number": 1, "viewers": 1000, "app_sessions": 300,
        "searches": 50, "likes": 120, "comments": 20, "shares": 10, "merch_clicks": 5,
    }
    event.update(overrides)
    return event


def test_valid_bytes_message_is_accepted():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    event = good_fan()
    assert gate.check("business.fans", b"CAR_01", json.dumps(event).encode()) == event
    assert gate.stats == {"accepted": 1, "invalid": 0, "duplicate": 0}
    assert dlq.records == []


def test_invalid_json_goes_to_dlq_with_dict_raw_value():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    assert gate.check("business.fans", b"CAR_01", b"{not json") is None
    assert gate.stats["invalid"] == 1
    record = dlq.records[0]
    assert record["errors"][0].startswith("invalid JSON")
    assert record["raw_value"] == {"_unparseable_payload": "{not json"}
    assert record["key"] == "CAR_01"


def test_invalid_utf8_bytes_do_not_crash_the_gate():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    assert gate.check("business.fans", None, b"\xff\xfe\xfa") is None
    assert len(dlq.records) == 1


def test_json_that_is_not_an_object_goes_to_dlq():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    assert gate.check("business.fans", None, b"[1, 2, 3]") is None
    assert dlq.records[0]["raw_value"] == {"_non_object_payload": [1, 2, 3]}


def test_schema_violation_goes_to_dlq_with_original_event():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    bad = good_fan(likes="lots")
    assert gate.check("business.fans", b"CAR_01", json.dumps(bad).encode()) is None
    assert dlq.records[0]["raw_value"] == bad
    assert dlq.records[0]["errors"] == ["wrong type for likes: expected int, got str"]


def test_duplicate_event_is_dropped_not_dlqd():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    raw = json.dumps(good_fan()).encode()
    assert gate.check("business.fans", b"CAR_01", raw) is not None
    assert gate.check("business.fans", b"CAR_01", raw) is None
    assert gate.stats == {"accepted": 1, "invalid": 0, "duplicate": 1}
    assert dlq.records == []


def test_invalid_event_does_not_poison_dedup_for_its_event_id():
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    eid = str(uuid4())
    assert gate.check("business.fans", None, json.dumps(good_fan(event_id=eid, likes=-1))) is None
    assert gate.check("business.fans", None, json.dumps(good_fan(event_id=eid))) is not None


def test_dlq_failure_does_not_crash_the_gate():
    def broken_dlq(*args):
        raise RuntimeError("kafka down")

    gate = ValidationGate(dlq_sender=broken_dlq)
    assert gate.check("business.fans", None, b"garbage") is None
    assert gate.stats["invalid"] == 1


def test_gate_accepts_an_already_parsed_dict():
    gate = ValidationGate(dlq_sender=FakeDLQ())
    assert gate.check("business.fans", "CAR_01", good_fan()) is not None


class FakeProducer:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, topic, key, value):
        if self.fail:
            raise RuntimeError("broker unavailable")
        self.sent.append((topic, key, value))


def test_safe_publish_sends_valid_event_keyed_by_car_id():
    producer, dlq = FakeProducer(), FakeDLQ()
    event = good_fan()
    assert safe_publish(producer, "business.fans", event, dlq_sender=dlq) is True
    assert producer.sent == [("business.fans", "CAR_01", event)]
    assert dlq.records == []


def test_safe_publish_routes_invalid_event_to_dlq_instead_of_topic():
    producer, dlq = FakeProducer(), FakeDLQ()
    assert safe_publish(producer, "business.fans", good_fan(viewers=-1), dlq_sender=dlq) is False
    assert producer.sent == []
    assert len(dlq.records) == 1


def test_safe_publish_routes_kafka_failure_to_dlq():
    producer, dlq = FakeProducer(fail=True), FakeDLQ()
    assert safe_publish(producer, "business.fans", good_fan(), dlq_sender=dlq) is False
    assert dlq.records[0]["errors"] == ["publish failed: broker unavailable"]
