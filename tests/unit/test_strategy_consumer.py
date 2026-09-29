from consumers.strategy.strategy_consumer import compute_signals, severity

def test_strategy_requires_timing_and_tyres():
    assert compute_signals({}) == []
    assert compute_signals({"timing": {}}) == []

def test_strategy_signal_is_deterministic():
    state = {
        "timing": {"lap_time_ms": 92000},
        "best_lap_time_ms": 90000,
        "tyres": {"grip": 0.7, "degradation_per_lap": 0.08},
        "weather": {"track_wetness": 0.5},
        "pitstops": {"pit_stop": False},
    }
    signals = compute_signals(state)
    assert [s["kpi_id"] for s in signals] == ["STR-001", "STR-002"]
    assert signals[0]["value"] > 0
    assert severity(2.0, 0.75, 1.5) == "critical"
    assert severity(0.8, 0.75, 1.5) == "warning"
    assert severity(0.2, 0.75, 1.5) == "none"
