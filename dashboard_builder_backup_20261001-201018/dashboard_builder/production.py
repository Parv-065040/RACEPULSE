
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
        "templating": {"list": []},
        "time": {"from": "now-30m", "to": "now"},
        "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
        "timezone": "browser",
        "title": title,
        "uid": uid,
        "version": 1,
        "description": description,
    }


def q(sql: str) -> str:
    return sql


LATEST_LAP = q(f"""
SELECT COALESCE(MAX(lap_number),0) AS value
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
""")

CRITICAL_ALERTS = q("""
SELECT COUNT(*) AS value
FROM alerts
WHERE severity='critical'
  AND $__timeFilter(created_at)
""")

STRATEGY_SIGNALS = q("""
SELECT COUNT(*) AS value
FROM strategy_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
""")

COMMERCIAL_EVENTS = q("""
SELECT COUNT(*) AS value
FROM commercial_results
WHERE $__timeFilter(event_time)
""")

CARS_REPORTING = q(f"""
SELECT COUNT(DISTINCT car_id) AS value
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
""")

WINDOWED_KPIS = q(f"""
SELECT COUNT(*) AS value
FROM windowed_kpi_results
WHERE $__timeFilter(window_start)
  AND car_id REGEXP '{CAR_RE}'
""")

PACE = q(f"""
SELECT event_time AS time, car_id,
       ROUND(delta_ms/1000.0,3) AS pace_delta_s
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY event_time
""")

GAP = q(f"""
SELECT event_time AS time, car_id,
       ROUND(trend_ms_per_lap/1000.0,3) AS gap_trend_s_per_lap
FROM gap_trend_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY event_time
""")

SPEED = q(f"""
SELECT window_start AS time, car_id,
       ROUND(value,1) AS avg_speed_kmh
FROM windowed_kpi_results
WHERE kpi_id='KPI-003'
  AND $__timeFilter(window_start)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY window_start
""")

STRATEGY_RISK = q(f"""
SELECT event_time AS time, car_id,
       ROUND(value,3) AS strategy_risk
FROM strategy_results
WHERE kpi_id='STR-001'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY event_time
""")

PIT_WINDOW = q(f"""
SELECT event_time AS time, car_id,
       ROUND(value,3) AS pit_window_signal
FROM strategy_results
WHERE kpi_id='STR-002'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY event_time
""")

COMM_ENGAGEMENT = q("""
SELECT event_time AS time, car_id,
       ROUND(value*100,2) AS engagement_pct
FROM commercial_results
WHERE kpi_id='COM-001'
  AND $__timeFilter(event_time)
ORDER BY event_time
""")

SPONSOR_VISIBILITY = q("""
SELECT event_time AS time, entity_id AS sponsor_id,
       ROUND(value,1) AS visibility_s
FROM commercial_results
WHERE kpi_id='COM-002'
  AND $__timeFilter(event_time)
ORDER BY event_time
""")

COMM_CONVERSION = q("""
SELECT event_time AS time, entity_id AS sponsor_id,
       ROUND(value*100,2) AS conversion_pct
FROM commercial_results
WHERE kpi_id='COM-003'
  AND $__timeFilter(event_time)
ORDER BY event_time
""")

CURRENT_CAR_STATUS = q(f"""
SELECT
    kr.car_id AS car,
    kr.lap_number AS lap,
    ROUND(kr.lap_time_ms/1000.0,3) AS lap_time_s,
    ROUND(kr.best_lap_time_ms/1000.0,3) AS best_lap_s,
    ROUND(kr.delta_ms/1000.0,3) AS pace_delta_s,
    kr.severity AS pace_status,
    ROUND(COALESCE(gt.gap_to_leader_ms,0)/1000.0,3) AS gap_s,
    ROUND(COALESCE(gt.trend_ms_per_lap,0)/1000.0,3) AS gap_trend_s_per_lap,
    COALESCE(gt.severity,'none') AS gap_status
FROM kpi_results kr
INNER JOIN (
    SELECT car_id, MAX(id) AS latest_id
    FROM kpi_results
    WHERE $__timeFilter(event_time)
      AND car_id REGEXP '{CAR_RE}'
    GROUP BY car_id
) latest
  ON latest.car_id=kr.car_id AND latest.latest_id=kr.id
LEFT JOIN gap_trend_results gt
  ON gt.car_id=kr.car_id AND gt.lap_number=kr.lap_number
 AND gt.id=(
    SELECT MAX(g2.id)
    FROM gap_trend_results g2
    WHERE g2.car_id=kr.car_id
      AND g2.lap_number=kr.lap_number
      AND $__timeFilter(g2.event_time)
 )
ORDER BY kr.car_id
""")

