from pathlib import Path

TARGET = Path(r'.\tools\dashboard_builder\production.py')
BACKUP = Path(r'.\tools\dashboard_builder\production_before_consolidated_patch.py')

if not TARGET.exists():
    raise SystemExit('ERROR: production.py was not found.')
if not BACKUP.exists():
    raise SystemExit('ERROR: pre-patch backup was not found.')
if TARGET.read_bytes() != BACKUP.read_bytes():
    raise SystemExit('ABORTED: production.py differs from the pre-patch backup. No changes made.')

text = TARGET.read_text(encoding='utf-8')

def block(name, body):
    global text
    marker = name + ' = q('
    start = text.find(marker)
    if start < 0:
        raise SystemExit('ABORTED: block not found: ' + name)
    end = text.find('\"\"\")', start)
    if end < 0:
        raise SystemExit('ABORTED: block end not found: ' + name)
    end += 5
    replacement = '\n'.join(body) + '\n'
    text = text[:start] + replacement + text[end:]

block('RACE_CONTROL_FEED', [
    'RACE_CONTROL_FEED = q(f\"\"\"',
    'SELECT rc.event_time AS time,',
    '       rc.car_id AS car,',
    '       CASE rc.kpi_id',
    "           WHEN 'RC-001' THEN 'TRACK RISK'",
    "           WHEN 'RC-002' THEN 'VEHICLE RISK'",
    '           ELSE rc.kpi_id',
    '       END AS signal,',
    '       ROUND(rc.value,2) AS value,',
    '       rc.severity AS status,',
    '       rc.message',
    'FROM race_control_results rc',
    "WHERE rc.severity <> 'none'",
    "  AND rc.car_id REGEXP '{CAR_RE}'",
    "  AND rc.car_id REGEXP '${{car:regex}}'",
    "  AND rc.severity REGEXP '${{severity:regex}}'",
    '  AND rc.lap_number BETWEEN 1 AND 60',
    '  AND rc.event_time >= DATE_SUB(',
    '      (SELECT MAX(event_time)',
    '       FROM race_control_results',
    '       WHERE lap_number BETWEEN 1 AND 60',
    "         AND car_id REGEXP '{CAR_RE}'),",
    '      INTERVAL 10 MINUTE',
    '  )',
    'ORDER BY rc.event_time DESC',
    'LIMIT 20',
    '\"\"\")',
])

block('COMMERCIAL_SCORECARD', [
    'COMMERCIAL_SCORECARD = q(f\"\"\"',
    '{RACE}',
    'SELECT c.entity_id AS sponsor,',
    "       ROUND(SUM(CASE WHEN c.kpi_id='COM-002' THEN c.value ELSE 0 END),1) AS visibility_s,",
    "       ROUND(AVG(CASE WHEN c.kpi_id='COM-003' THEN c.value END)*100,2) AS conversion_pct,",
    "       COUNT(CASE WHEN c.kpi_id='COM-002' THEN 1 END) AS visibility_events,",
    '       MAX(c.lap_number) AS latest_lap',
    'FROM commercial_results c CROSS JOIN race',
    'WHERE c.event_time BETWEEN race.race_start AND race.race_end',
    '  AND c.lap_number BETWEEN 1 AND 60',
    "  AND c.kpi_id IN ('COM-002','COM-003')",
    "  AND c.entity_id REGEXP '^SPONSOR_[0-9]+$'",
    'GROUP BY c.entity_id',
    'ORDER BY visibility_s DESC',
    'LIMIT 12',
    '\"\"\")',
])

block('ALERT_FEED', [
    'ALERT_FEED = q(f\"\"\"',
    'SELECT a.created_at AS time,',
    '       a.car_id AS car,',
    '       a.kpi_id AS signal,',
    '       a.severity AS status,',
    '       a.message',
    'FROM alerts a',
    'WHERE a.created_at >= DATE_SUB(',
    '    (SELECT MAX(created_at) FROM alerts),',
    '    INTERVAL 10 MINUTE',
    ')',
    "  AND a.car_id REGEXP '${{car:regex}}'",
    "  AND a.severity REGEXP '${{severity:regex}}'",
    'ORDER BY a.created_at DESC',
    'LIMIT 20',
    '\"\"\")',
])

