"""
Declarative event schemas - Navroop's ownership (engine/validation/).

One place that says what a valid event looks like on every topic.
"""

from dataclasses import dataclass

from engine.config.car_loader import get_known_car_ids


@dataclass(frozen=True)
class Field:
    kind: str  # "str" | "int" | "float" | "bool" | "uuid" | "timestamp"
    min: float | None = None
    max: float | None = None
    choices: frozenset | None = None
    entity: str | None = None


KNOWN_ENTITIES: dict[str, set[str]] = {
    "car": get_known_car_ids(),
    "sponsor": {f"SPONSOR_{i:02d}" for i in range(1, 13)},
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
    """Clicks cannot exceed impressions; conversions cannot exceed clicks."""
    errors = []

    if event["clicks"] > event["impressions"]:
        errors.append(
            f"inconsistent funnel: clicks ({event['clicks']}) "
            f"> impressions ({event['impressions']})"
        )

    if event["conversions"] > event["clicks"]:
        errors.append(
            f"inconsistent funnel: conversions ({event['conversions']}) "
            f"> clicks ({event['clicks']})"
        )

    return errors


CROSS_FIELD_RULES = {
    "business.sponsors": [_sponsor_funnel],
}