STRATEGY_MATRIX = q(f"""
SELECT
    car_id AS car,
    MAX(CASE WHEN kpi_id='STR-001' THEN ROUND(value,2) END) AS tyre_risk,
    MAX(CASE WHEN kpi_id='STR-002' THEN ROUND(value,2) END) AS pit_signal,
    MAX(CASE WHEN kpi_id='STR-001' THEN severity END) AS tyre_status,
    MAX(CASE WHEN kpi_id='STR-002' THEN severity END) AS pit_status,
    MAX(lap_number) AS lap
FROM strategy_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
GROUP BY car_id
ORDER BY car_id
""")

STRATEGY_FEED = q("""
SELECT event_time AS time,
       car_id AS car,
       CASE kpi_id
         WHEN 'STR-001' THEN 'TYRE DEGRADATION RISK'
         WHEN 'STR-002' THEN 'PIT WINDOW SIGNAL'
         ELSE kpi_id
       END AS signal,
       ROUND(value,2) AS value,
       severity AS status,
       message
FROM strategy_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
ORDER BY event_time DESC
LIMIT 20
""")

RACE_CONTROL_MATRIX = q(f"""
SELECT
    car_id AS car,
    MAX(CASE WHEN kpi_id='RC-001' THEN ROUND(value,2) END) AS track_risk,
    MAX(CASE WHEN kpi_id='RC-002' THEN ROUND(value,2) END) AS vehicle_risk,
    MAX(CASE WHEN kpi_id='RC-001' THEN severity END) AS track_status,
    MAX(CASE WHEN kpi_id='RC-002' THEN severity END) AS vehicle_status,
    MAX(lap_number) AS lap
FROM race_control_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
GROUP BY car_id
ORDER BY car_id
""")

RACE_CONTROL_FEED = q("""
SELECT event_time AS time,
       car_id AS car,
       CASE kpi_id
         WHEN 'RC-001' THEN 'TRACK RISK'
         WHEN 'RC-002' THEN 'VEHICLE RISK'
         ELSE kpi_id
       END AS signal,
       ROUND(value,2) AS value,
       severity AS status,
       message
FROM race_control_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
ORDER BY event_time DESC
LIMIT 20
""")

COMMERCIAL_SCORECARD = q("""
SELECT
    entity_id AS sponsor,
    ROUND(SUM(CASE WHEN kpi_id='COM-002' THEN value ELSE 0 END),1) AS visibility_s,
    ROUND(AVG(CASE WHEN kpi_id='COM-003' THEN value END)*100,2) AS conversion_pct,
    COUNT(CASE WHEN kpi_id='COM-001' THEN 1 END) AS engagement_events,
    MAX(lap_number) AS latest_lap
FROM commercial_results
WHERE $__timeFilter(event_time)
GROUP BY entity_id
ORDER BY visibility_s DESC
LIMIT 12
""")

COMMERCIAL_FEED = q("""
SELECT event_time AS time,
       entity_id AS sponsor,
       CASE kpi_id
         WHEN 'COM-001' THEN 'FAN ENGAGEMENT'
         WHEN 'COM-002' THEN 'SPONSOR VISIBILITY'
         WHEN 'COM-003' THEN 'SPONSOR CONVERSION'
         ELSE kpi_id
       END AS metric,
       ROUND(value,3) AS value,
       unit
FROM commercial_results
WHERE $__timeFilter(event_time)
ORDER BY event_time DESC
LIMIT 20
""")

