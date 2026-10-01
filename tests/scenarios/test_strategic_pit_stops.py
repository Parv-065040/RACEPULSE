from simulator.scenario import ScenarioType
from simulator.simulator import create_simulator


def test_normal_race_has_strategic_pit_stops():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    history = simulator.advance_laps(58)

    pit_laps = []

    for lap_number, cars in enumerate(history, start=1):
        for car in cars:
            if car.pitstop.pit_stop:
                pit_laps.append((lap_number, car.car_id))

    assert pit_laps


def test_strategic_pit_resets_tyre_state():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    history = simulator.advance_laps(58)

    reset_observed = False

    for cars in history:
        for car in cars:
            if car.pitstop.pit_stop:
                assert car.tyre.age_laps == 1
                assert car.tyre.wear > 0.0
                assert car.tyre.grip < 1.0
                assert car.tyre.wear <= car.tyre.degradation_per_lap
                reset_observed = True

    assert reset_observed


def test_strategic_pit_does_not_break_dynamic_ranking():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    history = simulator.advance_laps(58)

    for cars in history:
        positions = [car.position for car in cars if car.is_running]

        assert len(positions) == len(set(positions))
        assert sorted(positions) == list(
            range(1, len(positions) + 1)
        )


def test_pit_stop_penalty_is_applied_once():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    history = simulator.advance_laps(58)

    for cars in history:
        for car in cars:
            if car.pitstop.pit_stop:
                assert car.pit_time_loss_ms == 0


def test_existing_explicit_pit_stop_scenario_still_works():
    simulator = create_simulator(ScenarioType.PIT_STOP)

    pit_lap = simulator.scenario.pitstop_lap
    pit_car = simulator.scenario.pitstop_car_id

    simulator.advance_laps(pit_lap)

    car = simulator.race.get_car(pit_car)

    assert car.pitstop.pit_stop is True
    assert car.tyre.age_laps == 1
    assert car.tyre.wear > 0.0
    assert car.tyre.grip < 1.0
