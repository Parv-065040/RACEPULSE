from dataclasses import dataclass
from enum import Enum


class ScenarioType(str, Enum):
    NORMAL_RACE = "NORMAL_RACE"
    RAIN = "RAIN"
    TYRE_CRISIS = "TYRE_CRISIS"
    SAFETY_CAR = "SAFETY_CAR"
    MECHANICAL_FAILURE = "MECHANICAL_FAILURE"
    CLOSE_BATTLE = "CLOSE_BATTLE"
    PIT_STOP = "PIT_STOP"
    COMMERCIAL_SURGE = "COMMERCIAL_SURGE"
    DATA_FAILURE = "DATA_FAILURE"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"


@dataclass(frozen=True)
class ScenarioConfig:
    name: ScenarioType
    rain_intensity: float = 0.0
    tyre_degradation_per_lap: float = 0.02
    safety_car_gap_factor: float = 1.0
    close_battle_gap_ms: int = 1000
    close_battle_gap_change_ms: int = 100
    mechanical_failure_car_id: str = "CAR_03"
    mechanical_failure_lap: int = 3
    pitstop_car_id: str = "CAR_01"
    pitstop_lap: int = 2


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

    if scenario == ScenarioType.SAFETY_CAR:
        return ScenarioConfig(
            name=scenario,
            safety_car_gap_factor=0.5,
        )

    if scenario == ScenarioType.CLOSE_BATTLE:
        return ScenarioConfig(
            name=scenario,
            close_battle_gap_ms=1000,
            close_battle_gap_change_ms=100,
        )

    if scenario == ScenarioType.MECHANICAL_FAILURE:
        return ScenarioConfig(
            name=scenario,
            mechanical_failure_car_id="CAR_03",
            mechanical_failure_lap=3,
        )

    if scenario == ScenarioType.PIT_STOP:
        return ScenarioConfig(
            name=scenario,
            pitstop_car_id="CAR_01",
            pitstop_lap=2,
        )

    return ScenarioConfig(
        name=scenario,
    )