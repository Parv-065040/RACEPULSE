from simulator.scenario import ScenarioType
from simulator.simulator import create_simulator
from engine.config.car_loader import load_car_configs


def test_normal_race_scenario():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    cars = simulator.advance_one_lap()
    configured_cars = load_car_configs()

    assert simulator.scenario.name == ScenarioType.NORMAL_RACE
    assert len(cars) == len(configured_cars)
    assert {car.car_id for car in cars} == {
        config.car_id for config in configured_cars
    }


def test_rain_scenario_reduces_track_grip():
    dry_simulator = create_simulator(ScenarioType.NORMAL_RACE)
    rain_simulator = create_simulator(ScenarioType.RAIN)

    assert rain_simulator.race.weather.rain_intensity == 0.7
    assert rain_simulator.race.weather.track_wetness > 0.0
    assert rain_simulator.race.weather.track_grip < 1.0

    dry_car = dry_simulator.advance_one_lap()[0]
    rain_car = rain_simulator.advance_one_lap()[0]

    assert rain_car.lap_time_ms > dry_car.lap_time_ms


def test_tyre_crisis_increases_lap_time():
    normal = create_simulator(ScenarioType.NORMAL_RACE)
    crisis = create_simulator(ScenarioType.TYRE_CRISIS)

    normal_car = normal.advance_one_lap()[0]
    crisis_car = crisis.advance_one_lap()[0]

    assert crisis_car.lap_time_ms > normal_car.lap_time_ms


def test_safety_car_compresses_gaps():
    simulator = create_simulator(ScenarioType.SAFETY_CAR)

    original_gaps = {
        config.car_id: config.starting_gap_ms
        for config in load_car_configs()
    }

    simulator.advance_one_lap()

    for car in simulator.race.cars.values():
        if car.car_id == "CAR_01":
            assert car.gap_to_leader_ms == 0
        else:
            assert car.gap_to_leader_ms < original_gaps[car.car_id]


def test_close_battle_changes_selected_gap():
    simulator = create_simulator(ScenarioType.CLOSE_BATTLE)

    original_gaps = {
        car.car_id: car.gap_to_leader_ms
        for car in simulator.race.cars.values()
    }

    simulator.advance_one_lap()

    car_02 = simulator.race.get_car("CAR_02")

    assert car_02.gap_to_leader_ms != original_gaps["CAR_02"]


def test_mechanical_failure_removes_failed_car_from_active_simulation():
    simulator = create_simulator(
        ScenarioType.MECHANICAL_FAILURE
    )

    failure_car_id = simulator.scenario.mechanical_failure_car_id

    history = simulator.advance_laps(
        simulator.scenario.mechanical_failure_lap
    )

    configured_ids = {
        config.car_id
        for config in load_car_configs()
    }

    expected_active_ids = configured_ids - {failure_car_id}

    assert set(car.car_id for car in history[-1]) == expected_active_ids


def test_mechanical_failure_creates_incident():
    simulator = create_simulator(
        ScenarioType.MECHANICAL_FAILURE
    )

    failure_car_id = simulator.scenario.mechanical_failure_car_id
    failure_lap = simulator.scenario.mechanical_failure_lap

    simulator.advance_laps(failure_lap)

    failed_car = simulator.race.get_car(failure_car_id)

    assert failed_car.incident.incident_type == (
        "MECHANICAL_FAILURE"
    )
    assert failed_car.incident.active is True


def test_pit_stop_scenario_uses_configured_car():
    simulator = create_simulator(
        ScenarioType.PIT_STOP
    )

    pitstop_car_id = simulator.scenario.pitstop_car_id
    pitstop_lap = simulator.scenario.pitstop_lap

    simulator.advance_laps(pitstop_lap)

    car = simulator.race.get_car(pitstop_car_id)

    assert car.pitstop.pit_stop is True


def test_all_configured_cars_have_unique_positions():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    positions = [
        car.position
        for car in simulator.race.cars.values()
    ]

    assert len(positions) == len(set(positions))
    assert sorted(positions) == list(
        range(1, len(positions) + 1)
    )


