"""
Lap Pace Delta KPI - Parv's ownership (engine/formulas/).
Tracks each car's best lap time seen so far and computes the delta
for every new lap. Stateful per car_id, in-memory (no persistence yet -
that is Step 5, once MySQL is wired in).
"""
import yaml

with open("config/thresholds.yaml", "r", encoding="utf-8-sig") as f:
    _CONFIG = yaml.safe_load(f)["lap_pace_delta"]

WARNING_MS = _CONFIG["severity_thresholds"]["warning_ms"]
CRITICAL_MS = _CONFIG["severity_thresholds"]["critical_ms"]

_best_lap_by_car: dict[str, int] = {}

def compute_lap_pace_delta(car_id: str, lap_time_ms: int) -> dict:
    """
    Returns a dict with the KPI result for this lap event.
    First lap for a car has no prior best, so delta is 0 and severity is "none".
    """
    previous_best = _best_lap_by_car.get(car_id)

    if previous_best is None:
        _best_lap_by_car[car_id] = lap_time_ms
        return {
            "kpi_id": "KPI-001",
            "car_id": car_id,
            "lap_time_ms": lap_time_ms,
            "best_lap_time_ms": lap_time_ms,
            "delta_ms": 0,
            "severity": "none",
        }

    delta_ms = lap_time_ms - previous_best

    if delta_ms >= CRITICAL_MS:
        severity = "critical"
    elif delta_ms >= WARNING_MS:
        severity = "warning"
    else:
        severity = "none"

    if lap_time_ms < previous_best:
        _best_lap_by_car[car_id] = lap_time_ms

    return {
        "kpi_id": "KPI-001",
        "car_id": car_id,
        "lap_time_ms": lap_time_ms,
        "best_lap_time_ms": _best_lap_by_car[car_id],
        "delta_ms": delta_ms,
        "severity": severity,
    }
