"""
Unit tests for engine.formulas.lap_pace_delta.compute_lap_pace_delta.
get_config is monkeypatched so these tests are deterministic and do not
depend on the actual config/thresholds.yaml file, the background reload
thread, or test ordering.
Run with: pytest tests/unit/test_lap_pace_delta.py -v
"""
import pytest
from engine.formulas import lap_pace_delta


FAKE_CONFIG = {
    "lap_pace_delta": {
        "severity_thresholds": {"warning_ms": 500, "critical_ms": 1500}
    }
}


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Each test starts with a clean per-car state and a fixed fake config."""
    monkeypatch.setattr(lap_pace_delta, "get_config", lambda: FAKE_CONFIG)
    lap_pace_delta._best_lap_by_car.clear()
    yield
    lap_pace_delta._best_lap_by_car.clear()


def test_first_lap_for_a_car_has_zero_delta_and_none_severity():
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    assert result == {
        "kpi_id": "KPI-001",
        "car_id": "CAR_01",
        "lap_time_ms": 90000,
        "best_lap_time_ms": 90000,
        "delta_ms": 0,
        "severity": "none",
    }


def test_faster_lap_becomes_new_best_with_zero_or_negative_delta():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 89500)
    assert result["best_lap_time_ms"] == 89500
    assert result["delta_ms"] == -500
    assert result["severity"] == "none"


def test_delta_below_warning_threshold_is_none():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 90499)  # delta = 499
    assert result["severity"] == "none"


def test_delta_at_warning_threshold_is_warning():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 90500)  # delta = 500
    assert result["severity"] == "warning"


def test_delta_at_critical_threshold_is_critical():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 91500)  # delta = 1500
    assert result["severity"] == "critical"


def test_best_lap_never_regresses_to_a_slower_time():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 89000)  # new best = 89000
    result = lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)  # slower lap
    assert result["best_lap_time_ms"] == 89000  # best must not move backward
    assert result["delta_ms"] == 1000  # 90000 - 89000


def test_multiple_cars_track_independent_state():
    lap_pace_delta.compute_lap_pace_delta("CAR_01", 90000)
    lap_pace_delta.compute_lap_pace_delta("CAR_02", 95000)
    result_car_01 = lap_pace_delta.compute_lap_pace_delta("CAR_01", 90600)
    result_car_02 = lap_pace_delta.compute_lap_pace_delta("CAR_02", 95600)
    assert result_car_01["best_lap_time_ms"] == 90000
    assert result_car_02["best_lap_time_ms"] == 95000
    assert result_car_01["delta_ms"] == 600
    assert result_car_02["delta_ms"] == 600
