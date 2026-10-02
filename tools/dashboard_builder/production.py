
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .variables import dashboard_variables

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "grafana" / "dashboards" / "generated"

BG = "#080B10"
PANEL = "#0E131A"
PANEL_ALT = "#111821"
BORDER = "#27313C"
TEXT = "#E8EDF2"
MUTED = "#7F8B98"
NORMAL = "#36D399"
TELEMETRY = "#22D3EE"
STRATEGY = "#A78BFA"
COMMERCIAL = "#F5C451"
WARNING = "#F59E0B"
CRITICAL = "#EF4444"

CAR_RE = r"^CAR_(0[1-9]|1[0-2])$"


def target(sql: str, ref_id: str = "A", fmt: str = "table") -> dict[str, Any]:
    return {
        "refId": ref_id,
        "datasource": {"type": "mysql", "uid": "racepulse-mysql"},
        "rawSql": sql.strip(),
        "format": fmt,
    }


def base_panel(title: str, kind: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "type": kind,
        "title": title.upper(),
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "transparent": False,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "fixed", "fixedColor": TEXT},
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": NORMAL, "value": None},
                        {"color": WARNING, "value": 0.75},
                        {"color": CRITICAL, "value": 1.0},
                    ],
                },
            },
            "overrides": [],
        },
        "options": {},
    }


def stat(title: str, sql: str, x: int, y: int, color: str, unit: str = "none") -> dict[str, Any]:
    p = base_panel(title, "stat", x, y, 4, 4)
    p["targets"] = [target(sql)]
    p["fieldConfig"]["defaults"].update({
        "unit": unit,
        "decimals": 0,
        "color": {"mode": "fixed", "fixedColor": color},
    })
    p["options"] = {
        "reduceOptions": {"calcs": ["lastNotNull"], "fields": "/^value$/", "values": False},
        "orientation": "auto",
        "textMode": "value",
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "auto",
    }
    return p


def ts(title: str, sql: str, x: int, y: int, w: int = 12, h: int = 8,
       unit: str = "short", decimals: int = 1, fill: int = 10) -> dict[str, Any]:
    p = base_panel(title, "timeseries", x, y, w, h)
    p["targets"] = [target(sql, fmt="time_series")]
    p["fieldConfig"]["defaults"].update({
        "unit": unit,
        "decimals": decimals,
        "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth",
            "lineWidth": 2,
            "fillOpacity": fill,
            "gradientMode": "none",
            "spanNulls": True,
            "showPoints": "never",
            "pointSize": 4,
            "stacking": {"mode": "none", "group": "A"},
            "axisPlacement": "auto",
            "axisLabel": "",
            "scaleDistribution": {"type": "linear"},
        },
    })
    p["options"] = {
        "tooltip": {"mode": "multi", "sort": "desc"},
        "legend": {
            "displayMode": "table",
            "placement": "bottom",
            "calcs": ["lastNotNull", "max", "min"],
        },
    }
    return p


def table(title: str, sql: str, x: int, y: int, w: int = 12, h: int = 8) -> dict[str, Any]:
    p = base_panel(title, "table", x, y, w, h)
    p["targets"] = [target(sql)]
    p["options"] = {
        "showHeader": True,
        "cellHeight": "sm",
        "footer": {"show": False, "reducer": ["count"], "countRows": False, "fields": ""},
        "sortBy": [],
    }
    p["fieldConfig"]["defaults"] = {
        "custom": {
            "align": "auto",
            "cellOptions": {"type": "auto"},
            "inspect": False,
            "filterable": True,
            "wrapText": False,
        },
        "color": {"mode": "fixed", "fixedColor": TEXT},
        "thresholds": {"mode": "absolute", "steps": [{"color": TEXT, "value": None}]},
    }
    return p


def bar(title: str, sql: str, x: int, y: int, w: int = 12, h: int = 8,
        unit: str = "short", decimals: int = 1) -> dict[str, Any]:
    p = base_panel(title, "barchart", x, y, w, h)
    p["targets"] = [target(sql)]
    p["fieldConfig"]["defaults"].update({"unit": unit, "decimals": decimals})
    p["options"] = {
        "orientation": "horizontal",
        "showValue": "auto",
        "legend": {"displayMode": "hidden"},
        "tooltip": {"mode": "single"},
    }
    return p


def text(title: str, content: str, x: int, y: int, w: int = 24, h: int = 4) -> dict[str, Any]:
    p = base_panel(title, "text", x, y, w, h)
    p["options"] = {"mode": "markdown", "content": content}
    return p


def dashboard(uid: str, title: str, description: str, panels: list[dict[str, Any]]) -> dict[str, Any]:
    for i, p in enumerate(panels, 1):
        p["id"] = i
    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "links": [],
        "panels": panels,
        "refresh": "5s",
        "schemaVersion": 39,
        "tags": ["RACEPULSE", "streaming", "motorsport"],
        "templating": {"list": dashboard_variables()},
        "time": {"from": "now-30m", "to": "now"},
        "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
        "timezone": "browser",
        "title": title,
        "uid": uid,
        "version": 2,
        "description": description,
    }


