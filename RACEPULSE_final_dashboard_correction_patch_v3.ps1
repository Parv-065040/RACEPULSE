$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\tools\dashboard_builder\production.py")) {
    throw "Run this script from the RACEPULSE-FRESH repository root."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = ".\dashboard_final_patch_backup_$stamp"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RACEPULSE // FINAL DASHBOARD CORRECTION PATCH" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item ".\tools\dashboard_builder\production.py" "$backup\production.py" -Force

if (Test-Path ".\grafana\dashboards\generated") {
    New-Item -ItemType Directory -Force -Path "$backup\generated" | Out-Null
    Copy-Item ".\grafana\dashboards\generated\*.json" "$backup\generated\" -Force -ErrorAction SilentlyContinue
}

Write-Host "[OK] Backup created: $backup" -ForegroundColor Green

$source = Get-Content ".\tools\dashboard_builder\production.py" -Raw

function Replace-QueryBlock {
    param(
        [string]$Name,
        [string]$Replacement
    )

    $pattern = '(?ms)^' + [regex]::Escape($Name) + '\s*=\s*q\(f?""".*?"""\)'
    $matches = [regex]::Matches($source, $pattern)

    if ($matches.Count -eq 0) {
        Write-Host "[SKIP] Query block not present in production.py: $Name" -ForegroundColor Yellow
        return
    }

    if ($matches.Count -gt 1) {
        throw "Expected at most one query block for $Name, found $($matches.Count)."
    }

    $script:source = [regex]::Replace(
        $script:source,
        $pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $Replacement },
        1
    )
}

$replacement = @'
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
'@
Replace-QueryBlock "LATEST_LAP" $replacement

$replacement = @'
PACE = q(f"""
{RACE}
,scoped AS (
    SELECT k.*,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS current_best_lap_ms
    FROM kpi_results k CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '{CAR_RE}'
)
SELECT event_time AS time,
       car_id,
       ROUND((lap_time_ms - current_best_lap_ms)/1000.0,3) AS pace_delta_s
FROM scoped
ORDER BY event_time
""")
'@
Replace-QueryBlock "PACE" $replacement

$replacement = @'
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
'@
Replace-QueryBlock "CURRENT_CAR_STATUS" $replacement

$replacement = @'
PERFORMANCE_ALERTS = q(f"""
{RACE}
,scoped AS (
    SELECT k.*,
           MIN(k.lap_time_ms) OVER (PARTITION BY k.car_id) AS current_best_lap_ms
    FROM kpi_results k CROSS JOIN race
    WHERE k.event_time BETWEEN race.race_start AND race.race_end
      AND k.lap_number BETWEEN 1 AND 60
      AND k.car_id REGEXP '{CAR_RE}'
)
SELECT event_time AS time,
       car_id AS car,
       kpi_id AS signal,
       ROUND((lap_time_ms-current_best_lap_ms)/1000.0,2) AS pace_delta_s,
       CASE
           WHEN (lap_time_ms-current_best_lap_ms) >= 1500 THEN 'critical'
           WHEN (lap_time_ms-current_best_lap_ms) >= 500 THEN 'warning'
           ELSE 'none'
       END AS status
FROM scoped
WHERE (lap_time_ms-current_best_lap_ms) >= 500
ORDER BY event_time DESC
LIMIT 20
""")
'@
Replace-QueryBlock "PERFORMANCE_ALERTS" $replacement

$replacement = @'
ALERT_FEED = q(f"""
SELECT a.created_at AS time,
       a.car_id AS car,
       a.kpi_id AS signal,
       a.severity AS status,
       a.message
FROM alerts a
WHERE a.created_at BETWEEN
      DATE_SUB(
          (SELECT MAX(k.event_time)
           FROM kpi_results k
           WHERE k.lap_number BETWEEN 1 AND 60
             AND k.car_id REGEXP '{CAR_RE}'),
          INTERVAL 10 MINUTE
      )
  AND DATE_ADD(
          (SELECT MAX(k.event_time)
           FROM kpi_results k
           WHERE k.lap_number BETWEEN 1 AND 60
             AND k.car_id REGEXP '{CAR_RE}'),
          INTERVAL 10 MINUTE
      )
ORDER BY a.created_at DESC
LIMIT 20
""")
'@
Replace-QueryBlock "ALERT_FEED" $replacement

