"""Centralized SQL query library for RACEPULSE dashboards."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Executive / stat queries
# ---------------------------------------------------------------------------

LATEST_LAP = """
SELECT COALESCE(MAX(lap_number), 0) AS value
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
"""


CRITICAL_ALERTS = """
SELECT COUNT(*) AS value
FROM alerts
WHERE severity = 'critical'
  AND created_at >= NOW() - INTERVAL 30 MINUTE
"""


STRATEGY_SIGNALS = """
SELECT COUNT(*) AS value
FROM strategy_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
"""


COMMERCIAL_EVENTS = """
SELECT COUNT(*) AS value
FROM commercial_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
"""


# ---------------------------------------------------------------------------
# Race intelligence
# ---------------------------------------------------------------------------

CURRENT_RACE_SIGNALS = """
SELECT
    car_id,
    MAX(lap_number) AS latest_lap,
    ROUND(MAX(delta_ms), 0) AS pace_delta_ms
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
GROUP BY car_id
ORDER BY latest_lap DESC
"""


LATEST_ALERTS = """
SELECT
    created_at AS time,
    car_id,
    kpi_id,
    severity,
    message
FROM alerts
WHERE created_at >= NOW() - INTERVAL 30 MINUTE
ORDER BY created_at DESC
LIMIT 20
"""


PACE_TIMELINE = """
SELECT
    event_time AS time,
    car_id,
    ROUND(delta_ms / 1000.0, 3) AS pace_delta_s
FROM kpi_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


GAP_TIMELINE = """
SELECT
    event_time AS time,
    car_id,
    ROUND(trend_ms_per_lap / 1000.0, 3) AS gap_trend_s_per_lap
FROM gap_trend_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


SPEED_TIMELINE = """
SELECT
    window_start AS time,
    car_id,
    value AS avg_speed_kmh
FROM windowed_kpi_results
WHERE kpi_id = 'KPI-003'
  AND $__timeFilter(window_start)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY window_start
"""


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

STRATEGY_RISK = """
SELECT
    event_time AS time,
    car_id,
    value AS strategy_risk
FROM strategy_results
WHERE kpi_id = 'STR-001'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


PIT_WINDOW = """
SELECT
    event_time AS time,
    car_id,
    value AS pit_window_signal
FROM strategy_results
WHERE kpi_id = 'STR-002'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


# ---------------------------------------------------------------------------
# Commercial
# ---------------------------------------------------------------------------

COMMERCIAL_ACTIVITY = """
SELECT
    event_time AS time,
    kpi_id,
    car_id,
    value
FROM commercial_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


RACE_CONTROL_RISK = """
SELECT
    event_time AS time,
    car_id,
    kpi_id,
    value,
    severity
FROM race_control_results
WHERE $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


# ---------------------------------------------------------------------------
# Current 12-car grid
# ---------------------------------------------------------------------------

CURRENT_CAR_STATUS = """
SELECT
    kr.car_id AS car,
    kr.lap_number AS latest_lap,
    kr.lap_time_ms,
    kr.best_lap_time_ms AS best_lap_ms,
    kr.delta_ms AS pace_delta_ms,
    kr.severity AS pace_status,
    gt.gap_to_leader_ms,
    gt.trend_ms_per_lap AS gap_trend_ms_per_lap,
    gt.severity AS gap_status
FROM kpi_results kr
INNER JOIN (
    SELECT
        car_id,
        MAX(id) AS latest_id
    FROM kpi_results
    WHERE $__timeFilter(event_time)
      AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
    GROUP BY car_id
) latest
    ON latest.car_id = kr.car_id
   AND latest.latest_id = kr.id
LEFT JOIN (
    SELECT
        g.car_id,
        g.gap_to_leader_ms,
        g.trend_ms_per_lap,
        g.severity,
        g.lap_number
    FROM gap_trend_results g
    INNER JOIN (
        SELECT
            car_id,
            MAX(id) AS latest_id
        FROM gap_trend_results
        WHERE $__timeFilter(event_time)
          AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
        GROUP BY car_id
    ) latest_gap
        ON latest_gap.car_id = g.car_id
       AND latest_gap.latest_id = g.id
) gt
    ON gt.car_id = kr.car_id
ORDER BY kr.car_id
"""


# ---------------------------------------------------------------------------
# Race Control / Strategy alerts
# ---------------------------------------------------------------------------

RECENT_RACE_CONTROL_ALERTS = """
SELECT
    created_at AS time,
    car_id,
    kpi_id,
    severity,
    message,
    value
FROM race_control_results
WHERE severity <> 'none'
  AND $__timeFilter(created_at)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY created_at DESC
LIMIT 20
"""


RECENT_STRATEGY_SIGNALS = """
SELECT
    event_time AS time,
    car_id,
    kpi_id,
    ROUND(value, 3) AS value,
    severity,
    message
FROM strategy_results
WHERE severity <> 'none'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time DESC
LIMIT 20
"""


# ---------------------------------------------------------------------------
# Commercial intelligence
# ---------------------------------------------------------------------------

COMMERCIAL_ENGAGEMENT = """
SELECT
    event_time AS time,
    car_id,
    value * 100 AS engagement_percent
FROM commercial_results
WHERE kpi_id = 'COM-001'
  AND $__timeFilter(event_time)
  AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
ORDER BY event_time
"""


SPONSOR_VISIBILITY = """
SELECT
    event_time AS time,
    entity_id AS sponsor_id,
    value AS visibility_seconds
FROM commercial_results
WHERE kpi_id = 'COM-002'
  AND $__timeFilter(event_time)
ORDER BY event_time
"""


# ---------------------------------------------------------------------------
# Streaming engineering
# ---------------------------------------------------------------------------

DLQ_ACTIVITY = """
SELECT
    failed_at AS time,
    source_topic,
    raw_key,
    errors
FROM dlq_events
WHERE failed_at >= NOW() - INTERVAL 30 MINUTE
ORDER BY failed_at DESC
LIMIT 50
"""


STREAM_HEALTH = """
SELECT
    observed_at AS time,
    consumer_group,
    lag,
    status,
    message
FROM stream_health
WHERE observed_at >= NOW() - INTERVAL 30 MINUTE
ORDER BY observed_at DESC
LIMIT 100
"""


INFRA_ALERTS = """
SELECT
    observed_at AS time,
    signal,
    severity,
    component,
    message
FROM infra_alerts
WHERE observed_at >= NOW() - INTERVAL 30 MINUTE
ORDER BY observed_at DESC
LIMIT 50
"""
