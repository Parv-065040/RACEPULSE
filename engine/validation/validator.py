"""
Event validator - Navroop's ownership (engine/validation/).

validate_event(topic, event) -> list[str]. An empty list means valid.
Error strings use the same style as the inline check in
consumers/performance/timing_consumer.py ("missing field: X",
"wrong type for X: expected int, got str") so DLQ records look the same
no matter which layer rejected them.
"""
import math
import uuid
from datetime import datetime

from engine.validation.schemas import CROSS_FIELD_RULES, KNOWN_ENTITIES, SCHEMAS, Field


def parse_event_time(value: str) -> datetime:
    """Parse ISO 8601, accepting a trailing 'Z' (the contract's example format)."""
    if value.endswith(("Z", "z")):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _is_number(value) -> bool:
    # bool is a subclass of int in Python; True must not pass as a number.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_field(name: str, value, spec: Field) -> list[str]:
    kind = spec.kind

    if kind in ("str", "uuid", "timestamp"):
        if not isinstance(value, str):
            return [f"wrong type for {name}: expected str, got {type(value).__name__}"]
        if value.strip() == "":
            return [f"empty value for {name}"]
        if kind == "uuid":
            try:
                uuid.UUID(value)
            except ValueError:
                return [f"invalid {name}: not a valid UUID"]
        if kind == "timestamp":
            try:
                parse_event_time(value)
            except ValueError:
                return [f"invalid {name}: not an ISO 8601 timestamp ({value!r})"]
        if spec.choices is not None and value not in spec.choices:
            return [f"invalid value for {name}: {value!r} (allowed: {sorted(spec.choices)})"]
        if spec.entity is not None and value not in KNOWN_ENTITIES[spec.entity]:
            return [f"unknown {name}: {value!r}"]
        return []

    if kind == "bool":
        if not isinstance(value, bool):
            return [f"wrong type for {name}: expected bool, got {type(value).__name__}"]
        return []

    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"wrong type for {name}: expected int, got {type(value).__name__}"]
    elif kind == "float":
        if not _is_number(value):
            return [f"wrong type for {name}: expected number, got {type(value).__name__}"]
        if not math.isfinite(value):
            return [f"invalid {name}: not a finite number"]
    else:  # a typo in schemas.py should fail loudly, not pass silently
        raise ValueError(f"unknown field kind {kind!r} for {name}")

    if spec.min is not None and value < spec.min:
        return [f"out of range for {name}: {value} (min {spec.min})"]
    if spec.max is not None and value > spec.max:
        return [f"out of range for {name}: {value} (max {spec.max})"]
    return []


def validate_event(topic: str, event) -> list[str]:
    schema = SCHEMAS.get(topic)
    if schema is None:
        return [f"unknown topic: {topic}"]
    if not isinstance(event, dict):
        return [f"event must be a JSON object, got {type(event).__name__}"]

    errors: list[str] = []
    for name, spec in schema.items():
        if name not in event:
            errors.append(f"missing field: {name}")
            continue
        errors.extend(_check_field(name, event[name], spec))

    if not errors:
        for rule in CROSS_FIELD_RULES.get(topic, []):
            errors.extend(rule(event))
    return errors