block('PERFORMANCE_ALERTS', [
    'PERFORMANCE_ALERTS = q(f\"\"\"',
    '{RACE}',
    ',scoped AS (',
    '    SELECT k.*,',
    '           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS current_best_lap_ms',
    '    FROM kpi_results k CROSS JOIN race',
    '    WHERE k.event_time BETWEEN race.race_start AND race.race_end',
    '      AND k.lap_number BETWEEN 1 AND 60',
    "      AND k.car_id REGEXP '{CAR_RE}'",
    "      AND k.car_id REGEXP '${{car:regex}}'",
    '),',
    'alert_rows AS (',
    '    SELECT event_time, car_id, kpi_id,',
    '           ROUND((lap_time_ms-current_best_lap_ms)/1000.0,2) AS pace_delta_s,',
    '           CASE',
    '               WHEN (lap_time_ms-current_best_lap_ms) >= 1500 THEN \'critical\'',
    '               WHEN (lap_time_ms-current_best_lap_ms) >= 500 THEN \'warning\'',
    '               ELSE \'none\'',
    '           END AS status',
    '    FROM scoped',
    '    WHERE (lap_time_ms-current_best_lap_ms) >= 500',
    ')',
    'SELECT event_time AS time, car_id AS car, kpi_id AS signal, pace_delta_s, status',
    'FROM alert_rows',
    "WHERE status REGEXP '${{severity:regex}}'",
    'ORDER BY event_time DESC',
    'LIMIT 20',
    '\"\"\")',
])

block('STRATEGY_CRITICAL', [
    'STRATEGY_CRITICAL = q(f\"\"\"',
    '{RACE}',
    'SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race',
    "WHERE s.severity='critical'",
    '  AND s.event_time BETWEEN race.race_start AND race.race_end',
    '  AND s.lap_number BETWEEN 1 AND 60',
    "  AND s.car_id REGEXP '${{car:regex}}'",
    '\"\"\")',
])

block('STRATEGY_WARNING', [
    'STRATEGY_WARNING = q(f\"\"\"',
    '{RACE}',
    'SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race',
    "WHERE s.severity='warning'",
    '  AND s.event_time BETWEEN race.race_start AND race.race_end',
    '  AND s.lap_number BETWEEN 1 AND 60',
    "  AND s.car_id REGEXP '${{car:regex}}'",
    '\"\"\")',
])

block('RC_CRITICAL', [
    'RC_CRITICAL = q(f\"\"\"',
    '{RACE}',
    'SELECT COUNT(*) AS value FROM race_control_results rc CROSS JOIN race',
    "WHERE rc.severity='critical'",
    '  AND rc.event_time BETWEEN race.race_start AND race.race_end',
    '  AND rc.lap_number BETWEEN 1 AND 60',
    "  AND rc.car_id REGEXP '${{car:regex}}'",
    '\"\"\")',
])

block('PIT_SIGNALS', [
    'PIT_SIGNALS = q(f\"\"\"',
    '{RACE}',
    'SELECT COUNT(*) AS value FROM strategy_results s CROSS JOIN race',
    "WHERE s.kpi_id='STR-002' AND s.value>=0.6",
    '  AND s.event_time BETWEEN race.race_start AND race.race_end',
    '  AND s.lap_number BETWEEN 1 AND 60',
    "  AND s.car_id REGEXP '${{car:regex}}'",
    '\"\"\")',
])

block('STREAM_LAG_MAX', [
    'STREAM_LAG_MAX = q(\"\"\"',
    'SELECT NULL AS value WHERE 1=0',
    '\"\"\")',
])

block('LAG_TIMELINE', [
    'LAG_TIMELINE = q(\"\"\"',
    'SELECT created_at AS time, COUNT(*) AS alert_events',
    'FROM alerts',
    'WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)',
    'GROUP BY created_at',
    'ORDER BY created_at',
    '\"\"\")',
])

block('HEALTH_MATRIX', [
    'HEALTH_MATRIX = q(\"\"\"',
    "SELECT 'Alert Pipeline' AS consumer, COUNT(*) AS events_seen,",
    "       SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) AS critical_events,",
    "       SUM(CASE WHEN severity='warning' THEN 1 ELSE 0 END) AS warning_events,",
    "       MAX(created_at) AS last_event, 'ACTIVE' AS status",
    'FROM alerts',
    'WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)',
    '\"\"\")',
])

block('INFRA_FEED', [
    'INFRA_FEED = q(\"\"\"',
    'SELECT created_at AS time, kpi_id AS signal, severity AS status,',
    "       'Alert Monitor' AS component, message",
    'FROM alerts',
    'WHERE created_at >= DATE_SUB((SELECT MAX(created_at) FROM alerts), INTERVAL 30 MINUTE)',
    'ORDER BY created_at DESC LIMIT 20',
    '\"\"\")',
])

block('DLQ_TIMELINE', [
    'DLQ_TIMELINE = q(\"\"\"',
    'SELECT failed_at AS time, source_topic, COUNT(*) AS dlq_events',
    'FROM dlq_events',
    'WHERE failed_at >= DATE_SUB((SELECT MAX(failed_at) FROM dlq_events), INTERVAL 30 MINUTE)',
    'GROUP BY failed_at, source_topic',
    'ORDER BY failed_at',
    '\"\"\")',
])

text = text.replace('last_eventWHERE 1=0', 'last_event WHERE 1=0')
text = text.replace('lap_numberBETWEEN', 'lap_number BETWEEN 1 AND 60')

compile(text, str(TARGET), 'exec')
TARGET.write_text(text, encoding='utf-8')
print('PATCH SUCCESS')
print('production.py updated safely.')
