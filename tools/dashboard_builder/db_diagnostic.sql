SELECT '=== DATA RANGES ===' AS section;

SELECT 'kpi_results' AS table_name,
       MIN(event_time) AS min_time,
       MAX(event_time) AS max_time,
       COUNT(*) AS rows_count
FROM kpi_results
WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND lap_number BETWEEN 1 AND 60

UNION ALL

SELECT 'strategy_results',
       MIN(event_time),
       MAX(event_time),
       COUNT(*)
FROM strategy_results
WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND lap_number BETWEEN 1 AND 60

UNION ALL

SELECT 'race_control_results',
       MIN(event_time),
       MAX(event_time),
       COUNT(*)
FROM race_control_results
WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND lap_number BETWEEN 1 AND 60

UNION ALL

SELECT 'alerts',
       MIN(created_at),
       MAX(created_at),
       COUNT(*)
FROM alerts;

SELECT '=== CURRENT RACE BOUNDARY ===' AS section;

SELECT
    MAX(event_time) AS race_end,
    DATE_SUB(MAX(event_time), INTERVAL 10 MINUTE) AS race_start
FROM kpi_results
WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND lap_number BETWEEN 1 AND 60;

SELECT '=== PACE TEST ===' AS section;

SELECT COUNT(*) AS pace_rows
FROM kpi_results k
WHERE k.event_time BETWEEN
      DATE_SUB(
          (SELECT MAX(event_time)
           FROM kpi_results
           WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
             AND lap_number BETWEEN 1 AND 60),
          INTERVAL 10 MINUTE
      )
  AND
      (SELECT MAX(event_time)
       FROM kpi_results
       WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
         AND lap_number BETWEEN 1 AND 60)
  AND k.car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND k.car_id REGEXP '.*'
  AND k.lap_number BETWEEN 1 AND 60;

SELECT '=== STRATEGY FEED TEST ===' AS section;

SELECT
    COUNT(*) AS total_rows,
    SUM(severity='critical') AS critical_rows,
    SUM(severity='warning') AS warning_rows,
    SUM(severity='none') AS none_rows
FROM strategy_results s
WHERE s.severity <> 'none'
  AND s.event_time BETWEEN
      DATE_SUB(
          (SELECT MAX(k.event_time)
           FROM kpi_results k
           WHERE k.lap_number BETWEEN 1 AND 60
             AND k.car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'),
          INTERVAL 10 MINUTE
      )
  AND
      (SELECT MAX(k.event_time)
       FROM kpi_results k
       WHERE k.lap_number BETWEEN 1 AND 60
         AND k.car_id REGEXP '^CAR_(0[1-9]|1[0-2])$')
  AND s.lap_number BETWEEN 1 AND 60;

SELECT '=== ALERT FEED TEST ===' AS section;

SELECT
    COUNT(*) AS total_rows,
    SUM(car_id IS NULL) AS null_car_rows,
    SUM(severity='critical') AS critical_rows,
    SUM(severity='warning') AS warning_rows,
    SUM(severity='none') AS none_rows
FROM alerts
WHERE created_at >= DATE_SUB(
    (SELECT MAX(created_at) FROM alerts),
    INTERVAL 10 MINUTE
);

SELECT '=== ALERT CAR DISTRIBUTION ===' AS section;

SELECT
    COALESCE(car_id,'<NULL>') AS car,
    severity,
    COUNT(*) AS rows_count
FROM alerts
WHERE created_at >= DATE_SUB(
    (SELECT MAX(created_at) FROM alerts),
    INTERVAL 10 MINUTE
)
GROUP BY car_id, severity
ORDER BY rows_count DESC;

SELECT '=== RACE CONTROL FEED TEST ===' AS section;

SELECT
    COUNT(*) AS total_rows,
    SUM(severity='critical') AS critical_rows,
    SUM(severity='warning') AS warning_rows,
    SUM(severity='none') AS none_rows
FROM race_control_results rc
WHERE rc.lap_number BETWEEN 1 AND 60
  AND rc.car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
  AND rc.event_time >= DATE_SUB(
      (SELECT MAX(event_time)
       FROM race_control_results
       WHERE lap_number BETWEEN 1 AND 60
         AND car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'),
      INTERVAL 10 MINUTE
  );

SELECT '=== PERFORMANCE ALERT TEST ===' AS section;

WITH race AS (
    SELECT
        MAX(event_time) AS race_end,
        DATE_SUB(MAX(event_time), INTERVAL 10 MINUTE) AS race_start
    FROM kpi_results
    WHERE car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
      AND lap_number BETWEEN 1 AND 60
),
scoped AS (
    SELECT k.*,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS best_ms
    FROM kpi_results k
    CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '^CAR_(0[1-9]|1[0-2])$'
)
SELECT
    COUNT(*) AS rows_in_scope,
    SUM((lap_time_ms-best_ms) >= 500) AS warning_or_critical,
    SUM((lap_time_ms-best_ms) >= 1500) AS critical
FROM scoped;

SELECT '=== DLQ ===' AS section;

SELECT
    COUNT(*) AS total_dlq,
    MIN(failed_at) AS first_dlq,
    MAX(failed_at) AS last_dlq
FROM dlq_events;

SELECT '=== INFRA ALERTS ===' AS section;

SELECT
    COUNT(*) AS infra_rows,
    MIN(created_at) AS first_infra,
    MAX(created_at) AS last_infra
FROM infra_alerts;

SELECT '=== STALE ALERTS ===' AS section;

SELECT
    COUNT(*) AS stale_rows,
    MIN(created_at) AS first_stale,
    MAX(created_at) AS last_stale
FROM alerts
WHERE kpi_id='SYS-STALE';
