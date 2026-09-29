from simulator.scenario import ScenarioType
from simulator.simulator import create_simulator


def test_normal_race_scenario():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    cars = simulator.advance_one_lap()

    assert simulator.scenario.name == ScenarioType.NORMAL_RACE
    assert len(cars) == 3
    assert all(car.is_running for car in cars)


def test_rain_scenario_reduces_track_grip():
    simulator = create_simulator(ScenarioType.RAIN)

    assert simulator.race.weather.rain_intensity == 0.7
    assert simulator.race.weather.track_wetness > 0.0
    assert simulator.race.weather.track_grip < 1.0

    car = simulator.advance_one_lap()[0]

    assert car.lap_time_ms > 90000


def test_tyre_crisis_increases_tyre_wear():
    simulator = create_simulator(ScenarioType.TYRE_CRISIS)

    cars = simulator.advance_laps(5)

    car = cars[-1][0]

    assert car.tyre.wear == 0.40
    assert car.tyre.grip == 0.60


def test_safety_car_compresses_gaps():
    simulator = create_simulator(ScenarioType.SAFETY_CAR)

    car_01 = simulator.race.get_car("CAR_01")
    car_02 = simulator.race.get_car("CAR_02")
    car_03 = simulator.race.get_car("CAR_03")

    assert car_01.gap_to_leader_ms == 0
    assert car_02.gap_to_leader_ms == 1500
    assert car_03.gap_to_leader_ms == 2500

    assert car_02.gap_change_ms_per_lap == 0
    assert car_03.gap_change_ms_per_lap == 0


def test_safety_car_creates_active_incidents():
    simulator = create_simulator(ScenarioType.SAFETY_CAR)

    for car in simulator.race.cars.values():
        assert car.incident.incident_type == "SAFETY_CAR"
        assert car.incident.active is True
        assert car.incident.severity == "MEDIUM"
        assert car.incident.description == (
            "Safety car deployed on the track."
        )


def test_close_battle_creates_tight_gaps():
    simulator = create_simulator(ScenarioType.CLOSE_BATTLE)

    cars = simulator.race.cars

    assert cars["CAR_01"].gap_to_leader_ms == 0
    assert cars["CAR_02"].gap_to_leader_ms == 1000
    assert cars["CAR_03"].gap_to_leader_ms == 1000

    assert cars["CAR_02"].gap_change_ms_per_lap == 100
    assert cars["CAR_03"].gap_change_ms_per_lap == -100

    history = simulator.advance_laps(3)

    lap_three = history[-1]

    car_02 = next(
        car for car in lap_three
        if car.car_id == "CAR_02"
    )

    car_03 = next(
        car for car in lap_three
        if car.car_id == "CAR_03"
    )

    assert car_02.gap_to_leader_ms == 1300
    assert car_03.gap_to_leader_ms == 700


def test_mechanical_failure_removes_failed_car_from_active_simulation():
    simulator = create_simulator(
        ScenarioType.MECHANICAL_FAILURE
    )

    history = simulator.advance_laps(3)

    assert [car.car_id for car in history[0]] == [
        "CAR_01",
        "CAR_02",
        "CAR_03",
    ]

    assert [car.car_id for car in history[1]] == [
        "CAR_01",
        "CAR_02",
        "CAR_03",
    ]

    assert [car.car_id for car in history[2]] == [
        "CAR_01",
        "CAR_02",
    ]

    failed_car = simulator.race.get_car("CAR_03")

    assert failed_car.is_running is False
    assert failed_car.lap_number == 2


def test_mechanical_failure_creates_incident():
    simulator = create_simulator(
        ScenarioType.MECHANICAL_FAILURE
    )

    simulator.advance_laps(3)

    failed_car = simulator.race.get_car("CAR_03")

    assert failed_car.incident.incident_type == (
        "MECHANICAL_FAILURE"
    )
    assert failed_car.incident.active is True
    assert failed_car.incident.severity == "HIGH"
    assert failed_car.incident.description == (
        "Mechanical failure caused the car to retire."
    )