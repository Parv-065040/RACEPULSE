-- Latest KPI-001 (Lap Pace Delta) status per car.
-- Suggested panel: Table or Stat panel showing "current race status" per car.
SELECT
    kr.car_id,
    kr.lap_number,
    kr.delta_ms,
    kr.severity,
    kr.computed_at
FROM kpi_results kr
INNER JOIN (
    SELECT car_id, MAX(computed_at) AS max_computed_at
    FROM kpi_results
    GROUP BY car_id
) latest
    ON kr.car_id = latest.car_id AND kr.computed_at = latest.max_computed_at
ORDER BY kr.car_id;
