"""
Unit tests for engine.formulas.gap_trend.compute_gap_trend.
get_config is monkeypatched so these tests are deterministic and do not
depend on the actual config/thresholds.yaml file or its background reload
thread. The module-level RollingWindow instance is replaced fresh per test
so tests don't leak state into each other.
Run with: pytest tests/unit/test_gap_trend.py -v
"""
import pytest
from engine.formulas import gap_trend
from engine.windows.rolling_window import RollingWindow


FAKE_CONFIG = {
    "gap_trend": {
        "window_size": 3,
        "severity_thresholds": {
            "widening_warning_ms_per_lap": 200,
            "widening_critical_ms_per_lap": 400,
        },
    }
}


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    monkeypatch.setattr(gap_trend, "get_config", lambda: FAKE_CONFIG)
    monkeypatch.setattr(gap_trend, "_window", RollingWindow(window_size=3))
    yield


def test_first_lap_has_zero_trend_and_none_severity():
    result = gap_trend.compute_gap_trend("CAR_01", 3000)
    assert result["trend_ms_per_lap"] == 0
    assert result["severity"] == "none"


def test_second_lap_not_enough_for_a_trend_yet():
    gap_trend.compute_gap_trend("CAR_01", 3000)
    result = gap_trend.compute_gap_trend("CAR_01", 3200)
    # window_size=3 needs at least 2 values to compute a trend - this is
    # the 2nd value, so is_full() should now be true and a trend computed.
    assert result["trend_ms_per_lap"] == 200.0


def test_widening_gap_below_warning_is_none():
    gap_trend.compute_gap_trend("CAR_01", 3000)
    result = gap_trend.compute_gap_trend("CAR_01", 3100)  # trend = +100/lap
    assert result["severity"] == "none"


def test_widening_gap_at_warning_threshold_is_warning():
    gap_trend.compute_gap_trend("CAR_01", 3000)
    result = gap_trend.compute_gap_trend("CAR_01", 3200)  # trend = +200/lap
    assert result["severity"] == "warning"


def test_widening_gap_at_critical_threshold_is_critical():
    gap_trend.compute_gap_trend("CAR_01", 3000)
    result = gap_trend.compute_gap_trend("CAR_01", 3400)  # trend = +400/lap
    assert result["severity"] == "critical"


def test_narrowing_gap_never_alerts_even_with_large_magnitude():
    gap_trend.compute_gap_trend("CAR_01", 5000)
    result = gap_trend.compute_gap_trend("CAR_01", 1000)  # trend = -4000/lap
    assert result["trend_ms_per_lap"] == -4000.0
    assert result["severity"] == "none"  # catching up is never an alert


def test_flat_gap_is_none():
    gap_trend.compute_gap_trend("CAR_01", 3000)
    result = gap_trend.compute_gap_trend("CAR_01", 3000)
    assert result["trend_ms_per_lap"] == 0.0
    assert result["severity"] == "none"


def test_multiple_cars_track_independent_windows():
    gap_trend.compute_gap_trend("CAR_01", 1000)
    gap_trend.compute_gap_trend("CAR_02", 9000)
    result_car_01 = gap_trend.compute_gap_trend("CAR_01", 1200)  # +200/lap
    result_car_02 = gap_trend.compute_gap_trend("CAR_02", 8700)  # -300/lap
    assert result_car_01["severity"] == "warning"
    assert result_car_02["severity"] == "none"
