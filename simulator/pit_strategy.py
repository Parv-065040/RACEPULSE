from dataclasses import dataclass
from pathlib import Path

import yaml


CONFIG_PATH = Path("config/pit_strategy.yaml")


@dataclass(frozen=True)
class PitStrategyConfig:
    enabled: bool
    pit_lane_loss_ms: int
    minimum_laps_between_stops: int

    dry_min_age: int
    dry_wear_threshold: float

    wet_min_age: int
    wet_wear_threshold: float

    drying_min_age: int
    drying_wear_threshold: float

    weather_trigger_light_rain: bool
    weather_trigger_rain: bool
    weather_trigger_heavy_rain: bool
    weather_trigger_drying: bool

    tyre_management_weight: float
    wet_weather_weight: float

    maximum_stops: int


def load_pit_strategy_config() -> PitStrategyConfig:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    config = data.get("pit_strategy", {})

    dry = config.get("dry", {})
    wet = config.get("wet", {})
    drying = config.get("drying", {})
    weather_trigger = config.get("weather_trigger", {})
    car_adjustment = config.get("car_adjustment", {})
    strategy = config.get("strategy", {})

    return PitStrategyConfig(
        enabled=bool(config.get("enabled", True)),
        pit_lane_loss_ms=int(config.get("pit_lane_loss_ms", 22000)),
        minimum_laps_between_stops=int(
            config.get("minimum_laps_between_stops", 8)
        ),
        dry_min_age=int(dry.get("min_tyre_age_laps", 18)),
        dry_wear_threshold=float(
            dry.get("wear_threshold", 0.72)
        ),
        wet_min_age=int(wet.get("min_tyre_age_laps", 8)),
        wet_wear_threshold=float(
            wet.get("wear_threshold", 0.52)
        ),
        drying_min_age=int(
            drying.get("min_tyre_age_laps", 7)
        ),
        drying_wear_threshold=float(
            drying.get("wear_threshold", 0.45)
        ),
        weather_trigger_light_rain=bool(
            weather_trigger.get("light_rain", True)
        ),
        weather_trigger_rain=bool(
            weather_trigger.get("rain", True)
        ),
        weather_trigger_heavy_rain=bool(
            weather_trigger.get("heavy_rain", True)
        ),
        weather_trigger_drying=bool(
            weather_trigger.get("drying_track", True)
        ),
        tyre_management_weight=float(
            car_adjustment.get("tyre_management_weight", 0.20)
        ),
        wet_weather_weight=float(
            car_adjustment.get("wet_weather_weight", 0.15)
        ),
        maximum_stops=int(strategy.get("maximum_stops", 3)),
    )


def evaluate_pit_decision(
    *,
    lap_number: int,
    tyre_age: int,
    tyre_wear: float,
    tyre_management: float,
    wet_weather_performance: float,
    weather_condition: str,
    pit_stop_count: int,
    laps_since_last_stop: int,
    config: PitStrategyConfig,
) -> tuple[bool, str]:
    if not config.enabled:
        return False, "STRATEGY_DISABLED"

    if pit_stop_count >= config.maximum_stops:
        return False, "MAXIMUM_STOPS_REACHED"

    if laps_since_last_stop < config.minimum_laps_between_stops:
        return False, "MINIMUM_STINT_NOT_REACHED"

    condition = weather_condition.upper()

    if condition in {"LIGHT_RAIN", "RAIN", "HEAVY_RAIN"}:
        weather_enabled = {
            "LIGHT_RAIN": config.weather_trigger_light_rain,
            "RAIN": config.weather_trigger_rain,
            "HEAVY_RAIN": config.weather_trigger_heavy_rain,
        }[condition]

        if not weather_enabled:
            return False, "WEATHER_TRIGGER_DISABLED"

        threshold = config.wet_wear_threshold
        minimum_age = config.wet_min_age

        reason = "WET_WEATHER_TYRE_WINDOW"

    elif condition == "DRYING_TRACK":
        if not config.weather_trigger_drying:
            return False, "DRYING_TRACK_TRIGGER_DISABLED"

        threshold = config.drying_wear_threshold
        minimum_age = config.drying_min_age

        reason = "DRYING_TRACK_STRATEGY_WINDOW"

    else:
        threshold = config.dry_wear_threshold
        minimum_age = config.dry_min_age

        reason = "TYRE_DEGRADATION_WINDOW"

    age_adjustment = int(
        tyre_management
        * config.tyre_management_weight
        * 10
    )

    adjusted_minimum_age = max(
        1,
        minimum_age + age_adjustment,
    )

    if condition in {"LIGHT_RAIN", "RAIN", "HEAVY_RAIN"}:
        threshold += (
            wet_weather_performance
            * config.wet_weather_weight
            * 0.10
        )

    if tyre_age < adjusted_minimum_age:
        return False, "TYRE_AGE_BELOW_WINDOW"

    if tyre_wear < threshold:
        return False, "TYRE_WEAR_BELOW_WINDOW"

    return True, reason


def should_pit(
    *,
    lap_number: int,
    tyre_age: int,
    tyre_wear: float,
    tyre_management: float,
    wet_weather_performance: float,
    weather_condition: str,
    pit_stop_count: int,
    laps_since_last_stop: int,
    config: PitStrategyConfig,
) -> bool:
    decision, _ = evaluate_pit_decision(
        lap_number=lap_number,
        tyre_age=tyre_age,
        tyre_wear=tyre_wear,
        tyre_management=tyre_management,
        wet_weather_performance=wet_weather_performance,
        weather_condition=weather_condition,
        pit_stop_count=pit_stop_count,
        laps_since_last_stop=laps_since_last_stop,
        config=config,
    )

    return decision
