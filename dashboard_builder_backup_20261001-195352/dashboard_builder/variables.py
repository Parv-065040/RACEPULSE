"""Reusable Grafana dashboard variables."""

def car_variable():
    return {
        "name": "car",
        "label": "CAR",
        "type": "query",
        "query": "SELECT DISTINCT car_id FROM kpi_results ORDER BY car_id",
        "includeAll": True,
        "allValue": ".*",
        "multi": True,
        "refresh": 2,
        "current": {
            "text": "All",
            "value": "$__all",
        },
    }


def severity_variable():
    return {
        "name": "severity",
        "label": "SEVERITY",
        "type": "custom",
        "query": "all,critical,warning,none",
        "includeAll": True,
        "allValue": ".*",
        "multi": True,
        "current": {
            "text": "All",
            "value": "$__all",
        },
    }


def dashboard_variables():
    return [
        car_variable(),
        severity_variable(),
    ]
