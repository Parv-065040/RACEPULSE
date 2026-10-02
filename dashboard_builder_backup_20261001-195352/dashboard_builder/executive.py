"""RACEPULSE CEO Command Center dashboard."""

from __future__ import annotations

from . import queries
from . import theme
from .components import (
    alert_table_panel,
    stat_panel,
    table_panel,
    text_panel,
    timeseries_panel,
)
from .layouts import half_width, stat_strip


def build() -> dict:
    """Build the production CEO Command Center dashboard."""

    panels: list[dict] = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    panels.append(
        text_panel(
            "RACEPULSE // CEO COMMAND CENTER",
            """
# RACEPULSE // CEO COMMAND CENTER

**LIVE RACE INTELLIGENCE**  
Streaming telemetry • strategy • race control • commercial intelligence

`SENSE → STREAM → ANALYZE → ALERT → DECIDE`
            """.strip(),
            0,
            0,
            24,
            4,
        )
    )

    # ------------------------------------------------------------------
    # Executive KPI strip
    # ------------------------------------------------------------------

    panels.extend(
        stat_strip(
            [
                stat_panel(
                    "Latest Lap",
                    queries.LATEST_LAP,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.TELEMETRY,
                ),
                stat_panel(
                    "Critical Alerts",
                    queries.CRITICAL_ALERTS,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.CRITICAL,
                ),
                stat_panel(
                    "Strategy Signals",
                    queries.STRATEGY_SIGNALS,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.STRATEGY,
                ),
                stat_panel(
                    "Commercial Events",
                    queries.COMMERCIAL_EVENTS,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.COMMERCIAL,
                ),
                stat_panel(
                    "Cars Reporting",
                    """
                    SELECT COUNT(DISTINCT car_id) AS value
                    FROM kpi_results
                    WHERE $__timeFilter(event_time)
                      AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$' 
                    """,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.NORMAL,
                ),
                stat_panel(
                    "Windowed KPIs",
                    """
                    SELECT COUNT(*) AS value
                    FROM windowed_kpi_results
                    WHERE $__timeFilter(window_start)
                      AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$' 
                    """,
                    0,
                    4,
                    unit="none",
                    decimals=0,
                    fixed_color=theme.TELEMETRY,
                ),
            ],
            y=4,
            height=4,
        )
    )

    # ------------------------------------------------------------------
    # Main race intelligence
    # ------------------------------------------------------------------

    panels.extend(
        half_width(
            timeseries_panel(
                "Pace Delta // All Cars",
                queries.PACE_TIMELINE,
                0,
                8,
                12,
                9,
                unit="suffix:s",
                decimals=2,
            ),
            timeseries_panel(
                "Gap Trend // All Cars",
                queries.GAP_TIMELINE,
                12,
                8,
                12,
                9,
                unit="suffix:s",
                decimals=2,
            ),
            y=8,
            height=9,
        )
    )

    # ------------------------------------------------------------------
    # Strategy + commercial intelligence
    # ------------------------------------------------------------------

    panels.extend(
        half_width(
            timeseries_panel(
                "Strategy Risk",
                queries.STRATEGY_RISK,
                0,
                17,
                12,
                8,
                unit="short",
                decimals=3,
            ),
            timeseries_panel(
                "Commercial Activity",
                queries.COMMERCIAL_ACTIVITY,
                12,
                17,
                12,
                8,
                unit="short",
                decimals=3,
            ),
            y=17,
            height=8,
        )
    )

    # ------------------------------------------------------------------
    # Current car status
    # ------------------------------------------------------------------

    panels.append(
        table_panel(
            "Current Car Status // 12-Car Grid",
            queries.CURRENT_CAR_STATUS,
            0,
            25,
            24,
            9,
        )
    )

    # ------------------------------------------------------------------
    # Latest decision-support signals
    # ------------------------------------------------------------------

    panels.extend(
        half_width(
            alert_table_panel(
                "Latest Alerts",
                queries.LATEST_ALERTS,
                0,
                34,
                12,
                8,
            ),
            table_panel(
                "Latest Strategy Signals",
                queries.RECENT_STRATEGY_SIGNALS,
                12,
                34,
                12,
                8,
            ),
            y=34,
            height=8,
        )
    )

    # ------------------------------------------------------------------
    # Dashboard document
    # ------------------------------------------------------------------

    return {
        "id": None,
        "uid": "racepulse-ceo-command-center",
        "title": "RACEPULSE // CEO Command Center",
        "tags": [
            "racepulse",
            "executive",
            "command-center",
            "live",
        ],
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": theme.REFRESH,
        "time": theme.BASE_TIME,
        "editable": True,
        "graphTooltip": 1,
        "style": "dark",
        "templating": {
            "list": [],
        },
        "annotations": {
            "list": [],
        },
        "panels": panels,
    }