def q(sql: str) -> str:
    return sql


def car_filter(alias: str) -> str:
    return f"""AND {alias}.car_id REGEXP '${{car:regex}}'"""





# Current-race scope is derived from the latest clean 60-lap race in kpi_results.
# Historical/replay/test rows remain in MySQL; dashboard queries simply exclude them.
RACE = f"""
WITH race AS (
    SELECT
        MAX(event_time) AS race_end,
        DATE_SUB(MAX(event_time), INTERVAL 10 MINUTE) AS race_start
    FROM kpi_results
    WHERE car_id REGEXP '{CAR_RE}'
      AND lap_number BETWEEN 1 AND 60
)
"""

LATEST_LAP = q(f"""
SELECT COALESCE(
    (
        SELECT k.lap_number
        FROM kpi_results k
        WHERE k.event_time = (
            SELECT MAX(k2.event_time)
            FROM kpi_results k2
            WHERE k2.car_id REGEXP '{CAR_RE}'
        )
        AND k.lap_number BETWEEN 1 AND 60
        LIMIT 1
    ),
    0
) AS value
""")

CRITICAL_ALERTS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM alerts a CROSS JOIN race
WHERE a.severity='critical'
  AND a.created_at BETWEEN DATE_SUB(race.race_end, INTERVAL 10 MINUTE)
                       AND DATE_ADD(race.race_end, INTERVAL 10 MINUTE)
""")

STRATEGY_SIGNALS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race
WHERE s.severity <> 'none'
  AND s.event_time BETWEEN race.race_start AND race.race_end
  AND s.lap_number BETWEEN 1 AND 60
  AND s.car_id REGEXP '{CAR_RE}'
  AND s.car_id REGEXP '${{car:regex}}'
""")

COMMERCIAL_EVENTS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM commercial_results c CROSS JOIN race
WHERE c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
""")

CARS_REPORTING = q(f"""
{RACE}
SELECT COUNT(DISTINCT k.car_id) AS value FROM kpi_results k CROSS JOIN race
WHERE k.event_time BETWEEN race.race_start AND race.race_end
  AND k.lap_number BETWEEN 1 AND 60
  AND k.car_id REGEXP '{CAR_RE}'
  AND k.car_id REGEXP '${{car:regex}}'
""")

WINDOWED_KPIS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM windowed_kpi_results w CROSS JOIN race
WHERE w.window_start BETWEEN race.race_start AND race.race_end
  AND w.car_id REGEXP '{CAR_RE}'
  AND w.car_id REGEXP '${{car:regex}}'
""")

PACE = q(f"""
{RACE}
,scoped AS (
    SELECT k.*,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS current_best_lap_ms
    FROM kpi_results k CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '{CAR_RE}'
      AND k.car_id REGEXP '${{car:regex}}'

)
SELECT event_time AS time,
       car_id,
       ROUND((lap_time_ms - current_best_lap_ms)/1000.0,3) AS pace_delta_s
FROM scoped
ORDER BY event_time
""")

GAP = q(f"""
{RACE}
SELECT g.event_time AS time, g.car_id,
       ROUND(g.trend_ms_per_lap/1000.0,3) AS gap_trend_s_per_lap
FROM gap_trend_results g CROSS JOIN race
WHERE g.event_time BETWEEN race.race_start AND race.race_end
  AND g.lap_number BETWEEN 1 AND 60
  AND g.car_id REGEXP '{CAR_RE}'
  AND g.car_id REGEXP '${{car:regex}}'
ORDER BY g.event_time
""")

SPEED = q(f"""
{RACE}
SELECT w.window_start AS time, w.car_id,
       ROUND(w.value,1) AS avg_speed_kmh
FROM windowed_kpi_results w CROSS JOIN race
WHERE w.kpi_id='KPI-003'
  AND w.window_start BETWEEN race.race_start AND race.race_end
  AND w.car_id REGEXP '{CAR_RE}'
  AND w.car_id REGEXP '${{car:regex}}'
ORDER BY w.window_start
""")

STRATEGY_RISK = q(f"""
{RACE}
SELECT s.event_time AS time, s.car_id, ROUND(s.value,3) AS strategy_risk
FROM strategy_results s CROSS JOIN race
WHERE s.kpi_id='STR-001'
  AND s.event_time BETWEEN race.race_start AND race.race_end
  AND s.lap_number BETWEEN 1 AND 60
  AND s.car_id REGEXP '{CAR_RE}'
  AND s.car_id REGEXP '${{car:regex}}'
ORDER BY s.event_time
""")

PIT_WINDOW = q(f"""
{RACE}
SELECT s.event_time AS time, s.car_id, ROUND(s.value,3) AS pit_window_signal
FROM strategy_results s CROSS JOIN race
WHERE s.kpi_id='STR-002'
  AND s.event_time BETWEEN race.race_start AND race.race_end
  AND s.lap_number BETWEEN 1 AND 60
  AND s.car_id REGEXP '{CAR_RE}'
  AND s.car_id REGEXP '${{car:regex}}'
ORDER BY s.event_time
""")

