"""
Failure-injection tests - Navroop's ownership (tests/failure/).

One test group per required failure case from docs/team-work-division.md
section 9: invalid JSON, missing fields, wrong data types, unknown
entities, duplicate events, producer failure, invalid configuration,
plus stale-stream detection. These run WITHOUT Kafka/MySQL: the DLQ is
replaced by an in-memory fake and the alert engine by a stub.

Common assertion: a bad input is rejected, reported, and the pipeline
keeps processing the good events that follow it.

Run with: pytest tests/failure -v
"""
import json
import sys
import time
import types
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from engine.validation.gate import ValidationGate
from engine.validation.safe_publish import safe_publish

REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeDLQ:
    def __init__(self):
        self.records = []

    def __call__(self, source_topic, key, raw_value, errors):
        self.records.append({"topic": source_topic, "key": key, "raw": raw_value, "errors": errors})


def timing(**overrides):
    event = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z", "car_id": "CAR_01",
        "lap_number": 1, "lap_time_ms": 91000, "gap_to_leader_ms": 0, "position": 1,
    }
    event.update(overrides)
    return event


def run_stream(messages, topic="race.timing"):
    """Feed raw messages through a gate; return (accepted_events, dlq, gate)."""
    dlq = FakeDLQ()
    gate = ValidationGate(dlq_sender=dlq)
    accepted = []
    for key, raw in messages:
        event = gate.check(topic, key, raw)
        if event is not None:
            accepted.append(event)
    return accepted, dlq, gate


def as_bytes(event):
    return json.dumps(event).encode("utf-8")


# ---------------------------------------------------------------- invalid JSON
def test_invalid_json_is_dlqd_and_stream_continues():
    good_before, good_after = timing(lap_number=1), timing(lap_number=2)
    accepted, dlq, _ = run_stream([
        (b"CAR_01", as_bytes(good_before)),
        (b"CAR_01", b'{"event_id": "x", "lap_n'),      # truncated JSON
        (b"CAR_01", as_bytes(good_after)),
    ])
    assert [e["lap_number"] for e in accepted] == [1, 2]
    assert len(dlq.records) == 1 and dlq.records[0]["errors"][0].startswith("invalid JSON")


@pytest.mark.parametrize("payload", [b"", b"null", b"42", b'"text"', b"[]", b"\xff\xfe"])
def test_garbage_payloads_never_raise(payload):
    accepted, dlq, _ = run_stream([(None, payload)])
    assert accepted == [] and len(dlq.records) == 1


# ------------------------------------------------------------- missing fields
def test_every_missing_required_field_is_detected():
    for field in timing():
        event = timing()
        del event[field]
        accepted, dlq, _ = run_stream([(b"CAR_01", as_bytes(event))])
        assert accepted == [], field
        assert f"missing field: {field}" in dlq.records[0]["errors"]


def test_empty_object_reports_all_missing_fields():
    _, dlq, _ = run_stream([(b"CAR_01", b"{}")])
    assert len([e for e in dlq.records[0]["errors"] if e.startswith("missing field")]) == 7


# ------------------------------------------------------------ wrong data types
@pytest.mark.parametrize("field,bad_value", [
    ("lap_number", "3"), ("lap_time_ms", 91000.5), ("gap_to_leader_ms", None),
    ("position", True), ("car_id", 7), ("event_time", 1234567890),
])
def test_wrong_types_are_dlqd(field, bad_value):
    accepted, dlq, _ = run_stream([(b"CAR_01", as_bytes(timing(**{field: bad_value})))])
    assert accepted == [] and len(dlq.records) == 1


# ------------------------------------------------------------ unknown entities
def test_unknown_car_is_dlqd_known_car_passes():
    accepted, dlq, _ = run_stream([
        (b"CAR_99", as_bytes(timing(car_id="CAR_99"))),
        (b"CAR_02", as_bytes(timing(car_id="CAR_02"))),
    ])
    assert [e["car_id"] for e in accepted] == ["CAR_02"]
    assert dlq.records[0]["errors"] == ["unknown car_id: 'CAR_99'"]


# ------------------------------------------------------------ duplicate events
def test_replayed_event_is_processed_exactly_once():
    event = timing()
    accepted, dlq, gate = run_stream([(b"CAR_01", as_bytes(event))] * 5)
    assert len(accepted) == 1
    assert gate.stats == {"accepted": 1, "invalid": 0, "duplicate": 4}
    assert dlq.records == []  # duplicates are counted, not treated as malformed


# ------------------------------------------------------------- producer failure
class BrokenProducer:
    def send(self, topic, key, value):
        raise ConnectionError("Kafka unreachable")


