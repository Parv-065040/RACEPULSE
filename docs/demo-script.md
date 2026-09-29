# RACEPULSE Live Demo Script

## 1. Start infrastructure

```powershell
docker compose up -d
docker compose ps
```

## 2. Create Kafka topics

```powershell
python scripts/create_topics.py
```

Kafka auto-create is intentionally disabled.

## 3. Apply database migrations

```powershell
python -m database.migrations.run_migrations
```

## 4. Start consumers

Open separate PowerShell terminals:

```powershell
python -m consumers.performance.timing_consumer
python -m consumers.strategy.strategy_consumer
python -m consumers.race_control.race_control_consumer
python -m consumers.commercial.commercial_consumer
python -m ops.stream_monitor
```

## 5. Start the shared live race

Normal:

```powershell
python -m simulator.live_runner --scenario NORMAL_RACE --delay 1
```

Bounded demo:

```powershell
python -m simulator.live_runner --scenario RAIN --delay 1 --laps 10
```

Other controlled scenarios include TYRE_CRISIS, SAFETY_CAR, MECHANICAL_FAILURE and COMMERCIAL_SURGE.

## 6. Open Grafana

```
http://localhost:3000
```

Default Docker credentials are admin/admin.

Use the RACEPULSE folder and switch between Executive, Race Operations, Strategy, Commercial and Streaming Engineering.

## 7. Demonstration storyline

### Normal race
Show continuous events, pace, gap and alerts.

### Rain
Trace rain -> track wetness -> grip -> race-control risk -> strategy risk.

### Tyre crisis
Show strategy risk and pit-window signals.

### Mechanical failure
Show the incident and retirement. The retired car stops normal streams, but the stale monitor must not generate a false stale alert.

### Commercial surge
Show fan engagement and sponsor exposure increasing through the shared excitement factor.

### Failure handling
Send an invalid event. Expected flow:

```
invalid event
 -> ValidationGate
 -> system.dlq
 -> dlq_events
 -> Streaming Engineering dashboard
```

## 8. Dynamic configuration

Change a supported threshold in config/thresholds.yaml while the performance consumer is running.

Expected behavior:
- valid configuration is loaded
- invalid configuration is rejected
- the last valid configuration remains active

## 9. Final narrative

RACEPULSE is not a scoreboard. One shared race state creates multiple event streams; Kafka distributes them; independent consumers correlate the streams; configurable analytics produce signals; MySQL persists the state; and Grafana exposes both race intelligence and streaming-system health.
