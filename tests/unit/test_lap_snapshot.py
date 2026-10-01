from simulator.lap_snapshot import RaceLapSnapshot
from simulator.scenario import ScenarioType
from simulator.simulator import create_simulator


def _snapshot_from_car(simulator, car, lap):
    weather = simulator.race.weather

    return RaceLapSnapshot(
        lap=lap,
        weather_condition=weather.condition,
        rain_intensity=weather.rain_intensity,
        track_wetness=weather.track_wetness,
        track_grip=weather.track_grip,
        car_id=car.car_id,
        position=car.position,
        gap_to_leader_ms=car.gap_to_leader_ms,
        lap_time_ms=car.lap_time_ms,
        race_time_ms=car.race_time_ms,
        tyre_age=car.tyre.age_laps,
        tyre_wear=car.tyre.wear,
        tyre_grip=car.tyre.grip,
        tyre_compound=car.tyre.compound,
        pit_stop=car.pitstop.pit_stop,
        pit_stop_count=car.pitstop.pit_stop_count,
        last_pit_lap=car.pitstop.last_pit_lap,
        total_pit_loss_ms=car.pitstop.total_pit_loss_ms,
        is_running=car.is_running,
    )


def test_lap_snapshot_contains_weather_and_car_state():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    cars = simulator.advance_one_lap()

    snapshot = _snapshot_from_car(
        simulator,
        cars[0],
        1,
    )

    assert snapshot.lap == 1
    assert snapshot.car_id == cars[0].car_id
    assert snapshot.weather_condition
    assert snapshot.tyre_age >= 1
    assert snapshot.tyre_wear >= 0.0
    assert snapshot.tyre_grip >= 0.0


def test_snapshot_history_preserves_weather_transition():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    simulator.advance_laps(35)

    snapshots = simulator.snapshot_history

    assert snapshots

    lap_15 = [
        snapshot
        for snapshot in snapshots
        if snapshot.lap == 15
    ]

    lap_16 = [
        snapshot
        for snapshot in snapshots
        if snapshot.lap == 16
    ]

    lap_26 = [
        snapshot
        for snapshot in snapshots
        if snapshot.lap == 26
    ]

    lap_35 = [
        snapshot
        for snapshot in snapshots
        if snapshot.lap == 35
    ]

    assert lap_15
    assert lap_16
    assert lap_26
    assert lap_35

    assert lap_15[0].weather_condition == "DRY"
    assert lap_16[0].weather_condition == "OVERCAST"
    assert lap_26[0].weather_condition == "LIGHT_RAIN"
    assert lap_35[0].weather_condition == "RAIN"


def test_snapshot_history_contains_all_cars_per_lap():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    simulator.advance_laps(5)

    snapshots = simulator.snapshot_history

    assert len(snapshots) == 5 * len(simulator.race.cars)

    for lap in range(1, 6):
        lap_snapshots = [
            snapshot
            for snapshot in snapshots
            if snapshot.lap == lap
        ]

        assert len(lap_snapshots) == len(simulator.race.cars)


def test_snapshot_history_records_strategic_pit_stops():
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    simulator.advance_laps(58)

    pit_snapshots = [
        snapshot
        for snapshot in simulator.snapshot_history
        if snapshot.pit_stop
    ]

    assert pit_snapshots

    for snapshot in pit_snapshots:
        assert snapshot.pit_stop_count >= 1
        assert snapshot.last_pit_lap == snapshot.lap
        assert snapshot.total_pit_loss_ms >= 22000
        assert snapshot.tyre_age == 1
        assert snapshot.tyre_wear > 0.0
        assert snapshot.tyre_grip < 1.0
