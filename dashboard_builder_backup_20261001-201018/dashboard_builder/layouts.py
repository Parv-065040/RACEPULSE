"""Reusable 24-column layouts for RACEPULSE Grafana dashboards."""

from __future__ import annotations

from typing import Any


GRID_COLUMNS = 24


def row(
    y: int,
    height: int,
    panels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Place panels into a predefined dashboard row."""

    for panel in panels:
        panel.setdefault("gridPos", {})
        panel["gridPos"]["y"] = y
        panel["gridPos"]["h"] = height

    return panels


def full_width(
    panel: dict[str, Any],
    y: int,
    height: int,
) -> dict[str, Any]:
    """Place a panel across the complete 24-column grid."""

    panel["gridPos"] = {
        "x": 0,
        "y": y,
        "w": GRID_COLUMNS,
        "h": height,
    }

    return panel


def half_width(
    left: dict[str, Any],
    right: dict[str, Any],
    y: int,
    height: int,
) -> list[dict[str, Any]]:
    """Create two equal-width panels."""

    left["gridPos"] = {
        "x": 0,
        "y": y,
        "w": 12,
        "h": height,
    }

    right["gridPos"] = {
        "x": 12,
        "y": y,
        "w": 12,
        "h": height,
    }

    return [left, right]


def thirds(
    first: dict[str, Any],
    second: dict[str, Any],
    third: dict[str, Any],
    y: int,
    height: int,
) -> list[dict[str, Any]]:
    """Create three equal-width panels."""

    panels = [first, second, third]

    for index, panel in enumerate(panels):
        panel["gridPos"] = {
            "x": index * 8,
            "y": y,
            "w": 8,
            "h": height,
        }

    return panels


def stat_strip(
    panels: list[dict[str, Any]],
    y: int = 0,
    height: int = 4,
) -> list[dict[str, Any]]:
    """Distribute KPI/stat panels evenly across the 24-column grid."""

    if not panels:
        return []

    width = GRID_COLUMNS // len(panels)

    for index, panel in enumerate(panels):
        panel["gridPos"] = {
            "x": index * width,
            "y": y,
            "w": width,
            "h": height,
        }

    return panels


def next_row_y(
    panels: list[dict[str, Any]],
    default: int = 0,
) -> int:
    """Return the next available Y coordinate."""

    if not panels:
        return default

    return max(
        panel.get("gridPos", {}).get("y", 0)
        + panel.get("gridPos", {}).get("h", 0)
        for panel in panels
    )
