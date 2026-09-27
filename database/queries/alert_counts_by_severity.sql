-- Count of alerts by severity, optionally filtered to a time window.
-- Suggested panel: Pie chart or Bar gauge showing alert distribution.
-- $__timeFilter(created_at) is Grafana's macro for its time-range picker;
-- replace with a plain WHERE created_at >= ... for manual testing.
SELECT
    severity,
    COUNT(*) AS alert_count
FROM alerts
-- WHERE $__timeFilter(created_at)
GROUP BY severity
ORDER BY FIELD(severity, 'critical', 'warning', 'none');