ALERT_FEED = q("""
SELECT created_at AS time,
       car_id AS car,
       kpi_id AS signal,
       severity AS status,
       message
FROM alerts
WHERE $__timeFilter(created_at)
ORDER BY created_at DESC
LIMIT 20
""")

PERFORMANCE_ALERTS = q("""
SELECT event_time AS time,
       car_id AS car,
       kpi_id AS signal,
       ROUND(delta_ms/1000.0,2) AS pace_delta_s,
       severity AS status
FROM kpi_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
ORDER BY event_time DESC
LIMIT 20
""")

LAP_TIME = q(f"""
SELECT event_time AS time, car_id,
       ROUND(lap_time_ms/1000.0,3) AS lap_time_s
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '{CAR_RE}'
ORDER BY event_time
""")

STRATEGY_CRITICAL = q("""
SELECT COUNT(*) AS value
FROM strategy_results
WHERE severity='critical' AND $__timeFilter(event_time)
""")

STRATEGY_WARNING = q("""
SELECT COUNT(*) AS value
FROM strategy_results
WHERE severity='warning' AND $__timeFilter(event_time)
""")

PIT_SIGNALS = q("""
SELECT COUNT(*) AS value
FROM strategy_results
WHERE kpi_id='STR-002' AND value>=0.6 AND $__timeFilter(event_time)
""")

MAX_TYRE_RISK = q("""
SELECT COALESCE(ROUND(MAX(value),2),0) AS value
FROM strategy_results
WHERE kpi_id='STR-001' AND $__timeFilter(event_time)
""")

TRACK_RISK_SIGNALS = q("""
SELECT COUNT(*) AS value
FROM race_control_results
WHERE kpi_id='RC-001' AND severity<>'none' AND $__timeFilter(event_time)
""")

VEHICLE_RISK_SIGNALS = q("""
SELECT COUNT(*) AS value
FROM race_control_results
WHERE kpi_id='RC-002' AND severity<>'none' AND $__timeFilter(event_time)
""")

RC_TRACK = q("""
SELECT event_time AS time, car_id,
       ROUND(value,3) AS track_risk
FROM race_control_results
WHERE kpi_id='RC-001' AND $__timeFilter(event_time)
ORDER BY event_time
""")

RC_VEHICLE = q("""
SELECT event_time AS time, car_id,
       ROUND(value,3) AS vehicle_risk
FROM race_control_results
WHERE kpi_id='RC-002' AND $__timeFilter(event_time)
ORDER BY event_time
""")

RC_CRITICAL = q("""
SELECT COUNT(*) AS value
FROM race_control_results
WHERE severity='critical' AND $__timeFilter(event_time)
""")

COMM_ENGAGEMENT_AVG = q("""
SELECT COALESCE(ROUND(AVG(value)*100,2),0) AS value
FROM commercial_results
WHERE kpi_id='COM-001' AND $__timeFilter(event_time)
""")

COMM_VISIBILITY = q("""
SELECT COALESCE(ROUND(SUM(value),1),0) AS value
FROM commercial_results
WHERE kpi_id='COM-002' AND $__timeFilter(event_time)
""")

COMM_CONVERSION_AVG = q("""
SELECT COALESCE(ROUND(AVG(value)*100,2),0) AS value
FROM commercial_results
WHERE kpi_id='COM-003' AND $__timeFilter(event_time)
""")

DLQ_COUNT = q("""
SELECT COUNT(*) AS value
FROM dlq_events
WHERE $__timeFilter(failed_at)
""")

STALE_COUNT = q("""
SELECT COUNT(*) AS value
FROM infra_alerts
WHERE (signal='STALE_STREAM' OR signal='SYS-STALE')
  AND $__timeFilter(observed_at)
""")

INFRA_CRITICAL = q("""
SELECT COUNT(*) AS value
FROM infra_alerts
WHERE severity='critical' AND $__timeFilter(observed_at)
""")

STREAM_LAG_MAX = q("""
SELECT COALESCE(MAX(lag),0) AS value
FROM stream_health
WHERE $__timeFilter(observed_at)
""")

