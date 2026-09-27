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


def create_scenario(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> ScenarioConfig:
    """Create a race scenario configuration."""
    return ScenarioConfig(name=scenario)