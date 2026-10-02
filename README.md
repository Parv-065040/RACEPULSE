# 🏎️ RACEPULSE

## Real-Time Motorsport Event Intelligence & Race Operations Platform

> **SENSE → STREAM → ANALYZE → ALERT → DECIDE**

RACEPULSE is a production-style real-time streaming analytics platform built for motorsport/race-event intelligence. It converts multiple race and business event streams into configurable KPIs, risk signals, alerts, and decision-oriented Grafana dashboards.

The project demonstrates an end-to-end streaming architecture using **Apache Kafka, Python, MySQL, Grafana, Docker, YAML-based configuration, and automated testing**.

---

## 1. Executive Overview

Modern motorsport produces many streams simultaneously:

- Vehicle telemetry
- Lap timing
- Tyre condition
- Weather and track conditions
- Pit-stop activity
- Race-control incidents
- Fan engagement
- Sponsorship activity
- Streaming-system health

The challenge is not only collecting these events. The challenge is transforming them into **timely, correlated, and actionable intelligence**.

RACEPULSE creates an event-driven intelligence layer between raw events and decision-makers.

```text
RAW EVENTS
    ↓
VALIDATION
    ↓
KAFKA STREAMING
    ↓
CONSUMERS
    ↓
WINDOWING + KPI ENGINE
    ↓
RULES + THRESHOLDS
    ↓
ALERTS
    ↓
MYSQL
    ↓
GRAFANA
    ↓
DECISION SUPPORT
```

---

# 2. Problem Statement

Race teams and event operators deal with rapidly changing information across multiple domains.

A meaningful performance change may involve several related events:

```text
Tyre degradation
      ↓
Grip reduction
      ↓
Lap-time deterioration
      ↓
Gap change
      ↓
Strategy relevance
```

Similarly:

```text
Weather change
      ↓
Track wetness
      ↓
Grip change
      ↓
Vehicle performance change
      ↓
Tyre behaviour
      ↓
Strategy / race-control signal
```

Traditional dashboards often display these streams independently.

RACEPULSE is designed to connect them through a streaming analytics layer so that users can investigate **what changed, where it changed, and which analytical signal was generated**.

---

# 3. Core Architecture

RACEPULSE follows the architecture:

```text
                    RACEPULSE
                        │
                        ▼
                     SENSE
                        │
                        ▼
                    STREAM
                        │
                        ▼
                    ANALYZE
                        │
                        ▼
                     ALERT
                        │
                        ▼
                     DECIDE
```

Detailed flow:

```text
┌─────────────────────────────────────────────────────────────┐
│                    EVENT GENERATION                          │
│                                                             │
│ Timing | Telemetry | Tyres | Weather | Pit Stops | Incidents│
│ Fans   | Sponsors                                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Kafka + ZooKeeper│
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        Performance      Strategy      Race Control
         Consumer        Consumer        Consumer
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌──────────────────┐
                    │ Analytics Engine │
                    │                  │
                    │ Validation       │
                    │ Windowing        │
                    │ Formulas         │
                    │ Rules            │
                    │ Alerts           │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                 MySQL             Alerts
                    │                 │
                    └────────┬────────┘
                             ▼
                         Grafana
```

---

# 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Producers, simulator, consumers and analytics |
| Apache Kafka | Real-time event streaming |
| Apache ZooKeeper | Kafka coordination |
| MySQL | Analytical persistence |
| Grafana | Real-time visualization |
| Docker / Docker Compose | Infrastructure orchestration |
| Pytest | Automated testing |
| YAML | Formula, threshold, parameter and window configuration |
| Git / GitHub | Version control and collaboration |

---

# 5. Kafka Event Architecture

The system uses domain-oriented Kafka topics.

| Topic | Purpose |
|---|---|
| `race.timing` | Lap timing, position and gap data |
| `race.telemetry` | Vehicle telemetry |
| `race.tyres` | Tyre condition and degradation |
| `race.weather` | Weather and track conditions |
| `race.pitstops` | Pit-stop events |
| `race.incidents` | Race-control incidents |
| `business.fans` | Fan engagement |
| `business.sponsors` | Sponsorship activity |
| `analytics.alerts` | Generated analytical alerts |
| `system.dlq` | Invalid/rejected events |