$replacement = @'
STRATEGY_FEED = q(f"""
SELECT s.event_time AS time,
       s.car_id AS car,
       CASE s.kpi_id
           WHEN 'STR-001' THEN 'TYRE DEGRADATION RISK'
           WHEN 'STR-002' THEN 'PIT WINDOW SIGNAL'
           ELSE s.kpi_id
       END AS signal,
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
'@
Replace-QueryBlock "STRATEGY_FEED" $replacement

$replacement = @'
RACE_CONTROL_FEED = q(f"""
SELECT rc.event_time AS time,
       rc.car_id AS car,
       CASE rc.kpi_id
           WHEN 'RC-001' THEN 'TRACK RISK'
           WHEN 'RC-002' THEN 'VEHICLE RISK'
           ELSE rc.kpi_id
       END AS signal,
       ROUND(rc.value,2) AS value,
       rc.severity AS status,
       rc.message
FROM race_control_results rc
WHERE rc.severity <> 'none'
  AND rc.event_time BETWEEN
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
  AND rc.lap_number BETWEEN 1 AND 60
ORDER BY rc.event_time DESC
LIMIT 20
""")
'@
Replace-QueryBlock "RACE_CONTROL_FEED" $replacement

$replacement = @'
STREAM_LAG_MAX = q("""
SELECT NULL AS value WHERE 1=0
""")
'@
Replace-QueryBlock "STREAM_LAG_MAX" $replacement

$replacement = @'
LAG_TIMELINE = q("""
SELECT NULL AS time, NULL AS consumer_group, NULL AS lag WHERE 1=0
""")
'@
Replace-QueryBlock "LAG_TIMELINE" $replacement

$replacement = @'
HEALTH_MATRIX = q("""
SELECT NULL AS consumer, NULL AS lag, NULL AS events_seen,
       NULL AS status, NULL AS last_event WHERE 1=0
""")
'@
Replace-QueryBlock "HEALTH_MATRIX" $replacement

$replacement = @'
INFRA_FEED = q("""
SELECT NULL AS time, NULL AS signal, NULL AS status,
       NULL AS component, NULL AS message WHERE 1=0
""")
'@
Replace-QueryBlock "INFRA_FEED" $replacement

Set-Content ".\tools\dashboard_builder\production.py" $source -Encoding UTF8
Write-Host "[OK] production.py patched." -ForegroundColor Green

# Syntax-check the builder before generating anything.
python -m py_compile ".\tools\dashboard_builder\production.py"
if ($LASTEXITCODE -ne 0) {
    throw "production.py syntax check failed. Grafana was NOT restarted."
}
Write-Host "[OK] production.py syntax check passed." -ForegroundColor Green

if (Test-Path ".\grafana\dashboards\generated") {
    Get-ChildItem ".\grafana\dashboards\generated" -Filter "*.json" -File |
        Remove-Item -Force
}

python -m tools.dashboard_builder.build
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard generation failed. Grafana was NOT restarted."
}

$expected = @(
    "racepulse-ceo-command-center.json",
    "racepulse-race-operations.json",
    "racepulse-strategy.json",
    "racepulse-race-control.json",
    "racepulse-commercial.json",
    "racepulse-streaming-engineering.json"
)

$files = Get-ChildItem ".\grafana\dashboards\generated" -Filter "*.json" -File
if ($files.Count -ne 6) {
    throw "Expected exactly 6 generated dashboards, found $($files.Count)."
}

foreach ($name in $expected) {
    $path = ".\grafana\dashboards\generated\$name"
    if (-not (Test-Path $path)) {
        throw "Missing generated dashboard: $name"
    }
    Get-Content $path -Raw | ConvertFrom-Json | Out-Null
    Write-Host "[OK] JSON: $name" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING UNIT TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

python -m pytest tests/unit -q
if ($LASTEXITCODE -ne 0) {
    throw "Unit tests failed. Grafana was NOT restarted."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING INTEGRATION TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

python -m pytest tests/integration -q
if ($LASTEXITCODE -ne 0) {
    throw "Integration tests failed. Grafana was NOT restarted."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESTARTING GRAFANA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

docker restart racepulse-grafana | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Grafana restart failed."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " FINAL DASHBOARD PATCH COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup: $backup" -ForegroundColor Yellow
Write-Host "Refresh Grafana with Ctrl+Shift+R." -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected:"
Write-Host "  - Current Lap = 60"
Write-Host "  - Pace delta uses current-race best lap"
Write-Host "  - Alert / strategy / race-control feeds query real current data"
Write-Host "  - DLQ remains real"
Write-Host "  - Empty stream_health / infra_alerts remain honest"
Write-Host ""
