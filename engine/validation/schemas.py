"""
Declarative event schemas - Navroop's ownership (engine/validation/).

One place that says what a valid event looks like on every topic. The
race.* schemas mirror the DRAFT sections of docs/event-contract.md; the
business.* schemas mirror the sections added with the fan/sponsor
producers. If a contract changes, change it here in the same PR.

Design notes:
  - Extra (unknown) fields are tolerated so producers can add fields
    without instantly sending everything to the DLQ.
  - Ranges are only enforced where the contract states one (or where the
    value is physically impossible, e.g. a negative count).
  - Each topic can also have cross-field rules (see CROSS_FIELD_RULES).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    kind: str  # "str" | "int" | "float" | "bool" | "uuid" | "timestamp"
    min: float | None = None
    max: float | None = None
    choices: frozenset | None = None
    entity: str | None = None  # key into KNOWN_ENTITIES ("car", "sponsor")


# Known entities. A car_id/sponsor_id outside these sets is an "unknown
# entity" and the event goes to the DLQ. tests/unit/test_validator.py
# checks the car set against RaceState.create_default() so it cannot
# silently drift from the simulator.
KNOWN_ENTITIES: dict[str, set[str]] = {
    "car": {"CAR_01", "CAR_02", "CAR_03"},
    "sponsor": {"SPONSOR_01", "SPONSOR_02", "SPONSOR_03"},
}

_UNIT = dict(min=0.0, max=1.0)

_COMMON = {
    "event_id": Field("uuid"),
    "event_time": Field("timestamp"),
    "car_id": Field("str", entity="car"),
    "lap_number": Field("int", min=0),
}

SCHEMAS: dict[str, dict[str, Field]] = {
    "race.timing": {
        **_COMMON,
        "lap_number": Field("int", min=1),
        "lap_time_ms": Field("int", min=1),
        "gap_to_leader_ms": Field("int", min=0),
        "position": Field("int", min=1),
    },
    "race.telemetry": {
        **_COMMON,
        "speed_kmh": Field("float", min=0),
        "rpm": Field("int", min=0),
        "throttle_pct": Field("float", min=0, max=100),
        "brake_pct": Field("float", min=0, max=100),
        "gear": Field("int", min=0),
        "engine_temperature_c": Field("float"),
        "brake_temperature_c": Field("float"),
        "battery_temperature_c": Field("float"),
        "fuel_kg": Field("float", min=0),
        "energy_kwh": Field("float", min=0),
        "location_km": Field("float", min=0),
    },
    "race.tyres": {
        **_COMMON,
        "compound": Field("str"),
        "age_laps": Field("int", min=0),
        "wear": Field("float", **_UNIT),
        "grip": Field("float", **_UNIT),
        "degradation_per_lap": Field("float", min=0),
    },
    "race.weather": {
        **_COMMON,
        "condition": Field("str"),
        "rain_intensity": Field("float", **_UNIT),
        "track_wetness": Field("float", **_UNIT),
        "track_grip": Field("float", **_UNIT),
    },
    "race.pitstops": {
        **_COMMON,
        "pit_entry": Field("bool"),
        "pit_stop": Field("bool"),
        "tyre_change": Field("bool"),
        "repair": Field("bool"),
        "pit_exit": Field("bool"),
    },
    "race.incidents": {
        **_COMMON,
        "incident_type": Field("str"),
        "active": Field("bool"),
        "severity": Field("str"),
        "description": Field("str"),
    },
    "business.fans": {
        **_COMMON,
        "viewers": Field("int", min=0),
        "app_sessions": Field("int", min=0),
        "searches": Field("int", min=0),
        "likes": Field("int", min=0),
        "comments": Field("int", min=0),
        "shares": Field("int", min=0),
        "merch_clicks": Field("int", min=0),
    },
    "business.sponsors": {
        **_COMMON,
        "sponsor_id": Field("str", entity="sponsor"),
        "impressions": Field("int", min=0),
        "visibility_seconds": Field("float", min=0),
        "clicks": Field("int", min=0),
        "conversions": Field("int", min=0),
    },
}


def _sponsor_funnel(event: dict) -> list[str]:
    """clicks cannot exceed impressions; conversions cannot exceed clicks."""
    errors = []
    if event["clicks"] > event["impressions"]:
        errors.append(
            f"inconsistent funnel: clicks ({event['clicks']}) > impressions ({event['impressions']})"
        )
    if event["conversions"] > event["clicks"]:
        errors.append(
            f"inconsistent funnel: conversions ({event['conversions']}) > clicks ({event['clicks']})"
        )
    return errors


# Run only when every individual field already passed its own checks.
CROSS_FIELD_RULES = {
    "business.sponsors": [_sponsor_funnel],
}