The platform also uses internal/system monitoring streams and persisted health information where applicable.

---

# 6. Stateful Race Simulation

RACEPULSE uses a stateful race simulator rather than generating completely independent random records.

The simulator maintains race-related state across:

- Cars
- Race laps
- Timing
- Telemetry
- Tyres
- Weather
- Pit stops
- Incidents
- Fan activity
- Sponsorship activity

This allows downstream consumers to observe related events instead of isolated random values.

Example:

```text
RAIN
 ↓
TRACK WETNESS
 ↓
GRIP CHANGE
 ↓
VEHICLE PERFORMANCE
 ↓
LAP-TIME CHANGE
 ↓
TYRE / STRATEGY SIGNAL
```

---

# 7. Supported Race Scenarios

The simulator supports controlled scenarios for testing and demonstration.

| Scenario | Purpose |
|---|---|
| `NORMAL_RACE` | Baseline race behaviour |
| `RAIN` | Changing weather and track conditions |
| `TYRE_CRISIS` | Accelerated tyre degradation |
| `SAFETY_CAR` | Race-control and gap changes |
| `CLOSE_BATTLE` | Tight racing gaps |
| `MECHANICAL_FAILURE` | Vehicle failure and retirement |
| `PIT_STOP` | Pit-stop activity |
| `COMMERCIAL_SURGE` | Increased fan/sponsor activity |
| `DATA_FAILURE` | Missing/unhealthy data streams |
| `CONFIGURATION_FAILURE` | Invalid configuration handling |

---

# 8. Validation & Data Quality

Every event passes through a centralized validation layer before analytical processing.

Validation covers:

- JSON parsing
- Object/type validation
- Required fields
- Data types
- Value ranges
- UUID/event identifiers
- Timestamps
- Known cars/entities
- Business-rule constraints
- Duplicate event IDs

Invalid events are routed to:

```text
system.dlq
```

rather than being silently processed.

### Extra fields

Additional fields can be tolerated where the event contract permits them.

### Duplicate events

Duplicate `event_id` values are detected and prevented from creating duplicate analytical processing.

### Failure-closed configuration

Invalid formulas/configuration are rejected while the last valid configuration remains available.

---

# 9. Analytics Architecture

The analytical layer separates:

```text
VALIDATION
    ↓
WINDOWING
    ↓
FORMULAS
    ↓
RULES
    ↓
ALERTS
```

This separation allows the system to distinguish between:

- What should be calculated?
- Over what window?
- When is the result abnormal?
- How severe is the abnormality?

---

# 10. Configurable Analytics

Important analytical logic is externalized into configuration.

```text
config/
├── formulas.yaml
├── parameters.yaml
├── thresholds.yaml
├── windows.yaml
└── schemas/
```

Examples of configurable elements:

- KPI formulas
- Formula weights
- Warning thresholds
- Critical thresholds
- Window durations
- Allowed lateness
- Scenario parameters

This supports live demonstration of configuration changes without rewriting the consumer architecture.

The project follows a **last-known-good configuration** principle: invalid configuration should not silently replace a valid configuration.

---

# 11. Windowed Streaming Analytics

The primary analytical model uses configurable time windows.

The project includes:

```text
Short Window   → 5 sec
Default Window → 15 sec
Medium Window  → 30 sec
Long Window    → 60 sec
```

The default streaming assignment requirement of a **15-second tumbling window** is implemented through the configuration layer.

Windowed calculations are persisted for dashboard consumption.

---

# 12. Core Analytical Domains

## Performance Intelligence

Focuses on:

- Lap pace
- Pace deterioration
- Gap trends
- Average speed
- Vehicle performance

### Pace Delta

Measures current lap performance relative to a reference/best lap.

---

## Strategy Intelligence

Combines contextual signals from:

- Timing
- Tyres
- Weather
- Pit stops

Key signals include:

- Tyre degradation risk
- Grip loss
- Pace deterioration
- Pit-window signal

Example strategy model:

```text
Tyre Degradation
       +
Grip Loss
       +
Relative Pace Degradation
       +
Track Wetness
       ↓
Strategy Risk
```

---

## Race Control Intelligence

Focuses on:

