-- Most recent critical alerts across all cars, newest first.
-- Suggested panel: Table panel styled as an "active alerts" feed,
-- e.g. for the System Health / race-control dashboard view.
SELECT
    car_id,
    kpi_id,
    severity,
    message,
    created_at
FROM alerts
WHERE severity = 'critical'
ORDER BY created_at DESC
LIMIT 50;
