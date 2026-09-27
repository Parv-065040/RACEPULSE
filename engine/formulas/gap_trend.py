"""
Gap Trend KPI - Parv's ownership (engine/formulas/).
Tracks a rolling window of each car's gap_to_leader_ms and computes
the average per-lap change across that window. Positive = falling
behind the leader; negative = catching up.
"""
from collections import deque
import yaml

with open("config/thresholds.yaml", "r", encoding="utf-8-sig") as f:
    _CONFIG = yaml.safe_load(f)["gap_trend"]

WINDOW_SIZE = _CONFIG["window_size"]
WARNING_MS_PER_LAP = _CONFIG["severity_thresholds"]["widening_warning_ms_per_lap"]
CRITICAL_MS_PER_LAP = _CONFIG["severity_thresholds"]["widening_critical_ms_per_lap"]

_gap_history_by_car: dict[str, deque] = {}

def compute_gap_trend(car_id: str, gap_to_leader_ms: int) -> dict:
    """
    Returns a dict with the KPI result for this lap event.
    Needs at least 2 laps in the window to compute a trend; before
    that, trend is 0 and severity is "none" (not enough data yet).
    """
    history = _gap_history_by_car.setdefault(car_id, deque(maxlen=WINDOW_SIZE))
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

    if trend_ms_per_lap >= CRITICAL_MS_PER_LAP:
        severity = "critical"
    elif trend_ms_per_lap >= WARNING_MS_PER_LAP:
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