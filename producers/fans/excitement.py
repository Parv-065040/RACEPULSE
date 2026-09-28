"""
Race-excitement factor - Navroop's ownership (producers/fans/).

Fan engagement and sponsor exposure should not be independent random
numbers (see the causal chain in RACEPULSE_Master_Polish_Plan.md, section
8: rain -> excitement -> fan engagement -> sponsor exposure). This turns
existing race state into one multiplier both business producers share.
READ-ONLY on simulator state - nothing in simulator/ is modified.

These weights are project heuristics for the simulation, not validated
motorsport or marketing metrics.
"""
from simulator.scenario import ScenarioType

RAIN_WEIGHT = 0.5
INCIDENT_BOOST = {"HIGH": 0.6, "MEDIUM": 0.3}
DEFAULT_INCIDENT_BOOST = 0.1
CLOSE_GAP_MS = 1500
CLOSE_BATTLE_BOOST = 0.3
PIT_STOP_BOOST = 0.1
SURGE_MULTIPLIER = 3.0  # COMMERCIAL_SURGE scenario


def excitement_factor(car, race, scenario_name=None) -> float:
    e = 1.0
    e += RAIN_WEIGHT * race.weather.rain_intensity
    if car.incident.active:
        e += INCIDENT_BOOST.get(car.incident.severity, DEFAULT_INCIDENT_BOOST)
    if car.position > 1 and car.gap_to_leader_ms <= CLOSE_GAP_MS:
        e += CLOSE_BATTLE_BOOST
    if car.pitstop.pit_stop:
        e += PIT_STOP_BOOST
    if scenario_name == ScenarioType.COMMERCIAL_SURGE:
        e *= SURGE_MULTIPLIER
    return e
