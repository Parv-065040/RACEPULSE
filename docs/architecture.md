# RACEPULSE Architecture

## Purpose

RACEPULSE is an event-driven streaming analytics platform for simulated motorsport events.

**Sense → Stream → Analyze → Alert → Decide**

## Runtime

```text
Stateful Race Simulator
        |
        +--> race.timing
        +--> race.telemetry
        +--> race.tyres
        +--> race.weather
        +--> race.pitstops
        +--> race.incidents
        +--> business.fans
        +--> business.sponsors
                 |
                 v
          Kafka + ZooKeeper
                 |
       +---------+----------+-------------+
       |         |          |             |
 Performance  Strategy  Race Control  Commercial
       |         |          |             |
       +---------+----------+-------------+
                 |
          Validation / KPI /
          Rules / Alerts
                 |
        +--------+---------+
        |                  |
      MySQL          analytics.alerts
        |
      Grafana
```

## Consumers

| Consumer | Inputs | Outputs |
|---|---|---|
| Performance | timing + incidents | pace delta, gap trend, stale/retirement state |
| Strategy | timing, tyres, weather, pitstops | tyre risk, pit-window signal |
| Race Control | telemetry, timing, weather, incidents | track risk, vehicle risk |
| Commercial | fans, sponsors | engagement, exposure, conversion |

## Stateful simulation

The live runner owns one shared race simulator. Every stream for a lap is generated from the same state snapshot, preventing independently started producers from drifting into contradictory race states.

## Validation and failure closed

Every business/race stream uses the shared validation gate. Invalid events go to the system DLQ and are audited in the DLQ table. Duplicate event IDs are dropped by the bounded duplicate detector.

## Retirement semantics

A mechanical-failure incident is authoritative for retirement. The performance consumer also consumes incident events so its stale-stream monitor can suppress stale alerts for a legitimately retired car.

## Persistence

Analytical tables include kpi_results, gap_trend_results, strategy_results, race_control_results, commercial_results, alerts, stream_health, infra_alerts and dlq_events.

## Operational health

Kafka topic creation is deterministic because auto-create remains disabled. The stream monitor samples consumer-group lag and records health/infrastructure alerts.

## Boundary

RACEPULSE uses configurable educational heuristics. It is decision support for a streaming-data course demonstration, not a validated motorsport safety or race-strategy system.
