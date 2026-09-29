-- Gap-to-leader trend over time, per car.
-- Suggested panel: Time series, one line per car_id, showing whether
-- each car is falling behind (positive trend) or catching up (negative).
SELECT
    computed_at AS time,
    car_id,
    trend_ms_per_lap
FROM gap_trend_results
-- WHERE $__timeFilter(computed_at)
ORDER BY computed_at ASC;