COMM_ENGAGEMENT = q(f"""
{RACE}
SELECT c.event_time AS time, c.car_id, ROUND(c.value*100,2) AS engagement_pct
FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-001'
  AND c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
  AND c.car_id REGEXP '{CAR_RE}'
  AND c.car_id REGEXP '${{car:regex}}'
ORDER BY c.event_time
""")

SPONSOR_VISIBILITY = q(f"""
{RACE}
SELECT c.event_time AS time, c.entity_id AS sponsor_id, ROUND(c.value,1) AS visibility_s
FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-002'
  AND c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
ORDER BY c.event_time
""")

COMM_CONVERSION = q(f"""
{RACE}
SELECT c.event_time AS time, c.entity_id AS sponsor_id, ROUND(c.value*100,2) AS conversion_pct
FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-003'
  AND c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
ORDER BY c.event_time
""")

CURRENT_CAR_STATUS = q(f"""
{RACE}
,scoped AS (
    SELECT kr.*,
           MIN(kr.lap_time_ms) OVER (PARTITION BY kr.car_id) AS current_best_lap_ms,
           ROW_NUMBER() OVER (
               PARTITION BY kr.car_id
               ORDER BY kr.event_time DESC, kr.id DESC
           ) AS rn
    FROM kpi_results kr CROSS JOIN race
    WHERE kr.event_time BETWEEN race.race_start AND race.race_end
      AND kr.lap_number BETWEEN 1 AND 60
      AND kr.car_id REGEXP '{CAR_RE}'
      AND kr.car_id REGEXP '${{car:regex}}'
),
gap_ranked AS (
    SELECT gt.*,
           ROW_NUMBER() OVER (
               PARTITION BY gt.car_id, gt.lap_number
               ORDER BY gt.event_time DESC, gt.id DESC
           ) AS rn
    FROM gap_trend_results gt CROSS JOIN race
    WHERE gt.event_time BETWEEN race.race_start AND race.race_end
      AND gt.lap_number BETWEEN 1 AND 60
      AND gt.car_id REGEXP '{CAR_RE}'
      AND gt.car_id REGEXP '${{car:regex}}'
)
SELECT s.car_id AS car,
       s.lap_number AS lap,
       ROUND(s.lap_time_ms/1000.0,3) AS lap_time_s,
       ROUND(s.current_best_lap_ms/1000.0,3) AS best_lap_s,
       ROUND((s.lap_time_ms-s.current_best_lap_ms)/1000.0,3) AS pace_delta_s,
       CASE
           WHEN (s.lap_time_ms-s.current_best_lap_ms) >= 1500 THEN 'critical'
           WHEN (s.lap_time_ms-s.current_best_lap_ms) >= 500 THEN 'warning'
           ELSE 'none'
       END AS pace_status,
       ROUND(COALESCE(g.gap_to_leader_ms,0)/1000.0,3) AS gap_s,
       ROUND(COALESCE(g.trend_ms_per_lap,0)/1000.0,3) AS gap_trend_s_per_lap,
       COALESCE(g.severity,'none') AS gap_status
FROM scoped s
LEFT JOIN gap_ranked g
  ON g.car_id=s.car_id
 AND g.lap_number=s.lap_number
 AND g.rn=1
WHERE s.rn=1
ORDER BY s.car_id
""")

STRATEGY_MATRIX = q(f"""
{RACE}, ranked AS (
    SELECT s.*,
           ROW_NUMBER() OVER (PARTITION BY s.car_id, s.kpi_id ORDER BY s.event_time DESC, s.id DESC) AS rn
    FROM strategy_results s CROSS JOIN race
    WHERE s.event_time BETWEEN race.race_start AND race.race_end
      AND s.lap_number BETWEEN 1 AND 60
      AND s.car_id REGEXP '{CAR_RE}'
      AND s.car_id REGEXP '${{car:regex}}'
)
SELECT car_id AS car,
       MAX(CASE WHEN kpi_id='STR-001' THEN ROUND(value,2) END) AS tyre_risk,
       MAX(CASE WHEN kpi_id='STR-002' THEN ROUND(value,2) END) AS pit_signal,
       MAX(CASE WHEN kpi_id='STR-001' THEN severity END) AS tyre_status,
       MAX(CASE WHEN kpi_id='STR-002' THEN severity END) AS pit_status,
       MAX(lap_number) AS lap
FROM ranked WHERE rn=1
GROUP BY car_id ORDER BY car_id
""")