- Track risk
- Vehicle risk
- Incidents
- Operational conditions
- Stale-stream signals

Vehicle retirement is treated differently from an unexplained data-stream failure so that legitimate race events are not automatically interpreted as infrastructure failures.

---

## Commercial Intelligence

Uses business streams for:

- Fan engagement
- Sponsor visibility
- Sponsor conversion
- Commercial surge analysis

---

# 13. Alert Engine

RACEPULSE converts analytical results into structured alerts.

The general flow is:

```text
Event
 ↓
Validation
 ↓
KPI
 ↓
Threshold Evaluation
 ↓
Severity
 ↓
Alert
 ↓
MySQL / Grafana
```

Severity levels include:

```text
CRITICAL
WARNING
NONE
```

Alerts can contain:

- KPI identifier
- Signal
- Severity
- Affected car/entity
- Value
- Event timestamp
- Event identifier
- Context

Alerts are published through:

```text
analytics.alerts
```

and persisted in MySQL.

---

# 14. Reliability Engineering

RACEPULSE was designed with production-style failure handling.

## Malformed JSON

```text
Malformed Event
      ↓
Validation Failure
      ↓
DLQ
```

The consumer remains operational.

## Invalid Schema

```text
Schema Failure
      ↓
DLQ
      ↓
No downstream analytical corruption
```

## Duplicate Event

```text
Duplicate event_id
      ↓
Deduplication
      ↓
Event dropped/count tracked
```

## Invalid Formula

```text
Invalid Formula
      ↓
Reject
      ↓
Retain Last Valid Formula
```

## Stale Stream

```text
No new events
      ↓
Stale-stream detection
      ↓
SYS-STALE alert
```

## Zero vs No Data

The dashboard and analytical layer distinguish between:

```text
0
```

and:

```text
NO DATA
```

This prevents missing streams from being misrepresented as healthy zero values.

## Idempotency

Replay or repeated processing should not create duplicate analytical records where the persistence contract defines uniqueness.

---

# 15. Database Layer

MySQL stores analytical results used by downstream dashboards.

Important persisted domains include:

```text
kpi_results
gap_trend_results
windowed_kpi_results
strategy_results
race_control_results
commercial_results
alerts
stream_health
infra_alerts
dlq_events
```

The database is accessed by the consumers and Grafana dashboards.

Database migrations are versioned and applied through the project's migration structure.

---

# 16. Grafana Dashboard Suite

The final RACEPULSE dashboard layer contains **six production dashboards** with a total of **91 panels**.

| Dashboard | Panels | Main Question |
|---|---:|---|
| CEO Command Center | 16 | What is the overall race/business picture? |
| Race Operations | 17 | What is happening on track? |
| Strategy Intelligence | 14 | What strategic signals require attention? |
| Race Control | 14 | What safety/operational risks exist? |
| Commercial Intelligence | 16 | What is happening with fans and sponsors? |
| Streaming Engineering | 14 | Is the streaming platform healthy? |

---

## 16.1 CEO Command Center

Executive-level view containing:

- Race progress
- Current performance
- Pace delta
- Race alerts
- Risk signals
- Commercial indicators
- Current-lap ranking
- Pace distribution
- Platform-level signals

The dashboard is intended for rapid executive situational awareness.

---

## 16.2 Race Operations

Operational race view containing:

- Current speed ranking
- Gap to leader
- Lap progression
- Timing information
- Performance signals
- Alert severity
- Operational feeds

---

## 16.3 Strategy Intelligence

Focused on strategic decision support:

- Tyre risk
- Tyre degradation
- Grip
- Pace deterioration
- Strategy signals
- Pit-window indicators
- Vehicle-risk states

---

## 16.4 Race Control

Focused on:

- Track risk
- Vehicle risk
- Incidents
- Alert severity
- Operational alert feeds
- Risk-state distributions

---

## 16.5 Commercial Intelligence

Focused on:

- Fan engagement
- Sponsor visibility
- Sponsor conversion
- Commercial activity
- Engagement trends
- Commercial alert signals

---

## 16.6 Streaming Engineering

Focused on the health of the analytics platform:

- Infrastructure alert feed
- Data quality / DLQ feed
- Alert severity mix
- Alert signal mix
- Streaming health indicators
- Platform-level monitoring

