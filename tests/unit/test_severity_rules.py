"""
Unit tests for engine.rules.severity_rules.evaluate_severity.
Run with: pytest tests/unit/test_severity_rules.py -v
"""
from engine.rules.severity_rules import evaluate_severity


def test_below_warning_is_none():
    assert evaluate_severity(value=100, warning_threshold=500, critical_threshold=1500) == "none"


def test_at_warning_threshold_is_warning():
    assert evaluate_severity(value=500, warning_threshold=500, critical_threshold=1500) == "warning"


def test_between_warning_and_critical_is_warning():
    assert evaluate_severity(value=900, warning_threshold=500, critical_threshold=1500) == "warning"


def test_at_critical_threshold_is_critical():
    assert evaluate_severity(value=1500, warning_threshold=500, critical_threshold=1500) == "critical"


def test_above_critical_threshold_is_critical():
    assert evaluate_severity(value=999999, warning_threshold=500, critical_threshold=1500) == "critical"


def test_negative_value_is_none():
    assert evaluate_severity(value=-500, warning_threshold=500, critical_threshold=1500) == "none"


def test_zero_value_is_none():
    assert evaluate_severity(value=0, warning_threshold=500, critical_threshold=1500) == "none"