STRATEGY_FEED = q(f"""
SELECT s.event_time AS time,
       s.car_id AS car,
       CASE s.kpi_id
           WHEN 'STR-001' THEN 'TYRE DEGRADATION RISK'
           WHEN 'STR-002' THEN 'PIT WINDOW SIGNAL'
           ELSE s.kpi_id
       END AS `signal`,
       ROUND(s.value,2) AS value,
       s.severity AS status,
       s.message
FROM strategy_results s
WHERE s.severity <> 'none'
  AND s.event_time BETWEEN
      DATE_SUB(
          (SELECT MAX(k.event_time)
           FROM kpi_results k
           WHERE k.lap_number BETWEEN 1 AND 60
             AND k.car_id REGEXP '{CAR_RE}'),
          INTERVAL 10 MINUTE
      )
  AND (SELECT MAX(k.event_time)
       FROM kpi_results k
       WHERE k.lap_number BETWEEN 1 AND 60
         AND k.car_id REGEXP '{CAR_RE}')
  AND s.lap_number BETWEEN 1 AND 60
ORDER BY s.event_time DESC
LIMIT 20
""")

RACE_CONTROL_MATRIX = q(f"""
{RACE}, ranked AS (
    SELECT rc.*,
           ROW_NUMBER() OVER (PARTITION BY rc.car_id, rc.kpi_id ORDER BY rc.event_time DESC, rc.id DESC) AS rn
    FROM race_control_results rc CROSS JOIN race
    WHERE rc.event_time BETWEEN race.race_start AND race.race_end
      AND rc.lap_number BETWEEN 1 AND 60
      AND rc.car_id REGEXP '{CAR_RE}'
      AND rc.car_id REGEXP '${{car:regex}}'
)
SELECT car_id AS car,
       MAX(CASE WHEN kpi_id='RC-001' THEN ROUND(value,2) END) AS track_risk,
       MAX(CASE WHEN kpi_id='RC-002' THEN ROUND(value,2) END) AS vehicle_risk,
       MAX(CASE WHEN kpi_id='RC-001' THEN severity END) AS track_status,
       MAX(CASE WHEN kpi_id='RC-002' THEN severity END) AS vehicle_status,
       MAX(lap_number) AS lap
FROM ranked WHERE rn=1
GROUP BY car_id ORDER BY car_id
""")

RACE_CONTROL_FEED = q(f"""
SELECT rc.event_time AS time,
       rc.car_id AS car,
       CASE rc.kpi_id
           WHEN 'RC-001' THEN 'TRACK RISK'
           WHEN 'RC-002' THEN 'VEHICLE RISK'
           ELSE rc.kpi_id
       END AS `signal`,
       ROUND(rc.value,2) AS value,
       rc.severity AS status,
       rc.message
FROM race_control_results rc
WHERE rc.severity <> 'none'
  AND rc.car_id REGEXP '{CAR_RE}'
  AND rc.car_id REGEXP '${{car:regex}}'
  AND rc.severity REGEXP '${{severity:regex}}'
  AND rc.lap_number BETWEEN 1 AND 60
  AND rc.event_time >= DATE_SUB(
      (SELECT MAX(event_time)
       FROM race_control_results
       WHERE lap_number BETWEEN 1 AND 60
         AND car_id REGEXP '{CAR_RE}'),
      INTERVAL 10 MINUTE
  )
ORDER BY rc.event_time DESC
LIMIT 20
""")

COMMERCIAL_SCORECARD = q(f"""
{RACE}
SELECT c.entity_id AS sponsor,
       ROUND(SUM(CASE WHEN c.kpi_id='COM-002' THEN c.value ELSE 0 END),1) AS visibility_s,
       ROUND(AVG(CASE WHEN c.kpi_id='COM-003' THEN c.value END)*100,2) AS conversion_pct,
       COUNT(CASE WHEN c.kpi_id='COM-002' THEN 1 END) AS visibility_events,
       MAX(c.lap_number) AS latest_lap
FROM commercial_results c CROSS JOIN race
WHERE c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
  AND c.kpi_id IN ('COM-002','COM-003')
  AND c.entity_id REGEXP '^SPONSOR_[0-9]+$'
GROUP BY c.entity_id
ORDER BY visibility_s DESC
LIMIT 12
""")

COMMERCIAL_FEED = q(f"""
{RACE}
SELECT c.event_time AS time, c.entity_id AS sponsor,
       CASE c.kpi_id WHEN 'COM-001' THEN 'FAN ENGAGEMENT'
                     WHEN 'COM-002' THEN 'SPONSOR VISIBILITY'
                     WHEN 'COM-003' THEN 'SPONSOR CONVERSION' ELSE c.kpi_id END AS metric,
       ROUND(c.value,3) AS value, c.unit
FROM commercial_results c CROSS JOIN race
WHERE c.event_time BETWEEN race.race_start AND race.race_end
  AND c.lap_number BETWEEN 1 AND 60
ORDER BY c.event_time DESC LIMIT 20
""")