An empty operational table is not fabricated into a false zero. Where no persisted data exists, the dashboard intentionally shows **No Data**.

---

# 17. Dashboard Design Principles

The final dashboards use a production-oriented dark technical interface.

Design principles include:

- Decision-oriented panels
- Consistent typography
- Compact information density
- 12-car filtering
- Severity filtering
- Configurable time range
- Real-time refresh
- Semantic alert colors
- Appropriate units
- Threshold-aware visualization
- Clear NO DATA states

Dashboard variables include:

```text
Car
Severity
```

The dashboard layer also includes semantic visualizations such as:

- Current pace ranking
- Current speed ranking
- Gap-to-leader ranking
- Tyre-risk ranking
- Vehicle-risk state distribution
- Alert severity mix
- Alert signal mix
- Lap-time distribution
- Sponsor visibility
- Sponsor conversion

---

# 18. Demo Architecture

A typical demonstration follows:

```text
START INFRASTRUCTURE
        ↓
START RACE SIMULATOR
        ↓
EVENTS ENTER KAFKA
        ↓
CONSUMERS PROCESS EVENTS
        ↓
KPIs GENERATED
        ↓
ALERTS GENERATED
        ↓
RESULTS STORED IN MYSQL
        ↓
GRAFANA UPDATES
```

The strongest demonstrations use controlled scenarios such as:

```text
RAIN
TYRE CRISIS
MECHANICAL FAILURE
PIT STOP
COMMERCIAL SURGE
DATA FAILURE
CONFIGURATION FAILURE
```

These scenarios allow the same platform to demonstrate performance, strategy, race-control, commercial, and reliability behaviour.

---

# 19. Testing & Validation

The final frozen dashboard build was validated with:

```text
Dashboard Python compilation     PASS
Dashboard generation             PASS
Generated JSON validation        6 / 6 PASS
Git diff check                   PASS
Unit tests                       110 PASS
Integration tests                2 PASS
Integration tests skipped       1
```

The final dashboard builder generated:

```text
CEO Command Center               16 panels
Race Operations                  17 panels
Strategy Intelligence            14 panels
Race Control                     14 panels
Commercial Intelligence          16 panels
Streaming Engineering            14 panels
```

The final live race simulator was also validated through a **60-lap run**, with **84 events per lap**, and the Kafka pipeline was verified to drain successfully with consumer lag at zero across the active consumer groups.

---

# 20. 12-Car Grid

The simulator contains a 12-car grid:

| Car ID | Team |
|---|---|
| CAR_01 | Apex One |
| CAR_02 | Vortex Racing |
| CAR_03 | Velocity Motorsport |
| CAR_04 | EcoDrive GP |
| CAR_05 | Velocity Works |
| CAR_06 | Northstar Racing |
| CAR_07 | RainForce GP |
| CAR_08 | Titan Motorsport |
| CAR_09 | Endurance Racing |
| CAR_10 | Midland GP |
| CAR_11 | Raptor Racing |
| CAR_12 | Phoenix Motorsport |

The dashboard car selector is restricted to the supported 12-car grid.

---

# 21. Project Structure

```text
RACEPULSE/
│
├── config/
│   ├── formulas.yaml
│   ├── parameters.yaml
│   ├── thresholds.yaml
│   ├── windows.yaml
│   ├── cars.yaml
│   └── schemas/
│
├── consumers/
│   ├── performance/
│   ├── strategy/
│   ├── race_control/
│   ├── commercial/
│   └── windowed/
│
├── producers/
│
├── simulator/
│
├── engine/
│   ├── validation/
│   ├── rules/
│   ├── alerts/
│   └── ...
│
├── database/
│   ├── schema.sql
│   └── migrations/
│
├── grafana/
│   ├── dashboards/
│   ├── provisioning/
│   └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── ...
│
├── tools/
│   └── dashboard_builder/
│
├── docs/
│
├── docker-compose.yml
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

# 22. Installation

## Prerequisites

Recommended environment:

- Windows / Linux / macOS
- Python 3.11+
- Docker Desktop
- Docker Compose
- Git
- VS Code or equivalent IDE

---

## Clone

```bash
git clone https://github.com/Parv-065040/RACEPULSE.git
cd RACEPULSE
```

---

## Python Environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 23. Start the Platform

Start Docker services:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

The Compose stack provides the streaming infrastructure, database, Grafana, consumers and simulator components defined by the project.

---

# 24. Run the Dashboard Builder

The Grafana dashboards are generated from the production dashboard builder.

```bash
python -m tools.dashboard_builder.build
```

Validate the Python source:

```bash
python -m py_compile .\tools\dashboard_builder\production.py
```

The generated dashboards are stored under:

```text
grafana/dashboards/generated/
```

---

# 25. Run Tests

Unit tests:

```bash
python -m pytest tests/unit -q
```

Integration tests:

```bash
python -m pytest tests/integration -q
```

Full suite:

```bash
python -m pytest -q
```

---

# 26. Dockerized Race Run

A representative simulator run can be executed through Docker.

Example:

```powershell
docker compose run --rm `
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 `
  race-simulator `
  python -m simulator.live_runner `
  --scenario NORMAL_RACE `
  --laps 20 `
  --delay 2
