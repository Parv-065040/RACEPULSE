from dataclasses import dataclass
from enum import Enum


class ScenarioType(str, Enum):
    NORMAL_RACE = "NORMAL_RACE"
    RAIN = "RAIN"
    TYRE_CRISIS = "TYRE_CRISIS"
    SAFETY_CAR = "SAFETY_CAR"
    MECHANICAL_FAILURE = "MECHANICAL_FAILURE"
    CLOSE_BATTLE = "CLOSE_BATTLE"
    COMMERCIAL_SURGE = "COMMERCIAL_SURGE"
    DATA_FAILURE = "DATA_FAILURE"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"


@dataclass(frozen=True)
class ScenarioConfig:
    name: ScenarioType
    rain_intensity: float = 0.0
    tyre_degradation_per_lap: float = 0.02


def create_scenario(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> ScenarioConfig:
    """Create a race scenario configuration."""

    if scenario == ScenarioType.RAIN:
        return ScenarioConfig(
            name=scenario,
            rain_intensity=0.7,
        )

    if scenario == ScenarioType.TYRE_CRISIS:
        return ScenarioConfig(
            name=scenario,
            tyre_degradation_per_lap=0.08,
        )

    return ScenarioConfig(
        name=scenario,
    )