ALERT_FEED = q(f"""
SELECT a.created_at AS time,
       a.car_id AS car,
       a.kpi_id AS `signal`,
       a.severity AS status,
       a.message
FROM alerts a
WHERE a.created_at >= DATE_SUB(
    (SELECT MAX(created_at) FROM alerts),
    INTERVAL 10 MINUTE
)
  AND a.car_id REGEXP '${{car:regex}}'
  AND a.severity REGEXP '${{severity:regex}}'
ORDER BY a.created_at DESC
LIMIT 20
""")

PERFORMANCE_ALERTS = q(f"""
{RACE}
,scoped AS (
    SELECT k.*,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS current_best_lap_ms
    FROM kpi_results k CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '{CAR_RE}'
      AND k.car_id REGEXP '${{car:regex}}'
),
alert_rows AS (
    SELECT event_time, car_id, kpi_id,
           ROUND((lap_time_ms-current_best_lap_ms)/1000.0,2) AS pace_delta_s,
           CASE
               WHEN (lap_time_ms-current_best_lap_ms) >= 1500 THEN 'critical'
               WHEN (lap_time_ms-current_best_lap_ms) >= 500 THEN 'warning'
               ELSE 'none'
           END AS status
    FROM scoped
    WHERE (lap_time_ms-current_best_lap_ms) >= 500
)
SELECT event_time AS time,
       car_id AS car,
       kpi_id AS `signal`,
       pace_delta_s,
       status
FROM alert_rows
WHERE status REGEXP '${{severity:regex}}'
ORDER BY event_time DESC
LIMIT 20
""")

LAP_TIME = q(f"""
{RACE}
SELECT k.event_time AS time, k.car_id, ROUND(k.lap_time_ms/1000.0,3) AS lap_time_s
FROM kpi_results k CROSS JOIN race
WHERE k.event_time BETWEEN race.race_start AND race.race_end
  AND k.lap_number BETWEEN 1 AND 60
  AND k.car_id REGEXP '{CAR_RE}'
  AND k.car_id REGEXP '${{car:regex}}'
ORDER BY k.event_time
""")

STRATEGY_CRITICAL = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race
WHERE s.severity REGEXP '${{severity:regex}}' AND s.event_time BETWEEN race.race_start AND race.race_end AND s.lap_number BETWEEN 1 AND 60
""")
STRATEGY_WARNING = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race
WHERE s.severity REGEXP '${{severity:regex}}' AND s.event_time BETWEEN race.race_start AND race.race_end AND s.lap_number BETWEEN 1 AND 60
""")
PIT_SIGNALS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race
WHERE s.kpi_id='STR-002' AND s.value>=0.6 AND s.event_time BETWEEN race.race_start AND race.race_end AND s.lap_number BETWEEN 1 AND 60
""")
MAX_TYRE_RISK = q(f"""
{RACE}
SELECT COALESCE(ROUND(MAX(s.value),2),0) AS value FROM strategy_results s CROSS JOIN race
WHERE s.kpi_id='STR-001' AND s.event_time BETWEEN race.race_start AND race.race_end AND s.lap_number BETWEEN 1 AND 60
""")
TRACK_RISK_SIGNALS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM race_control_results rc CROSS JOIN race
WHERE rc.kpi_id='RC-001' AND rc.severity<>'none' AND rc.event_time BETWEEN race.race_start AND race.race_end AND rc.lap_number BETWEEN 1 AND 60
""")
VEHICLE_RISK_SIGNALS = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM race_control_results rc CROSS JOIN race
WHERE rc.kpi_id='RC-002' AND rc.severity<>'none' AND rc.event_time BETWEEN race.race_start AND race.race_end AND rc.lap_number BETWEEN 1 AND 60
""")
RC_TRACK = q(f"""
{RACE}
SELECT rc.event_time AS time, rc.car_id, ROUND(rc.value,3) AS track_risk
FROM race_control_results rc CROSS JOIN race
WHERE rc.kpi_id='RC-001' AND rc.event_time BETWEEN race.race_start AND race.race_end AND rc.lap_number BETWEEN 1 AND 60
ORDER BY rc.event_time
""")
RC_VEHICLE = q(f"""
{RACE}
SELECT rc.event_time AS time, rc.car_id, ROUND(rc.value,3) AS vehicle_risk
FROM race_control_results rc CROSS JOIN race
WHERE rc.kpi_id='RC-002' AND rc.event_time BETWEEN race.race_start AND race.race_end AND rc.lap_number BETWEEN 1 AND 60
ORDER BY rc.event_time
""")
RC_CRITICAL = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM race_control_results rc CROSS JOIN race
WHERE rc.severity REGEXP '${{severity:regex}}' AND rc.event_time BETWEEN race.race_start AND race.race_end AND rc.lap_number BETWEEN 1 AND 60
""")
COMM_ENGAGEMENT_AVG = q(f"""
{RACE}
SELECT COALESCE(ROUND(AVG(c.value)*100,2),0) AS value FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-001' AND c.event_time BETWEEN race.race_start AND race.race_end AND c.lap_number BETWEEN 1 AND 60
""")
COMM_VISIBILITY = q(f"""
{RACE}
SELECT COALESCE(ROUND(SUM(c.value),1),0) AS value FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-002' AND c.event_time BETWEEN race.race_start AND race.race_end AND c.lap_number BETWEEN 1 AND 60
""")
COMM_CONVERSION_AVG = q(f"""
{RACE}
SELECT COALESCE(ROUND(AVG(c.value)*100,2),0) AS value FROM commercial_results c CROSS JOIN race
WHERE c.kpi_id='COM-003' AND c.event_time BETWEEN race.race_start AND race.race_end AND c.lap_number BETWEEN 1 AND 60
""")

