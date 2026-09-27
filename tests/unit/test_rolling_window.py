"""
Unit tests for engine.windows.rolling_window.RollingWindow.
Run with: pytest tests/unit/test_rolling_window.py -v
"""
import pytest
from engine.windows.rolling_window import RollingWindow


def test_rejects_window_size_below_2():
    with pytest.raises(ValueError):
        RollingWindow(window_size=1)


def test_not_full_before_two_values():
    window = RollingWindow(window_size=3)
    window.push("CAR_01", 100)
    assert window.is_full("CAR_01") is False


def test_full_after_two_values():
    window = RollingWindow(window_size=3)
    window.push("CAR_01", 100)
    window.push("CAR_01", 200)
    assert window.is_full("CAR_01") is True


def test_evicts_oldest_beyond_window_size():
    window = RollingWindow(window_size=3)
    for value in [1, 2, 3, 4, 5]:
        window.push("CAR_01", value)
    # window_size=3, so only the most recent 3 pushes should remain
    assert window.get("CAR_01") == [3, 4, 5]


def test_separate_entities_do_not_share_history():
    window = RollingWindow(window_size=3)
    window.push("CAR_01", 100)
    window.push("CAR_02", 999)
    assert window.get("CAR_01") == [100]
    assert window.get("CAR_02") == [999]


def test_unknown_entity_returns_empty_list():
    window = RollingWindow(window_size=3)
    assert window.get("CAR_UNKNOWN") == []
    assert window.is_full("CAR_UNKNOWN") is False


def test_set_window_size_rejects_below_2():
    window = RollingWindow(window_size=3)
    with pytest.raises(ValueError):
        window.set_window_size(1)


def test_set_window_size_shrinks_on_next_push():
    window = RollingWindow(window_size=5)
    for value in [1, 2, 3, 4, 5]:
        window.push("CAR_01", value)
    window.set_window_size(2)
    window.push("CAR_01", 6)
    # After resizing to 2 and pushing once more, only the last 2 values remain
    assert window.get("CAR_01") == [5, 6]
