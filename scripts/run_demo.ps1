param(
  [string]$Scenario = "NORMAL_RACE",
  [double]$Delay = 1.0
)

$ErrorActionPreference = "Stop"

docker compose up -d
python scripts/create_topics.py
python -m database.migrations.run_migrations

$commands = @(
  "python -m consumers.performance.timing_consumer",
  "python -m consumers.strategy.strategy_consumer",
  "python -m consumers.race_control.race_control_consumer",
  "python -m consumers.commercial.commercial_consumer",
  "python -m ops.stream_monitor"
)

foreach ($cmd in $commands) {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
}

Start-Sleep -Seconds 3
python -m simulator.live_runner --scenario $Scenario --delay $Delay
