"""
Gap Trend KPI - Parv's ownership (engine/formulas/).
Tracks a rolling window of each car's gap_to_leader_ms and computes
the average per-lap change. Reads thresholds and window_size live
from engine.config.loader. Windowing delegated to engine.windows.RollingWindow
and severity classification to engine.rules.severity_rules
(structural change only - same outputs as before).
"""
from engine.config.loader import get_config
from engine.windows.rolling_window import RollingWindow
from engine.rules.severity_rules import evaluate_severity

_window = RollingWindow(window_size=3)  # initial size; resized live below


def compute_gap_trend(car_id: str, gap_to_leader_ms: int) -> dict:
    gt_config = get_config()["gap_trend"]
    window_size = gt_config["window_size"]
    warning_ms_per_lap = gt_config["severity_thresholds"]["widening_warning_ms_per_lap"]
    critical_ms_per_lap = gt_config["severity_thresholds"]["widening_critical_ms_per_lap"]

    if window_size != _window.window_size:
        _window.set_window_size(window_size)

    _window.push(car_id, gap_to_leader_ms)

    if not _window.is_full(car_id):
        return {
            "kpi_id": "KPI-002",
            "car_id": car_id,
            "gap_to_leader_ms": gap_to_leader_ms,
            "trend_ms_per_lap": 0,
            "severity": "none",
        }

    history = _window.get(car_id)
    laps_spanned = len(history) - 1
    trend_ms_per_lap = (history[-1] - history[0]) / laps_spanned

    # Asymmetric by design: only a widening gap (falling behind) can alert.
    # A car catching up (negative trend) is never a severity condition -
    # that decision lives here, not inside evaluate_severity().
    if trend_ms_per_lap > 0:
        severity = evaluate_severity(trend_ms_per_lap, warning_ms_per_lap, critical_ms_per_lap)
    else:
        severity = "none"

    return {
        "kpi_id": "KPI-002",
        "car_id": car_id,
        "gap_to_leader_ms": gap_to_leader_ms,
        "trend_ms_per_lap": round(trend_ms_per_lap, 1),
        "severity": severity,
    }
