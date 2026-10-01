from simulator.pit_strategy import (
    evaluate_pit_decision,
    load_pit_strategy_config,
)


def test_strategy_returns_explanation_when_pit_window_opens():
    config = load_pit_strategy_config()

    decision, reason = evaluate_pit_decision(
        lap_number=30,
        tyre_age=30,
        tyre_wear=0.70,
        tyre_management=0.70,
        wet_weather_performance=0.80,
        weather_condition="LIGHT_RAIN",
        pit_stop_count=0,
        laps_since_last_stop=30,
        config=config,
    )

    assert decision is True
    assert reason == "WET_WEATHER_TYRE_WINDOW"


def test_strategy_explains_when_tyre_age_is_too_low():
    config = load_pit_strategy_config()

    decision, reason = evaluate_pit_decision(
        lap_number=10,
        tyre_age=3,
        tyre_wear=0.80,
        tyre_management=0.70,
        wet_weather_performance=0.80,
        weather_condition="DRY",
        pit_stop_count=0,
        laps_since_last_stop=3,
        config=config,
    )

    assert decision is False
    assert reason == "MINIMUM_STINT_NOT_REACHED"


def test_strategy_explains_when_wear_is_below_window():
    config = load_pit_strategy_config()

    decision, reason = evaluate_pit_decision(
        lap_number=20,
        tyre_age=20,
        tyre_wear=0.20,
        tyre_management=0.70,
        wet_weather_performance=0.80,
        weather_condition="DRY",
        pit_stop_count=0,
        laps_since_last_stop=20,
        config=config,
    )

    assert decision is False
    assert reason == "TYRE_WEAR_BELOW_WINDOW"


def test_strategy_explanation_is_recorded_in_snapshot():
    from simulator.scenario import ScenarioType
    from simulator.simulator import create_simulator

    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    simulator.advance_laps(35)

    snapshots = simulator.snapshot_history

    pit_snapshots = [
        snapshot
        for snapshot in snapshots
        if snapshot.pit_stop
    ]

    assert pit_snapshots

    for snapshot in pit_snapshots:
        assert snapshot.strategy_decision == "PIT"
        assert snapshot.strategy_decision_reason
        assert snapshot.strategy_decision_lap == snapshot.lap
