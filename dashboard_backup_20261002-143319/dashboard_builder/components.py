"""Reusable Grafana panel components for RACEPULSE."""

from __future__ import annotations

from typing import Any

from . import theme


def _field_override(
    *,
    unit: str | None = None,
    decimals: int | None = None,
    thresholds: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    properties: list[dict[str, Any]] = []

    if unit is not None:
        properties.append({"id": "unit", "value": unit})

    if decimals is not None:
        properties.append({"id": "decimals", "value": decimals})

    if thresholds is not None:
        properties.append(
            {
                "id": "thresholds",
                "value": {
                    "mode": "absolute",
                    "steps": thresholds,
                },
            }
        )

    return {
        "matcher": {"id": "byName", "options": "value"},
        "properties": properties,
    }


def _base_panel(
    title: str,
    panel_type: str,
    x: int,
    y: int,
    w: int,
    h: int,
) -> dict[str, Any]:
    return {
        "type": panel_type,
        "title": title.upper(),
        "gridPos": {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
        },
        "transparent": False,
        "fieldConfig": {
            "defaults": {
                "color": {
                    "mode": "thresholds",
                },
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": theme.NORMAL, "value": None},
                        {"color": theme.WARNING, "value": 0.75},
                        {"color": theme.CRITICAL, "value": 1.0},
                    ],
                },
            },
            "overrides": [],
        },
        "options": {},
    }


def mysql_target(
    raw_sql: str,
    ref_id: str = "A",
    *,
    format: str = "table",
) -> dict[str, Any]:
    return {
        "datasource": {
            "type": "mysql",
            "uid": "racepulse-mysql",
        },
        "rawSql": raw_sql.strip(),
        "format": format,
        "refId": ref_id,
    }


def stat_panel(
    title: str,
    sql: str,
    x: int,
    y: int,
    w: int = 4,
    h: int = 4,
    *,
    unit: str = "short",
    decimals: int = 0,
    color_mode: str = "value",
    fixed_color: str | None = None,
) -> dict[str, Any]:
    panel = _base_panel(title, "stat", x, y, w, h)
    panel["targets"] = [mysql_target(sql, format="table")]

    panel["fieldConfig"]["defaults"].update(
        {
            "unit": unit,
            "decimals": decimals,
            "color": {
                "mode": "fixed",
                "fixedColor": fixed_color or theme.TEXT,
            },
        }
    )

    panel["options"] = {
        "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "/^value$/",
            "values": False,
        },
        "orientation": "auto",
        "textMode": "value",
        "colorMode": color_mode,
        "graphMode": "area",
        "justifyMode": "auto",
    }

    return panel


def timeseries_panel(
    title: str,
    sql: str,
    x: int,
    y: int,
    w: int = 12,
    h: int = 8,
    *,
    unit: str = "short",
    decimals: int = 1,
    line_width: int = 2,
    fill_opacity: int = 12,
) -> dict[str, Any]:
    panel = _base_panel(title, "timeseries", x, y, w, h)

    panel["targets"] = [mysql_target(sql, format="time_series")]

    panel["fieldConfig"]["defaults"].update(
        {
            "unit": unit,
            "decimals": decimals,
            "custom": {
                "drawStyle": "line",
                "lineInterpolation": "smooth",
                "barAlignment": 0,
                "lineWidth": line_width,
                "fillOpacity": fill_opacity,
                "gradientMode": "none",
                "spanNulls": True,
                "showPoints": "never",
                "pointSize": 5,
                "stacking": {
                    "mode": "none",
                    "group": "A",
                },
                "axisPlacement": "auto",
                "axisLabel": "",
                "axisColorMode": "text",
                "axisGridShow": True,
                "axisLabel": "",
                "scaleDistribution": {
                    "type": "linear",
                },
            },
        }
    )

    panel["options"] = {
        "legend": {
            "displayMode": "table",
            "placement": "bottom",
            "calcs": ["last", "max", "min"],
        },
        "tooltip": {
            "mode": "multi",
            "sort": "desc",
        },
    }

    return panel


def table_panel(
    title: str,
    sql: str,
    x: int,
    y: int,
    w: int = 12,
    h: int = 8,
) -> dict[str, Any]:
    panel = _base_panel(title, "table", x, y, w, h)
    panel["targets"] = [mysql_target(sql, format="table")]

    panel["options"] = {
        "showHeader": True,
        "cellHeight": "sm",
        "footer": {
            "show": False,
        },
        "sortBy": [],
    }

    panel["fieldConfig"]["defaults"] = {
        "color": {
            "mode": "thresholds",
        },
        "custom": {
            "align": "auto",
            "displayMode": "auto",
            "inspect": False,
        },
    }

    return panel


def gauge_panel(
    title: str,
    sql: str,
    x: int,
    y: int,
    w: int = 6,
    h: int = 6,
    *,
    unit: str = "short",
    decimals: int = 1,
    min_value: float = 0,
    max_value: float = 1,
) -> dict[str, Any]:
    panel = _base_panel(title, "gauge", x, y, w, h)
    panel["targets"] = [mysql_target(sql, format="table")]

    panel["fieldConfig"]["defaults"].update(
        {
            "unit": unit,
            "decimals": decimals,
            "min": min_value,
            "max": max_value,
            "color": {
                "mode": "thresholds",
            },
        }
    )

    panel["options"] = {
        "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": False,
        },
        "showThresholdLabels": False,
        "showThresholdMarkers": True,
        "orientation": "auto",
    }

    return panel


def text_panel(
    title: str,
    content: str,
    x: int,
    y: int,
    w: int = 24,
    h: int = 4,
) -> dict[str, Any]:
    panel = _base_panel(title, "text", x, y, w, h)

    panel["options"] = {
        "mode": "markdown",
        "content": content,
    }

    return panel


def alert_table_panel(
    title: str,
    sql: str,
    x: int,
    y: int,
    w: int = 24,
    h: int = 8,
) -> dict[str, Any]:
    panel = table_panel(title, sql, x, y, w, h)

    panel["fieldConfig"]["defaults"]["custom"] = {
        "align": "auto",
        "displayMode": "auto",
        "inspect": True,
    }

    return panel


def apply_panel_theme(
    panel: dict[str, Any],
    *,
    accent: str | None = None,
) -> dict[str, Any]:
    """Apply RACEPULSE visual defaults without changing panel semantics."""

    panel["transparent"] = False

    if accent:
        panel["fieldConfig"]["defaults"]["color"] = {
            "mode": "fixed",
            "fixedColor": accent,
        }

    return panel