# Engineering observability is independent of the race session.
DLQ_COUNT = q("""
SELECT COUNT(*) AS value FROM dlq_events
WHERE failed_at >= DATE_SUB((SELECT MAX(failed_at) FROM dlq_events), INTERVAL 30 MINUTE)
""")
STALE_COUNT = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM alerts a CROSS JOIN race
WHERE a.kpi_id='SYS-STALE'
  AND a.created_at BETWEEN DATE_SUB(race.race_end, INTERVAL 10 MINUTE) AND DATE_ADD(race.race_end, INTERVAL 10 MINUTE)
""")
INFRA_CRITICAL = q("""
SELECT COUNT(*) AS value
FROM infra_alerts
WHERE severity = 'critical'
  AND observed_at >= DATE_SUB(
      (SELECT COALESCE(MAX(observed_at), CURRENT_TIMESTAMP) FROM infra_alerts),
      INTERVAL 30 MINUTE
  )
""")
# These tables are currently empty. Return an intentional empty result rather than inventing health data.
STREAM_LAG_MAX = q("SELECT NULL AS value WHERE 1=0")

LAG_TIMELINE = q("""
SELECT created_at AS time,
       COUNT(*) AS alert_events
FROM alerts
WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)
GROUP BY created_at
ORDER BY created_at
""")

HEALTH_MATRIX = q("""
SELECT
    'Alert Pipeline' AS consumer,
    COUNT(*) AS events_seen,
    SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) AS critical_events,
    SUM(CASE WHEN severity='warning' THEN 1 ELSE 0 END) AS warning_events,
    MAX(created_at) AS last_event,
    'ACTIVE' AS status
FROM alerts
WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)
""")

INFRA_FEED = q("""
SELECT created_at AS time,
       kpi_id AS `signal`,
       severity AS status,
       'Alert Monitor' AS component,
       message
FROM alerts
WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)
ORDER BY created_at DESC
LIMIT 20
""")
DLQ_TIMELINE = q("""
SELECT failed_at AS time, source_topic, COUNT(*) AS dlq_events
FROM dlq_events
WHERE failed_at >= DATE_SUB((SELECT MAX(failed_at) FROM dlq_events), INTERVAL 30 MINUTE)
GROUP BY failed_at, source_topic ORDER BY failed_at
""")
DATA_QUALITY = q("""
SELECT failed_at AS time, source_topic AS topic, raw_key, errors
FROM dlq_events
WHERE failed_at >= DATE_SUB((SELECT MAX(failed_at) FROM dlq_events), INTERVAL 30 MINUTE)
ORDER BY failed_at DESC LIMIT 30
""")


CURRENT_PACE_RANKING = q(f"""
{RACE}
,ranked AS (
    SELECT k.car_id,
           k.lap_time_ms,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS best_lap_ms,
           ROW_NUMBER() OVER (
               PARTITION BY k.car_id
               ORDER BY k.event_time DESC, k.id DESC
           ) AS rn
    FROM kpi_results k CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '{CAR_RE}'
      AND k.car_id REGEXP '${car:regex}'
)
SELECT car_id AS car,
       ROUND((lap_time_ms-best_lap_ms)/1000.0,2) AS pace_delta_s
