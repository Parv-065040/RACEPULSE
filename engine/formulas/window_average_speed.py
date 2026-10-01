"""
KPI-003: Average vehicle speed over a completed tumbling window.
"""

from __future__ import annotations


def compute_average_speed(events: list[dict]) -> float:
    if not events:
        raise ValueError("cannot calculate average speed from an empty window")

    return sum(
        float(event["speed_kmh"])
        for event in events
    ) / len(events)