DLQ_TIMELINE = q("""
SELECT failed_at AS time, source_topic, COUNT(*) AS dlq_events
FROM dlq_events
WHERE $__timeFilter(failed_at)
GROUP BY failed_at, source_topic
ORDER BY failed_at
""")

LAG_TIMELINE = q("""
SELECT observed_at AS time, consumer_group, MAX(lag) AS lag
FROM stream_health
WHERE $__timeFilter(observed_at)
GROUP BY observed_at, consumer_group
ORDER BY observed_at
""")

HEALTH_MATRIX = q("""
SELECT
    consumer_group AS consumer,
    MAX(lag) AS lag,
    MAX(events_seen) AS events_seen,
    SUBSTRING_INDEX(GROUP_CONCAT(status ORDER BY observed_at DESC), ',', 1) AS status,
    MAX(last_event_at) AS last_event
FROM stream_health
WHERE $__timeFilter(observed_at)
GROUP BY consumer_group
ORDER BY consumer_group
""")

INFRA_FEED = q("""
SELECT observed_at AS time,
       signal,
       severity AS status,
       component,
       message
FROM infra_alerts
WHERE $__timeFilter(observed_at)
ORDER BY observed_at DESC
LIMIT 30
""")

DATA_QUALITY = q("""
SELECT failed_at AS time,
       source_topic AS topic,
       raw_key,
       errors
FROM dlq_events
WHERE $__timeFilter(failed_at)
ORDER BY failed_at DESC
LIMIT 30
""")


def build_executive():
    panels = [
        text("RACEPULSE // CEO COMMAND CENTER",
             "**LIVE RACE INTELLIGENCE**  \nStreaming telemetry â€¢ strategy â€¢ race control â€¢ commercial intelligence  \n`SENSE â†’ STREAM â†’ ANALYZE â†’ ALERT â†’ DECIDE`",
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
             "**RACE ENGINEERING WORKSTATION**  \nPerformance â€¢ pace â€¢ gap â€¢ speed â€¢ race-control signals",
             0, 0, 24, 4),
        stat("Current Lap", LATEST_LAP, 0, 4, TELEMETRY),
        stat("Active Cars", CARS_REPORTING, 4, 4, NORMAL),
        stat("Critical Alerts", CRITICAL_ALERTS, 8, 4, CRITICAL),
        stat("Track Risk Signals", TRACK_RISK_SIGNALS, 12, 4, WARNING),
        stat("Vehicle Risk Signals", VEHICLE_RISK_SIGNALS, 16, 4, WARNING),
        stat("Max Gap Trend", q("SELECT COALESCE(ROUND(MAX(ABS(trend_ms_per_lap))/1000.0,2),0) AS value FROM gap_trend_results WHERE $__timeFilter(event_time)"), 20, 4, TELEMETRY, "suffix:s"),
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
             "**STRATEGIST WORKSTATION**  \nTyre degradation â€¢ pit-window signals â€¢ strategic exposure",
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
        table("Current Race Performance Context", CURRENT_CAR_STATUS, 12, 25, 12, 9),
    ]
    return dashboard("racepulse-strategy", "RACEPULSE // Strategy Intelligence",
                      "Strategy workstation for tyre risk and pit-window intelligence.", panels)


def build_control():
    panels = [
        text("RACE CONTROL // SAFETY & INCIDENTS",
             "**CONTROL ROOM**  \nTrack risk â€¢ vehicle risk â€¢ operational alerts",
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
             "**SPORTS BUSINESS WORKSTATION**  \nFan engagement â€¢ sponsor visibility â€¢ conversion â€¢ commercial momentum",
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
        table("Commercial Opportunity Context", STRATEGY_FEED, 12, 32, 12, 9),
    ]
    return dashboard("racepulse-commercial", "RACEPULSE // Commercial Intelligence",
                      "Commercial intelligence for fan and sponsor performance.", panels)


def build_engineering():
    panels = [
        text("STREAMING ENGINEERING // MISSION CONTROL",
             "**PLATFORM HEALTH**  \nKafka â€¢ consumers â€¢ validation â€¢ DLQ â€¢ stale-stream monitoring",
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

