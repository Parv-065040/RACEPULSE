"""
Unit tests for engine.validation.validator / schemas.
Run with: pytest tests/unit/test_validator.py -v
"""
import copy
from uuid import uuid4

import pytest

from engine.validation.schemas import KNOWN_ENTITIES, SCHEMAS
from engine.validation.validator import parse_event_time, validate_event
from simulator.state import RaceState


def timing_event(**overrides):
    event = {
        "event_id": str(uuid4()),
        "event_time": "2026-09-26T10:15:30.000Z",
        "car_id": "CAR_01",
        "lap_number": 1,
        "lap_time_ms": 91234,
        "gap_to_leader_ms": 0,
        "position": 1,
    }
    event.update(overrides)
    return event


def fan_event(**overrides):
    event = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z",
        "car_id": "CAR_01", "lap_number": 1, "viewers": 50000, "app_sessions": 15000,
        "searches": 2500, "likes": 6000, "comments": 1000, "shares": 500, "merch_clicks": 250,
    }
    event.update(overrides)
    return event


def sponsor_event(**overrides):
    event = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z",
        "car_id": "CAR_01", "lap_number": 1, "sponsor_id": "SPONSOR_01",
        "impressions": 20000, "visibility_seconds": 14.0, "clicks": 80, "conversions": 6,
    }
    event.update(overrides)
    return event


def test_valid_timing_event_has_no_errors():
    assert validate_event("race.timing", timing_event()) == []


def test_valid_fan_and_sponsor_events_have_no_errors():
    assert validate_event("business.fans", fan_event()) == []
    assert validate_event("business.sponsors", sponsor_event()) == []


def test_missing_field_is_reported():
    event = timing_event()
    del event["lap_time_ms"]
    assert "missing field: lap_time_ms" in validate_event("race.timing", event)


def test_wrong_type_is_reported_in_timing_consumer_style():
    errors = validate_event("race.timing", timing_event(lap_number="not-a-number"))
    assert errors == ["wrong type for lap_number: expected int, got str"]


def test_bool_is_not_accepted_as_int():
    errors = validate_event("race.timing", timing_event(position=True))
    assert errors == ["wrong type for position: expected int, got bool"]


def test_float_field_accepts_int_but_not_string_or_nan():
    telemetry_base = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z", "car_id": "CAR_01",
        "lap_number": 1, "speed_kmh": 210, "rpm": 9000, "throttle_pct": 80.0, "brake_pct": 0.0,
        "gear": 7, "engine_temperature_c": 95.0, "brake_temperature_c": 450.0,
        "battery_temperature_c": 40.0, "fuel_kg": 100.0, "energy_kwh": 4.0, "location_km": 0.0,
    }
    assert validate_event("race.telemetry", telemetry_base) == []
    assert validate_event("race.telemetry", {**telemetry_base, "speed_kmh": "fast"})
    assert validate_event("race.telemetry", {**telemetry_base, "speed_kmh": float("nan")})


def test_unknown_car_is_reported():
    errors = validate_event("race.timing", timing_event(car_id="CAR_99"))
    assert errors == ["unknown car_id: 'CAR_99'"]


def test_unknown_sponsor_is_reported():
    errors = validate_event("business.sponsors", sponsor_event(sponsor_id="SPONSOR_99"))
    assert errors == ["unknown sponsor_id: 'SPONSOR_99'"]


def test_negative_count_is_out_of_range():
    errors = validate_event("business.fans", fan_event(likes=-5))
    assert errors == ["out of range for likes: -5 (min 0)"]


def test_unit_interval_fields_reject_values_above_one():
    event = {
        "event_id": str(uuid4()), "event_time": "2026-09-26T10:15:30.000Z", "car_id": "CAR_01",
        "lap_number": 1, "compound": "MEDIUM", "age_laps": 1, "wear": 1.5, "grip": 0.98,
        "degradation_per_lap": 0.02,
    }
    assert validate_event("race.tyres", event) == ["out of range for wear: 1.5 (max 1.0)"]


def test_bad_uuid_and_bad_timestamp():
    assert validate_event("race.timing", timing_event(event_id="bad-event-001")) == [
        "invalid event_id: not a valid UUID"
    ]
    errors = validate_event("race.timing", timing_event(event_time="yesterday"))
    assert errors and errors[0].startswith("invalid event_time")


def test_timestamp_accepts_z_suffix_and_offset_format():
    assert parse_event_time("2026-09-26T10:15:30.000Z").tzinfo is not None
    assert parse_event_time("2026-09-28T19:00:31.780130+00:00").tzinfo is not None


def test_sponsor_funnel_cross_field_rules():
    assert validate_event("business.sponsors", sponsor_event(clicks=30000))[0].startswith(
        "inconsistent funnel: clicks"
    )
    assert validate_event("business.sponsors", sponsor_event(clicks=5, conversions=9))[0].startswith(
        "inconsistent funnel: conversions"
    )


def test_non_object_event_and_unknown_topic():
    assert validate_event("race.timing", ["not", "an", "object"]) == [
        "event must be a JSON object, got list"
    ]
    assert validate_event("race.nonsense", timing_event()) == ["unknown topic: race.nonsense"]


def test_extra_fields_are_tolerated():
    assert validate_event("race.timing", timing_event(new_optional_field="ok")) == []


def test_input_event_is_not_mutated():
    event = timing_event()
    snapshot = copy.deepcopy(event)
    validate_event("race.timing", event)
    assert event == snapshot


def test_known_cars_match_the_simulator_defaults():
    assert KNOWN_ENTITIES["car"] == set(RaceState.create_default().cars)


@pytest.mark.parametrize("topic", sorted(SCHEMAS))
def test_every_schema_requires_the_common_fields(topic):
    for common in ("event_id", "event_time", "car_id", "lap_number"):
        assert common in SCHEMAS[topic]
