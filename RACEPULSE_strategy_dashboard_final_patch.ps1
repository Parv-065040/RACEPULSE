$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\consumers\strategy\strategy_consumer.py")) {
    throw "Run this script from the RACEPULSE-FRESH repository root."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = ".\dashboard_strategy_final_backup_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$files = @(
    ".\consumers\strategy\strategy_consumer.py",
    ".\config\formulas.yaml",
    ".\tools\dashboard_builder\production.py"
)

foreach ($file in $files) {
    if (-not (Test-Path $file)) { throw "Missing required file: $file" }
    $dest = Join-Path $backup (($file -replace '^\.\[\\/]', '') -replace '[\\/:]', '_')
    Copy-Item $file $dest -Force
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RACEPULSE // STRATEGY + DASHBOARD FINAL CORRECTION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[OK] Backup created: $backup" -ForegroundColor Green

# ------------------------------------------------------------
# 1. Fix the strategy-risk scale at the calculation source.
#    pace_delta_seconds was being multiplied directly by 0.4,
#    turning a ~60s pace delta into ~24 risk points.
#    Use scale-free pace degradation relative to the car's best lap.
# ------------------------------------------------------------
$strategyPath = ".\consumers\strategy\strategy_consumer.py"
$strategy = Get-Content $strategyPath -Raw

$old = '    pace_delta_s = max(0.0, (timing["lap_time_ms"] - best) / 1000.0)' + "`r`n" +
       '    grip_loss = max(0.0, 1.0 - float(tyres["grip"]))' + "`r`n" +
       '    degradation = float(tyres["degradation_per_lap"])' + "`r`n" +
       '    wetness = float(weather.get("track_wetness", 0.0))' + "`r`n" +
       '    risk = degradation * 5.0 + grip_loss * 2.0 + pace_delta_s * 0.4 + wetness * 0.5'

$new = '    pace_delta_s = max(0.0, (timing["lap_time_ms"] - best) / 1000.0)' + "`r`n" +
       '    best_lap_s = max(best / 1000.0, 1.0)' + "`r`n" +
       '    pace_delta_ratio = pace_delta_s / best_lap_s' + "`r`n" +
       '    grip_loss = max(0.0, 1.0 - float(tyres["grip"]))' + "`r`n" +
       '    degradation = float(tyres["degradation_per_lap"])' + "`r`n" +
       '    wetness = float(weather.get("track_wetness", 0.0))' + "`r`n" +
       '    risk = degradation * 5.0 + grip_loss * 2.0 + pace_delta_ratio * 0.4 + wetness * 0.5'

if (-not $strategy.Contains($old)) {
    throw "Expected strategy risk calculation block was not found. No strategy source change made."
}

$strategy = $strategy.Replace($old, $new)
Set-Content $strategyPath $strategy -Encoding UTF8
Write-Host "[OK] Strategy risk calculation normalized to relative pace degradation." -ForegroundColor Green

# ------------------------------------------------------------
# 2. Keep the YAML formula aligned with the actual calculation.
# ------------------------------------------------------------
$formulaPath = ".\config\formulas.yaml"
$formulas = Get-Content $formulaPath -Raw

$oldFormula = 'formula: "degradation_per_lap*5 + grip_loss*2 + pace_delta_seconds*0.4 + track_wetness*0.5"'
$newFormula = 'formula: "degradation_per_lap*5 + grip_loss*2 + pace_delta_ratio*0.4 + track_wetness*0.5"'

if (-not $formulas.Contains($oldFormula)) {
    throw "Expected STR-001 formula was not found in config/formulas.yaml."
}

$formulas = $formulas.Replace($oldFormula, $newFormula)
$formulas = $formulas.Replace("    version: 1`r`n  STR-002:", "    version: 2`r`n  STR-002:")
$formulas = $formulas.Replace("    version: 1`n  STR-002:", "    version: 2`n  STR-002:")
Set-Content $formulaPath $formulas -Encoding UTF8
Write-Host "[OK] config/formulas.yaml aligned; STR-001 version bumped to 2." -ForegroundColor Green

# ------------------------------------------------------------
# 3. Fix Critical Infra Alerts.
#    infra_alerts is the authoritative infrastructure-alert table.
#    It is currently empty, so COUNT(*) correctly returns 0.
# ------------------------------------------------------------
$prodPath = ".\tools\dashboard_builder\production.py"
$prod = Get-Content $prodPath -Raw

$oldInfra = @'
INFRA_CRITICAL = q(f"""
{RACE}
SELECT COUNT(*) AS value FROM alerts a CROSS JOIN race
WHERE a.severity='critical'
  AND (a.kpi_id LIKE 'SYS-%' OR a.kpi_id LIKE 'INFRA-%')
  AND a.created_at BETWEEN DATE_SUB(race.race_end, INTERVAL 10 MINUTE) AND DATE_ADD(race.race_end, INTERVAL 10 MINUTE)
""")
'@

$newInfra = @'
INFRA_CRITICAL = q("""
SELECT COUNT(*) AS value
FROM infra_alerts
WHERE severity = 'critical'
  AND observed_at >= DATE_SUB(
      (SELECT COALESCE(MAX(observed_at), CURRENT_TIMESTAMP) FROM infra_alerts),
      INTERVAL 30 MINUTE
  )
""")
'@

if (-not $prod.Contains($oldInfra)) {
    throw "Expected INFRA_CRITICAL query block was not found in production.py."
}

$prod = $prod.Replace($oldInfra, $newInfra)
Set-Content $prodPath $prod -Encoding UTF8
Write-Host "[OK] Critical Infra Alerts now uses infra_alerts." -ForegroundColor Green

# ------------------------------------------------------------
# 4. Validate source syntax.
# ------------------------------------------------------------
python -m py_compile ".\consumers\strategy\strategy_consumer.py"
if ($LASTEXITCODE -ne 0) { throw "strategy_consumer.py syntax check failed." }

python -m py_compile ".\tools\dashboard_builder\production.py"
if ($LASTEXITCODE -ne 0) { throw "production.py syntax check failed." }

Write-Host "[OK] Python syntax checks passed." -ForegroundColor Green

# ------------------------------------------------------------
# 5. Regenerate dashboards.
# ------------------------------------------------------------
if (Test-Path ".\grafana\dashboards\generated") {
    Get-ChildItem ".\grafana\dashboards\generated" -Filter "*.json" -File |
        Remove-Item -Force
}

python -m tools.dashboard_builder.build
if ($LASTEXITCODE -ne 0) { throw "Dashboard generation failed." }

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
    throw "Expected 6 generated dashboards, found $($files.Count)."
}