```

The final validation run was also performed over 60 laps.

---

# 27. Configuration Examples

Formula configuration is maintained separately from Python code.

Example:

```yaml
strategy:
  STR-001:
    name: Tyre Degradation Risk
    formula: "degradation_per_lap*5 + grip_loss*2 + pace_delta_ratio*0.4 + track_wetness*0.5"
    version: 2
```

Thresholds are maintained independently:

```text
KPI
 ↓
Warning threshold
 ↓
Critical threshold
```

This makes live demonstration and analytical tuning easier.

---

# 28. Security & Environment

Do not commit real credentials.

Use:

```text
.env
```

locally and provide:

```text
.env.example
```

for required configuration.

Sensitive credentials should never be placed in source code or committed to GitHub.

---

# 29. Scope & Limitations

RACEPULSE is an academic and demonstration platform using simulated motorsport data.

It is not intended to replace:

- Official race timing systems
- Professional race engineers
- FIA/race-control systems
- Safety-critical systems
- Validated commercial motorsport strategy software

The formulas, thresholds and risk indicators are project-defined analytical models. They demonstrate streaming analytics and decision-support architecture rather than claiming real-world motorsport validation.

---

# 30. Future Scope

Potential extensions include:

### Advanced Anomaly Detection

Machine-learning models for telemetry and race-event anomalies.

### AI-Powered Race Explanations

Natural-language explanations of correlated signals.

Example:

```text
CAR_07 pace deteriorated while grip decreased
and track wetness increased across recent windows.
```

### Strategy Simulation

Evaluate alternative pit-stop strategies against simulated future race conditions.

### Real-Time External Data

Connect official or licensed external racing feeds.

### Predictive Analytics

Add predictive models for:

- Tyre life
- Pit-window probability
- Mechanical risk
- Pace degradation
- Fan engagement

### Venue Intelligence

Extend the platform to:

- Crowd movement
- Entry/exit flows
- Parking
- Concessions
- Venue incidents

---

# 31. Team

**FORE School of Management, New Delhi**

**PGDM — Big Data Analytics**

| Member | ID |
|---|---:|
| Parv | 065040 |
| Awantika Kholia | 065060 |
| Navroop | 065039 |
| Yashi Tiwari | 065054 |

The project was developed collaboratively using Git/GitHub feature branches, testing, integration and release tagging.

---

# 32. Final Release

The final production-style release is tagged:

```text
v1.0-final
```

Release philosophy:

```text
SIMULATE
    ↓
STREAM
    ↓
VALIDATE
    ↓
PROCESS
    ↓
ANALYZE
    ↓
ALERT
    ↓
PERSIST
    ↓
VISUALIZE
    ↓
DECIDE
```

The final dashboard layer is frozen and validated as part of this release.

---

# 33. Key Takeaway

RACEPULSE demonstrates how streaming infrastructure can move beyond simply collecting events and instead create a complete analytical decision-support pipeline.

```text
EVENTS
  ↓
CONTEXT
  ↓
STREAMING ANALYTICS
  ↓
SIGNALS
  ↓
ALERTS
  ↓
DECISION SUPPORT
```

> **RACEPULSE — From Race Events to Real-Time Intelligence.**


