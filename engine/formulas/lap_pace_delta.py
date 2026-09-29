"""
Lap Pace Delta KPI - Parv's ownership (engine/formulas/).
Tracks each car's best lap time seen so far and computes the delta
for every new lap. Reads thresholds live from engine.config.loader,
so a config change takes effect without restarting the consumer.
Severity classification delegated to engine.rules.severity_rules
(structural change only - same outputs as before).
"""
from engine.config.loader import get_config
from engine.rules.severity_rules import evaluate_severity

_best_lap_by_car: dict[str, int] = {}


def compute_lap_pace_delta(car_id: str, lap_time_ms: int) -> dict:
    thresholds = get_config()["lap_pace_delta"]["severity_thresholds"]
    warning_ms = thresholds["warning_ms"]
    critical_ms = thresholds["critical_ms"]

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
    severity = evaluate_severity(delta_ms, warning_ms, critical_ms)

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