foreach ($name in $expected) {
    $path = ".\grafana\dashboards\generated\$name"
    if (-not (Test-Path $path)) { throw "Missing generated dashboard: $name" }
    Get-Content $path -Raw | ConvertFrom-Json | Out-Null
    Write-Host "[OK] JSON: $name" -ForegroundColor Green
}

# ------------------------------------------------------------
# 6. Run tests before touching running services.
# ------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING UNIT TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

python -m pytest tests/unit -q
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed. Services were NOT restarted." }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING INTEGRATION TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

python -m pytest tests/integration -q
if ($LASTEXITCODE -ne 0) { throw "Integration tests failed. Services were NOT restarted." }

# ------------------------------------------------------------
# 7. Restart strategy consumer + Grafana.
#    Do not delete historical rows.
# ------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESTARTING STRATEGY CONSUMER + GRAFANA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

docker restart racepulse-strategy-consumer | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] racepulse-strategy-consumer container name was not found." -ForegroundColor Yellow
    Write-Host "       Restart the strategy consumer service manually before the next live run." -ForegroundColor Yellow
}

docker restart racepulse-grafana | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Grafana restart failed." }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " FINAL CORRECTION PATCH COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup: $backup" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT:"
Write-Host "  - Existing historical strategy rows were NOT deleted."
Write-Host "  - Existing historical race-control/commercial data was NOT changed."
Write-Host "  - A fresh 60-lap run is required to populate corrected STR-001/STR-002 values."
Write-Host "  - After the fresh run, verify Strategy Intelligence again."
Write-Host "  - Critical Infra Alerts should now be 0 while infra_alerts is empty."
Write-Host ""
