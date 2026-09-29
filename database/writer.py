"""
MySQL writer functions - Parv's ownership (database/writer.py).
Idempotent writes for both KPI-001 (Lap Pace Delta) and KPI-002
(Gap Trend): each relies on a UNIQUE KEY (event_id, kpi_id) so a
replayed/duplicate event overwrites the same row instead of creating
a second one.
"""
from datetime import datetime
from database.connection import get_connection

_INSERT_KPI_RESULT = """
INSERT INTO kpi_results
    (kpi_id, event_id, car_id, lap_number, lap_time_ms, best_lap_time_ms, delta_ms, severity, event_time)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    lap_time_ms = VALUES(lap_time_ms),
    best_lap_time_ms = VALUES(best_lap_time_ms),
    delta_ms = VALUES(delta_ms),
    severity = VALUES(severity),
    event_time = VALUES(event_time)
"""

_INSERT_GAP_TREND_RESULT = """
INSERT INTO gap_trend_results
    (kpi_id, event_id, car_id, lap_number, gap_to_leader_ms, trend_ms_per_lap, severity, event_time)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    gap_to_leader_ms = VALUES(gap_to_leader_ms),
    trend_ms_per_lap = VALUES(trend_ms_per_lap),
    severity = VALUES(severity),
    event_time = VALUES(event_time)
"""

_connection = None

def _get_conn():
    global _connection
    if _connection is None or not _connection.open:
        _connection = get_connection()
    return _connection

def write_kpi_result(kpi: dict, event: dict) -> None:
    event_time = datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(_INSERT_KPI_RESULT, (
            kpi["kpi_id"],
            event["event_id"],
            kpi["car_id"],
            event["lap_number"],
            kpi["lap_time_ms"],
            kpi["best_lap_time_ms"],
            kpi["delta_ms"],
            kpi["severity"],
            event_time,
        ))

def write_gap_trend_result(kpi: dict, event: dict) -> None:
    event_time = datetime.fromisoformat(event["event_time"]).replace(tzinfo=None)
    conn = _get_conn()
    with conn.cursor() as cursor:
        cursor.execute(_INSERT_GAP_TREND_RESULT, (
            kpi["kpi_id"],
            event["event_id"],
            kpi["car_id"],
            event["lap_number"],
            kpi["gap_to_leader_ms"],
            kpi["trend_ms_per_lap"],
            kpi["severity"],
            event_time,
        ))