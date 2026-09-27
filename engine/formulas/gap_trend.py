"""
Gap Trend KPI - Parv's ownership (engine/formulas/).
Tracks a rolling window of each car's gap_to_leader_ms and computes
the average per-lap change. Reads thresholds and window_size live
from engine.config.loader.
"""
from collections import deque
from engine.config.loader import get_config

_gap_history_by_car: dict[str, deque] = {}
_window_size_in_use_by_car: dict[str, int] = {}

def compute_gap_trend(car_id: str, gap_to_leader_ms: int) -> dict:
    gt_config = get_config()["gap_trend"]
    window_size = gt_config["window_size"]
    warning_ms_per_lap = gt_config["severity_thresholds"]["widening_warning_ms_per_lap"]
    critical_ms_per_lap = gt_config["severity_thresholds"]["widening_critical_ms_per_lap"]

    if _window_size_in_use_by_car.get(car_id) != window_size:
        existing = list(_gap_history_by_car.get(car_id, []))
        _gap_history_by_car[car_id] = deque(existing[-window_size:], maxlen=window_size)
        _window_size_in_use_by_car[car_id] = window_size

    history = _gap_history_by_car[car_id]
    history.append(gap_to_leader_ms)

    if len(history) < 2:
        return {
            "kpi_id": "KPI-002",
            "car_id": car_id,
            "gap_to_leader_ms": gap_to_leader_ms,
            "trend_ms_per_lap": 0,
            "severity": "none",
        }

    laps_spanned = len(history) - 1
    trend_ms_per_lap = (history[-1] - history[0]) / laps_spanned

    if trend_ms_per_lap >= critical_ms_per_lap:
        severity = "critical"
    elif trend_ms_per_lap >= warning_ms_per_lap:
        severity = "warning"
    else:
        severity = "none"

    return {
        "kpi_id": "KPI-002",
        "car_id": car_id,
        "gap_to_leader_ms": gap_to_leader_ms,
        "trend_ms_per_lap": round(trend_ms_per_lap, 1),
        "severity": severity,
    }