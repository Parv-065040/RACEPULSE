"""
Unit tests for the fan and sponsor event builders and their causal link
to race state. Run with: pytest tests/unit/test_business_events.py -v
"""
import random

from engine.validation.schemas import KNOWN_ENTITIES
from engine.validation.validator import validate_event
from producers.fans.excitement import (
    CLOSE_BATTLE_BOOST, SURGE_MULTIPLIER, excitement_factor,
)
from producers.fans.fan_event import build_fan_event
from producers.sponsors.sponsor_event import SPONSOR_BY_CAR, build_sponsor_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator


def advance(scenario, laps=3):
    sim = RaceSimulator(scenario=create_scenario(scenario))
    for _ in range(laps):
        sim.advance_one_lap()
    return sim


def test_built_events_satisfy_the_contract_for_every_scenario_and_car():
    for scenario in ScenarioType:
        sim = advance(scenario)
        for car in sim.race.cars.values():
            fan = build_fan_event(car, sim.race, sim.current_lap, scenario, rng=random.Random(1))
            spo = build_sponsor_event(car, sim.race, sim.current_lap, scenario, rng=random.Random(1))
            assert validate_event("business.fans", fan) == [], (scenario, car.car_id)
            assert validate_event("business.sponsors", spo) == [], (scenario, car.car_id)


def test_same_seed_gives_same_counts():
    sim = advance(ScenarioType.NORMAL_RACE)
    car = sim.race.get_car("CAR_01")
    a = build_fan_event(car, sim.race, 3, rng=random.Random(7))
    b = build_fan_event(car, sim.race, 3, rng=random.Random(7))
    a.pop("event_id"), a.pop("event_time"), b.pop("event_id"), b.pop("event_time")
    assert a == b


def test_leader_draws_more_viewers_than_last_place():
    sim = advance(ScenarioType.NORMAL_RACE)
    leader = build_fan_event(sim.race.get_car("CAR_01"), sim.race, 3, rng=random.Random(0))
    last = build_fan_event(sim.race.get_car("CAR_03"), sim.race, 3, rng=random.Random(0))
    assert leader["viewers"] > last["viewers"]


def test_rain_raises_excitement_over_a_dry_race():
    dry, wet = advance(ScenarioType.NORMAL_RACE), advance(ScenarioType.RAIN)
    assert excitement_factor(wet.race.get_car("CAR_01"), wet.race) > excitement_factor(
        dry.race.get_car("CAR_01"), dry.race
    )


def test_active_incident_raises_excitement():
    sim = advance(ScenarioType.SAFETY_CAR)
    car = sim.race.get_car("CAR_01")
    with_incident = excitement_factor(car, sim.race)
    car.incident.active = False
    assert with_incident > excitement_factor(car, sim.race)


def test_close_battle_adds_boost_for_a_chasing_car():
    sim = advance(ScenarioType.CLOSE_BATTLE, laps=1)
    chaser = sim.race.get_car("CAR_02")
    assert chaser.gap_to_leader_ms <= 1500
    assert excitement_factor(chaser, sim.race) >= 1.0 + CLOSE_BATTLE_BOOST


def test_commercial_surge_multiplies_exposure():
    sim = advance(ScenarioType.NORMAL_RACE)
    car = sim.race.get_car("CAR_01")
    base = excitement_factor(car, sim.race, ScenarioType.NORMAL_RACE)
    surge = excitement_factor(car, sim.race, ScenarioType.COMMERCIAL_SURGE)
    assert surge == base * SURGE_MULTIPLIER


def test_sponsor_funnel_is_always_consistent():
    sim = advance(ScenarioType.COMMERCIAL_SURGE)
    for seed in range(50):
        for car in sim.race.cars.values():
            e = build_sponsor_event(car, sim.race, 3, ScenarioType.COMMERCIAL_SURGE, random.Random(seed))
            assert e["conversions"] <= e["clicks"] <= e["impressions"]


def test_sponsor_mapping_uses_only_known_sponsors_and_cars():
    assert set(SPONSOR_BY_CAR.values()) <= KNOWN_ENTITIES["sponsor"]
    assert set(SPONSOR_BY_CAR) == KNOWN_ENTITIES["car"]