FROM ranked
WHERE rn=1
ORDER BY pace_delta_s DESC
""")

def build_executive():
    panels = [
        text("RACEPULSE // CEO COMMAND CENTER",
             "**LIVE RACE INTELLIGENCE**  \nStreaming telemetry | strategy | race control | commercial intelligence  \n`SENSE -> STREAM -> ANALYZE -> ALERT -> DECIDE`",
             0, 0, 24, 4),
        stat("Current Lap", LATEST_LAP, 0, 4, TELEMETRY),
        stat("Critical Alerts", CRITICAL_ALERTS, 4, 4, CRITICAL),
        stat("Strategy Signals", STRATEGY_SIGNALS, 8, 4, STRATEGY),
        stat("Commercial Events", COMMERCIAL_EVENTS, 12, 4, COMMERCIAL),
        stat("Cars Reporting", CARS_REPORTING, 16, 4, NORMAL),
        stat("Windowed KPIs", WINDOWED_KPIS, 20, 4, TELEMETRY),
        ts("Race Pace // Pace Delta", PACE, 0, 8, 12, 9, "suffix:s", 2),
        ts("Race Pace // Gap Trend", GAP, 12, 8, 12, 9, "suffix:s", 2),
        ts("Strategic Exposure // Tyre Risk", STRATEGY_RISK, 0, 17, 12, 8, "short", 2),
        ts("Commercial Momentum // Engagement", COMM_ENGAGEMENT, 12, 17, 12, 8, "percent", 2),
        table("12-Car Executive Status", CURRENT_CAR_STATUS, 0, 25, 24, 9),
        table("Executive Alert Feed", ALERT_FEED, 0, 34, 12, 8),
        table("Strategy Decision Feed", STRATEGY_FEED, 12, 34, 12, 8),
    ]
    return dashboard("racepulse-ceo-command-center", "RACEPULSE // CEO Command Center",
                      "Executive command center for live race, strategy, commercial and risk intelligence.", panels)


def build_operations():
    panels = [
        text("RACE OPERATIONS // LIVE PERFORMANCE",
             "**RACE ENGINEERING WORKSTATION**  \nPerformance | pace | gap | speed | race-control signals",
             0, 0, 24, 4),
        stat("Current Lap", LATEST_LAP, 0, 4, TELEMETRY),
        stat("Active Cars", CARS_REPORTING, 4, 4, NORMAL),
        stat("Critical Alerts", CRITICAL_ALERTS, 8, 4, CRITICAL),
        stat("Track Risk Signals", TRACK_RISK_SIGNALS, 12, 4, WARNING),
        stat("Vehicle Risk Signals", VEHICLE_RISK_SIGNALS, 16, 4, WARNING),
        stat("Max Gap Trend", q(f"""{RACE} SELECT COALESCE(ROUND(MAX(ABS(g.trend_ms_per_lap))/1000.0,2),0) AS value FROM gap_trend_results g CROSS JOIN race WHERE g.event_time BETWEEN race.race_start AND race.race_end AND g.lap_number BETWEEN 1 AND 60"""), 20, 4, TELEMETRY, "suffix:s"),
        ts("Live Pace Delta", PACE, 0, 8, 12, 8, "suffix:s", 2),
        ts("Gap Trend", GAP, 12, 8, 12, 8, "suffix:s", 2),
        ts("Lap Time Evolution", LAP_TIME, 0, 16, 12, 8, "suffix:s", 2),
        ts("Average Vehicle Speed // 15s", SPEED, 12, 16, 12, 8, "kmh", 1),
        table("12-Car Performance Matrix", CURRENT_CAR_STATUS, 0, 24, 24, 9),
        table("Performance Alert Feed", PERFORMANCE_ALERTS, 0, 33, 12, 8),
        table("Race Control Alert Feed", RACE_CONTROL_FEED, 12, 33, 12, 8),
    ]
    return dashboard("racepulse-race-operations", "RACEPULSE // Race Operations",
                      "Live performance workstation for race engineering.", panels)


def build_strategy():
    panels = [
        text("STRATEGY INTELLIGENCE",
             "**STRATEGIST WORKSTATION**  \nTyre degradation | pit-window signals | strategic exposure",
             0, 0, 24, 4),
        stat("Critical Signals", STRATEGY_CRITICAL, 0, 4, CRITICAL),
        stat("Warning Signals", STRATEGY_WARNING, 4, 4, WARNING),
        stat("Pit-Window Signals", PIT_SIGNALS, 8, 4, STRATEGY),
        stat("Highest Tyre Risk", MAX_TYRE_RISK, 12, 4, CRITICAL),
        stat("Cars Reporting", CARS_REPORTING, 16, 4, NORMAL),
        stat("Current Lap", LATEST_LAP, 20, 4, TELEMETRY),
        ts("Tyre Degradation Risk", STRATEGY_RISK, 0, 8, 12, 8, "short", 2),
        ts("Pit-Window Signal", PIT_WINDOW, 12, 8, 12, 8, "short", 2),
        table("12-Car Strategy Matrix", STRATEGY_MATRIX, 0, 16, 24, 9),
        table("Strategy Decision Feed", STRATEGY_FEED, 0, 25, 12, 9),
        bar("Current Pace Delta // 12-Car Ranking", CURRENT_PACE_RANKING, 0, 42, 12, 8, "suffix:s", 2),
        table("Current Race Performance Context", CURRENT_CAR_STATUS, 12, 25, 12, 9),
    ]
    return dashboard("racepulse-strategy", "RACEPULSE // Strategy Intelligence",
                      "Strategy workstation for tyre risk and pit-window intelligence.", panels)


def build_control():
    panels = [
        text("RACE CONTROL // SAFETY & INCIDENTS",
             "**CONTROL ROOM**  \nTrack risk | vehicle risk | operational alerts",
             0, 0, 24, 4),
        stat("Critical Control Signals", RC_CRITICAL, 0, 4, CRITICAL),
        stat("Track Risk Signals", TRACK_RISK_SIGNALS, 4, 4, WARNING),
        stat("Vehicle Risk Signals", VEHICLE_RISK_SIGNALS, 8, 4, WARNING),
        stat("Active Cars", CARS_REPORTING, 12, 4, NORMAL),
        stat("Current Lap", LATEST_LAP, 16, 4, TELEMETRY),
        stat("Critical Platform Alerts", CRITICAL_ALERTS, 20, 4, CRITICAL),
        ts("Track Risk Timeline", RC_TRACK, 0, 8, 12, 8, "short", 2),
        ts("Vehicle Risk Timeline", RC_VEHICLE, 12, 8, 12, 8, "short", 2),
        table("12-Car Safety Matrix", RACE_CONTROL_MATRIX, 0, 16, 24, 9),
        table("Race Control Alert Feed", RACE_CONTROL_FEED, 0, 25, 12, 9),
        table("Executive Alert Context", ALERT_FEED, 12, 25, 12, 9),
    ]
    return dashboard("racepulse-race-control", "RACEPULSE // Race Control",
                      "Race-control and safety intelligence workstation.", panels)


def build_commercial():
    panels = [
        text("COMMERCIAL INTELLIGENCE",
             "**SPORTS BUSINESS WORKSTATION**  \nFan engagement | sponsor visibility | conversion | commercial momentum",
             0, 0, 24, 4),
        stat("Avg Engagement", COMM_ENGAGEMENT_AVG, 0, 4, COMMERCIAL, "percent"),
        stat("Sponsor Visibility", COMM_VISIBILITY, 4, 4, COMMERCIAL, "suffix:s"),
        stat("Avg Conversion", COMM_CONVERSION_AVG, 8, 4, COMMERCIAL, "percent"),
        stat("Commercial Events", COMMERCIAL_EVENTS, 12, 4, COMMERCIAL),
        stat("Active Cars", CARS_REPORTING, 16, 4, NORMAL),
        stat("Current Lap", LATEST_LAP, 20, 4, TELEMETRY),
        ts("Fan Engagement Trend", COMM_ENGAGEMENT, 0, 8, 12, 8, "percent", 2),
        ts("Sponsor Visibility", SPONSOR_VISIBILITY, 12, 8, 12, 8, "suffix:s", 1),
        ts("Sponsor Conversion", COMM_CONVERSION, 0, 16, 12, 8, "percent", 2),
        ts("Average Speed // Commercial Context", SPEED, 12, 16, 12, 8, "kmh", 1),
        table("Sponsor Scorecard", COMMERCIAL_SCORECARD, 0, 24, 24, 8),
        table("Commercial Activity Feed", COMMERCIAL_FEED, 0, 32, 12, 9),
        table("Commercial Signal Context", COMMERCIAL_FEED, 12, 32, 12, 9),
    ]
    return dashboard("racepulse-commercial", "RACEPULSE // Commercial Intelligence",
                      "Commercial intelligence for fan and sponsor performance.", panels)


def build_engineering():
    panels = [
        text("STREAMING ENGINEERING // MISSION CONTROL",
             "**PLATFORM HEALTH**  \nKafka | consumers | validation | DLQ | stale-stream monitoring",
             0, 0, 24, 4),
        stat("Max Consumer Lag", STREAM_LAG_MAX, 0, 4, NORMAL),
        stat("DLQ Events", DLQ_COUNT, 4, 4, CRITICAL),
        stat("Stale Stream Alerts", STALE_COUNT, 8, 4, WARNING),
        stat("Critical Infra Alerts", INFRA_CRITICAL, 12, 4, CRITICAL),
        stat("Active Cars", CARS_REPORTING, 16, 4, NORMAL),
        stat("Current Lap", LATEST_LAP, 20, 4, TELEMETRY),
        ts("Consumer Lag", LAG_TIMELINE, 0, 8, 12, 8, "short", 0),
        ts("DLQ Activity", DLQ_TIMELINE, 12, 8, 12, 8, "short", 0),
        table("Consumer Health Matrix", HEALTH_MATRIX, 0, 16, 24, 8),
        table("Infrastructure Alert Feed", INFRA_FEED, 0, 24, 12, 9),
        table("Data Quality / DLQ Feed", DATA_QUALITY, 12, 24, 12, 9),
    ]
    return dashboard("racepulse-streaming-engineering", "RACEPULSE // Streaming Engineering",
                      "Streaming platform health, lag, validation and data-quality control room.", panels)


DASHBOARDS = [
    build_executive,
    build_operations,
    build_strategy,
    build_control,
    build_commercial,
    build_engineering,
]


def build_all() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for builder in DASHBOARDS:
        d = builder()
        path = OUT / f"{d['uid']}.json"
        path.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        written.append(path)
        print(f"[OK] {d['title']}: {len(d['panels'])} panels")
        json.loads(path.read_text(encoding="utf-8"))
    return written


if __name__ == "__main__":
    print("=" * 70)
    print("RACEPULSE PRODUCTION DASHBOARD BUILDER")
    print("=" * 70)
    build_all()
    print("=" * 70)
    print("All production dashboards generated.")
    print("=" * 70)