def test_producer_failure_is_captured_not_raised():
    dlq = FakeDLQ()
    event = timing()
    assert safe_publish(BrokenProducer(), "race.timing", event, dlq_sender=dlq) is False
    assert dlq.records[0]["raw"] == event
    assert "publish failed" in dlq.records[0]["errors"][0]


def test_producer_and_dlq_both_down_still_does_not_raise():
    def dead_dlq(*args):
        raise ConnectionError("DLQ unreachable")

    assert safe_publish(BrokenProducer(), "race.timing", timing(), dlq_sender=dead_dlq) is False


# ---------------------------------------------------------- stale stream (Parv's)
def _load_stale_monitor(monkeypatch):
    """Import engine.alerts.stale_stream_monitor with the alert engine stubbed
    (the real one opens a Kafka producer at import time)."""
    calls = []
    stub = types.ModuleType("engine.alerts.alert_engine")
    stub.raise_stale_stream_alert = lambda car_id, elapsed: calls.append(car_id)
    monkeypatch.setitem(sys.modules, "engine.alerts.alert_engine", stub)
    monkeypatch.delitem(sys.modules, "engine.alerts.stale_stream_monitor", raising=False)
    monkeypatch.chdir(REPO_ROOT)  # the module reads config/thresholds.yaml relative to cwd
    import engine.alerts.stale_stream_monitor as monitor
    monkeypatch.setattr(monitor, "_last_seen_by_car", {})
    monkeypatch.setattr(monitor, "_flagged", set())
    return monitor, calls


def test_silent_producer_raises_one_stale_alert_then_recovers(monkeypatch):
    monitor, calls = _load_stale_monitor(monkeypatch)
    monitor.mark_seen("CAR_01")
    monitor.check_for_stale_cars()
    assert calls == []                                   # fresh -> no alert

    monitor._last_seen_by_car["CAR_01"] = time.time() - (monitor.THRESHOLD_SECONDS + 5)
    monitor.check_for_stale_cars()
    monitor.check_for_stale_cars()
    assert calls == ["CAR_01"]                           # alerted once, not every poll

    monitor.mark_seen("CAR_01")                          # stream resumes
    assert "CAR_01" not in monitor._flagged
    monitor._last_seen_by_car["CAR_01"] = time.time() - (monitor.THRESHOLD_SECONDS + 5)
    monitor.check_for_stale_cars()
    assert calls == ["CAR_01", "CAR_01"]                 # can alert again after recovery


# ------------------------------------------------------- invalid configuration
@pytest.fixture
def config_loader(monkeypatch, tmp_path):
    from engine.config import loader

    path = tmp_path / "thresholds.yaml"
    good = yaml.safe_load((REPO_ROOT / "config" / "thresholds.yaml").read_text(encoding="utf-8-sig"))
    path.write_text(yaml.safe_dump(good), encoding="utf-8")
    monkeypatch.setattr(loader, "CONFIG_PATH", str(path))
    monkeypatch.setattr(loader, "_current_config", {})
    monkeypatch.setattr(loader, "_last_good_version", 0)
    loader._load_once()
    assert loader.get_config() == good
    return loader, path, good


def _try_reload(loader):
    try:
        loader._load_once()
    except Exception:
        pass  # in production the reload thread catches and logs this


def test_threshold_order_violation_keeps_last_valid_config(config_loader):
    loader, path, good = config_loader
    bad = json.loads(json.dumps(good))
    bad["lap_pace_delta"]["severity_thresholds"]["warning_ms"] = 9999  # >= critical_ms
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    _try_reload(loader)
    assert loader.get_config() == good


def test_unparseable_yaml_keeps_last_valid_config(config_loader):
    loader, path, good = config_loader
    path.write_text("lap_pace_delta: [unclosed\n  - : :", encoding="utf-8")
    _try_reload(loader)
    assert loader.get_config() == good


def test_missing_required_section_keeps_last_valid_config(config_loader):
    loader, path, good = config_loader
    bad = json.loads(json.dumps(good))
    del bad["gap_trend"]
    path.write_text(yaml.safe_dump(bad), encoding="utf-8")
    _try_reload(loader)
    assert loader.get_config() == good


def test_valid_edit_is_picked_up(config_loader):
    loader, path, good = config_loader
    edited = json.loads(json.dumps(good))
    edited["lap_pace_delta"]["severity_thresholds"]["warning_ms"] = 600
    path.write_text(yaml.safe_dump(edited), encoding="utf-8")
    loader._load_once()
    assert loader.get_config()["lap_pace_delta"]["severity_thresholds"]["warning_ms"] == 600
