"""
Generic severity rule evaluator - Parv's ownership (engine/rules/).

Centralizes the ascending-threshold comparison (value >= critical -> critical,
value >= warning -> warning, else none) that was previously duplicated as an
inline if/elif chain inside both KPI-001 (Lap Pace Delta) and KPI-002 (Gap
Trend). This is a structural extraction, not a formula change - existing
severity outputs are identical to before.

Each KPI decides for itself what value to pass in (e.g. KPI-002 only calls
this for positive/widening trends, since a car catching up is never an
alert condition - that asymmetry lives in the KPI module, not here).
"""


def evaluate_severity(value: float, warning_threshold: float, critical_threshold: float) -> str:
    """
    Ascending-severity rule.

    Returns "critical" if value >= critical_threshold, "warning" if
    value >= warning_threshold, otherwise "none".

    Assumes warning_threshold < critical_threshold - this is enforced at
    config-load time by engine/config/loader.py's _validate(), so it is
    not re-checked here on every call for performance.
    """
    if value >= critical_threshold:
        return "critical"
    if value >= warning_threshold:
        return "warning"
    return "none"
