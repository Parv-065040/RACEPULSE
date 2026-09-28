# 🏎️ RACEPULSE

### Real-Time Motorsport Event Intelligence & Race Operations Platform

> **Sense → Stream → Analyze → Alert → Decide**

RACEPULSE is a real-time streaming analytics platform designed to transform multiple racing-event data streams into operational, strategic, safety, and commercial intelligence.

Instead of functioning as a conventional race scoreboard, RACEPULSE correlates telemetry, timing, tyre, weather, pit-stop, incident, fan-engagement, and sponsorship streams to identify meaningful changes and surface actionable signals through real-time dashboards and alerts.

---

## 🚀 What is RACEPULSE?

Modern motorsport generates multiple high-frequency data streams simultaneously:

* Vehicle telemetry
* Lap timing
* Tyre condition
* Weather and track conditions
* Pit-stop activity
* Race-control incidents
* Fan engagement
* Sponsorship exposure
* Streaming-system health

Looking at these streams independently makes it difficult to understand **what changed, why it changed, and what needs attention**.

RACEPULSE creates a streaming intelligence layer between raw event streams and decision-makers.

```text
                  RACEPULSE
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     SENSE          STREAM         ANALYZE
       │              │              │
       └──────────────┼──────────────┘
                      ↓
                  ALERT
                      ↓
                  DECIDE
```

The platform continuously transforms raw events into:

* KPIs
* Trends
* Risk signals
* Alerts
* Operational insights
* Strategic indicators
* Commercial insights
* Streaming-health metrics

---

# 🎯 Problem Statement

A modern race environment contains large volumes of rapidly changing information.

A single event can simultaneously involve:

```text
Telemetry change
      ↓
Tyre degradation
      ↓
Lap-time deterioration
      ↓
Position/gap change
      ↓
Potential strategy implication
```

At the same time:

```text
Rain
 ↓
Track wetness
 ↓
Grip reduction
 ↓
Vehicle performance change
 ↓
Tyre behavior
 ↓
Pit-window relevance
```

The challenge is not simply collecting the data.

The challenge is **connecting related events quickly enough to create useful intelligence**.

RACEPULSE addresses this using an event-driven streaming architecture.

---

# 🧠 Core Concept

RACEPULSE follows the pipeline:

```text
SOURCE
   ↓
EVENT GENERATION
   ↓
SCHEMA VALIDATION
   ↓
KAFKA STREAMING
   ↓
WINDOWING & AGGREGATION
   ↓
KPI ENGINE
   ↓
RULE EVALUATION
   ↓
ALERT GENERATION
   ↓
MYSQL ANALYTICS
   ↓
GRAFANA
```

The platform is designed around one central question:

> **What happened, why does it matter, what is affected, and what should the user investigate next?**

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │   Race Simulation    │
                         │   & Event Producers  │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
       Race Streams           Business Streams       System Events
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   Kafka + ZooKeeper  │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
             Performance        Strategy        Race Control
              Consumer          Consumer          Consumer
                    │               │                │
                    └───────────────┼────────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   Analytics Engine   │
                         │                      │
                         │ Validation           │
                         │ Windowing            │
                         │ Formula Engine       │
                         │ Rule Engine           │
                         │ Alert Engine          │
                         │ Configuration        │
                         └──────────┬───────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
                KPI / Analytics              Alerts
                       │                         │
                       ▼                         ▼
                  ┌────────┐              ┌────────────┐
                  │ MySQL  │              │   Kafka    │
                  └────┬───┘              │ Alert Topic│
                       │                  └────────────┘
                       ▼
                  ┌─────────┐
                  │ Grafana │
                  └─────────┘
```

---

# 🔄 Event-Driven Architecture

RACEPULSE uses Kafka as the central event backbone.

Core race streams include:

| Kafka Topic         | Purpose                           |
| ------------------- | --------------------------------- |
| `race.timing`       | Lap timing, position and gaps     |
| `race.telemetry`    | Vehicle telemetry                 |
| `race.tyres`        | Tyre condition and degradation    |
| `race.weather`      | Weather and track conditions      |
| `race.pitstops`     | Pit activity                      |
| `race.incidents`    | Race-control events               |
| `business.fans`     | Fan engagement                    |
| `business.sponsors` | Sponsorship activity              |
| `analytics.alerts`  | Generated alerts                  |
| `system.dlq`        | Invalid or rejected events        |
| `system.audit`      | Configuration/system audit events |

Events are keyed by the relevant entity, primarily `car_id`, to preserve ordering for each vehicle.

---

# 🏎️ Stateful Race Simulation

RACEPULSE does not rely on completely independent random records.

The simulator maintains state for:

* Race
* Car
* Driver
* Tyres
* Weather
* Track
* Telemetry
* Pit stops
* Incidents

This allows events to be causally related.

For example:

```text
RAIN
  ↓
Track Wetness ↑
  ↓
Grip ↓
  ↓
Vehicle Performance ↓
  ↓
Lap Time ↑
  ↓
Tyre Behaviour Changes
  ↓
Strategy Risk ↑
```

Similarly:

```text
Mechanical Failure
        ↓
Incident Event
        ↓
Car Retires
        ↓
Timing Events Stop
        ↓
Race Control Updates State
        ↓
Stale-Stream Monitor
understands retirement
```

This creates meaningful sequences for downstream streaming analytics.

---

# 🎬 Race Scenarios

The simulator supports controlled scenarios for testing and demonstrations.

### Normal Race

Baseline racing conditions with normal performance progression.

### 🌧️ Rain

Simulates changing weather and track conditions.

```text
Rain
 ↓
Wetness
 ↓
Grip
 ↓
Performance
 ↓
Lap Time
```

### 🛞 Tyre Crisis

Introduces accelerated tyre degradation and grip loss.

### 🚨 Safety Car

Changes race gaps and race-control state.

### 🔧 Mechanical Failure

A vehicle experiences a mechanical failure and retires from the race.

### ⚔️ Close Battle

Creates a small gap between cars to generate meaningful timing and strategy signals.

### 🏁 Pit Stop

Introduces pit-entry, tyre-change, repair and pit-exit events.

### 📈 Commercial Surge

Creates increased fan engagement and sponsorship activity.

### 💥 Data Failure

Simulates missing or unhealthy data streams.

### ⚙️ Configuration Failure

Tests invalid KPI configuration and failure-closed behavior.

---

# 📊 Analytics Engine

The analytics layer is divided into reusable components.

```text
engine/
├── validation/
├── formulas/
├── windows/
├── rules/
├── alerts/
└── config/
```

## Validation

Validates incoming events before processing.

Invalid events are routed to the DLQ rather than silently discarded.

---

## Windowing

RACEPULSE supports configurable time windows for streaming calculations.

Example:

```text
15-second tumbling window
```

Window configuration is externalized so the analytics logic does not need to be rewritten when parameters change.

---

## Formula Engine

KPIs are implemented as reusable, configurable analytical formulas.

Example:

```text
Input Events
     ↓
Window
     ↓
Formula
     ↓
KPI Result
```

---

## Rule Engine

The rule engine evaluates KPI results against configured thresholds.

```text
KPI Result
    ↓
Threshold Evaluation
    ↓
Severity
    ↓
Alert
```

This separates:

* **What is the KPI?**
* **When should it trigger?**
* **How severe is the signal?**

---

# 📈 Core KPIs

## 1. Lap Pace Delta

Measures a car's current lap pace relative to its best/reference lap.

Useful for identifying:

* Pace deterioration
* Performance changes
* Significant lap-time deviations

---

## 2. Gap Trend

Tracks the evolution of a car's gap to the leader over a rolling window.

The implementation uses asymmetric alerting:

> A widening gap is treated as a meaningful deterioration signal.

---

## 3. Tyre Degradation Rate

Measures the rate at which tyre performance deteriorates over time.

Inputs can include:

* Tyre age
* Grip
* Wear
* Pace change

---

## 4. Pit Stop Efficiency

Evaluates pit-stop execution using:

* Pit duration
* Pit activity
* Tyre change
* Repair activity

---

## 5. Average Speed

Aggregates telemetry to identify vehicle speed trends.

---

## 6. Track Risk

Combines track conditions and race-control signals to identify elevated operational risk.

---

## 7. Incident Rate

Measures incident frequency over configurable time windows.

---

## 8. Fan Engagement Rate

Measures engagement activity across the simulated fan stream.

---

## 9. Sponsor Exposure

Tracks simulated sponsorship exposure and engagement.

---

## 10. End-to-End Streaming Latency

Measures the time between event generation and analytical visibility.

```text
event_time
    ↓
Kafka
    ↓
Consumer
    ↓
Processing
    ↓
MySQL
    ↓
Grafana
```

---

# 🚨 Alerting

RACEPULSE generates structured alerts rather than simply displaying raw threshold violations.

An alert contains:

```text
Signal
Severity
Affected Entity
Timestamp
Evidence
Cause / Context
Suggested Investigation
```

Example:

```text
HIGH — TYRE RISK

Car: CAR_07
Tyre Age: 17 laps
Grip: 0.71
Pace Delta: +0.84 sec
Degradation: 0.81

Suggested Investigation:
Review current pit-window conditions.
```

Alerts are published to:

```text
analytics.alerts
```

and persisted in MySQL.

---

# 🛡️ Reliability & Failure Handling

Production-style streaming systems must handle failure explicitly.

RACEPULSE follows a **failure-closed** philosophy.

## Invalid JSON

```text
Invalid Event
     ↓
Validation Failure
     ↓
DLQ
```

## Invalid Formula

```text
Invalid Formula
     ↓
Reject New Formula
     ↓
Retain Last Valid Formula
```

## Duplicate Event

```text
Duplicate event_id
     ↓
Idempotency Check
     ↓
No duplicate analytical result
```

## Missing Stream

Missing data is represented as:

```text
NO DATA
```

rather than incorrectly treating it as:

```text
0
```

## Producer Failure

```text
Producer stops
      ↓
No new events
      ↓
Stale-stream detection
      ↓
Alert
```

Legitimate vehicle retirement is handled separately so a retired car is not incorrectly treated as a failed stream.

## Kafka / Consumer Issues

The platform is designed to expose:

* Consumer health
* Processing latency
* Consumer lag
* Error counts
* DLQ activity

for operational monitoring.

---

# 🗄️ Database Layer

MySQL stores analytical rather than raw high-frequency telemetry data.

Core analytical tables include:

```text
kpi_results
gap_trend_results
alerts
schema_migrations
```

The database layer supports:

* Idempotent writes
* Versioned migrations
* Analytical queries
* Grafana integration

Example idempotency pattern:

```text
(event_id, kpi_id)
        ↓
UNIQUE KEY
        ↓
ON DUPLICATE KEY UPDATE
```

This allows events to be replayed without creating duplicate KPI records.

---

# 📊 Grafana Dashboards

RACEPULSE is designed around multiple decision-oriented dashboards rather than one overloaded dashboard.

## 1. Executive / CEO Command Center

Answers:

> **How is the race performing overall?**

Key signals:

* Race progress
* Current leader
* Pace
* Risk
* Strategy alerts
* Incidents
* Fan engagement
* Sponsor exposure
* Streaming health

---

## 2. Race Operations Dashboard

Answers:

> **What is happening on track right now?**

Includes:

* Live positions
* Lap progression
* Gaps
* Lap pace
* Sector performance
* Flags
* Incidents
* Safety-car status

---

## 3. Strategy Dashboard

Answers:

> **What strategic signals require investigation?**

Includes:

* Tyre age
* Tyre degradation
* Grip
* Weather
* Pit stops
* Pit duration
* Pit-window indicators
* Strategy risk

---

## 4. Commercial Dashboard

Answers:

> **What is happening with audience and sponsorship activity?**

Includes:

* Viewership
* Fan engagement
* Social activity
* Sponsor impressions
* Exposure
* Commercial activity

---

## 5. Streaming Engineering Dashboard

Answers:

> **Is the RACEPULSE platform itself healthy?**

Includes:

* Events/sec
* Consumer lag
* Processing latency
* Database writes
* Errors
* DLQ count
* Producer health
* Consumer health

---

# 🔁 Live Scenario Demonstration

One of the strongest RACEPULSE demonstrations is a weather event.

For example:

```text
NORMAL RACE
     ↓
RAIN EVENT
     ↓
Weather Stream
     ↓
Track Wetness
     ↓
Grip Reduction
     ↓
Vehicle Performance
     ↓
Lap Pace Change
     ↓
Tyre Behaviour
     ↓
Strategy Signal
     ↓
Alert
     ↓
Grafana
```

The user can observe how one event propagates across multiple streaming domains.

This demonstrates that RACEPULSE is not simply displaying independent charts.

It is **correlating streams into operational intelligence**.

---

# 🔄 Replay & Scenario Testing

RACEPULSE supports repeatable scenarios for development, testing and demonstrations.

Possible modes:

```text
LIVE
SCENARIO
REPLAY
```

Replay speeds can include:

```text
1×
2×
5×
10×
```

This enables:

* Repeatable demonstrations
* Regression testing
* Formula comparison
* Failure testing
* Dashboard testing

---

# ⚙️ Dynamic Configuration

Important analytical parameters are externalized into configuration files.

```text
config/
├── parameters.yaml
├── formulas.yaml
├── thresholds.yaml
├── windows.yaml
└── schemas/
```

This allows parameters such as:

* Thresholds
* Formula weights
* Window sizes
* Scenario parameters

to be changed without rewriting the core consumer architecture.

Example:

```text
Threshold
2.0×
   ↓
2.5×
```

The system can reload valid configuration while continuing to operate.

Invalid configuration is rejected rather than replacing the last known-good configuration.

---

# 🧪 Testing Strategy

RACEPULSE uses multiple testing levels.

```text
tests/
├── unit/
├── integration/
├── failure/
└── scenarios/
```

## Unit Tests

Test individual:

* KPI formulas
* Window calculations
* Rules
* Configuration
* Event logic
* Idempotency

## Integration Tests

Test:

```text
Kafka
 ↓
Consumer
 ↓
Analytics
 ↓
MySQL
```

## Failure Tests

Test:

* Invalid events
* Duplicate events
* Invalid configuration
* Producer failures
* Stale streams
* DLQ routing

## Scenario Tests

Validate controlled race scenarios such as:

* Rain
* Tyre crisis
* Safety car
* Mechanical failure
* Close battle
* Pit stop

---

# 🐳 Technology Stack

| Technology       | Purpose                                        |
| ---------------- | ---------------------------------------------- |
| Python           | Simulation, producers, consumers and analytics |
| Apache Kafka     | Event streaming                                |
| Apache ZooKeeper | Kafka coordination                             |
| MySQL            | Analytical persistence                         |
| Grafana          | Real-time dashboards                           |
| Docker           | Infrastructure orchestration                   |
| Pytest           | Automated testing                              |
| YAML             | Configuration                                  |
| Git / GitHub     | Version control and collaboration              |

---

# 📁 Project Structure

```text
RACEPULSE/
│
├── config/
│   ├── parameters.yaml
│   ├── formulas.yaml
│   ├── thresholds.yaml
│   ├── windows.yaml
│   └── schemas/
│
├── producers/
│   ├── telemetry/
│   ├── timing/
│   ├── tyres/
│   ├── weather/
│   ├── pitstops/
│   ├── incidents/
│   ├── fans/
│   └── sponsors/
│
├── simulator/
│
├── consumers/
│   ├── performance/
│   ├── strategy/
│   ├── race_control/
│   └── commercial/
│
├── engine/
│   ├── validation/
│   ├── formulas/
│   ├── windows/
│   ├── rules/
│   ├── alerts/
│   └── config/
│
├── database/
│   ├── schema.sql
│   ├── migrations/
│   └── queries/
│
├── grafana/
│   ├── dashboards/
│   ├── queries/
│   └── provisioning/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── failure/
│   └── scenarios/
│
├── docs/
│   ├── architecture.md
│   ├── event-contract.md
│   ├── kpi-contract.md
│   ├── database-contract.md
│   ├── dashboard-contract.md
│   ├── demo-script.md
│   ├── team-work-division.md
│   └── contribution-guide.md
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🛠️ Installation

## Prerequisites

Install:

* Git
* Python 3.11+
* Docker Desktop
* Docker Compose
* VS Code or another IDE

---

# 📥 Clone the Repository

```bash
git clone https://github.com/Parv-065040/RACEPULSE.git
cd RACEPULSE
```

---

# 🐳 Start Infrastructure

```bash
docker compose up -d
```

This starts the RACEPULSE infrastructure:

```text
Kafka
ZooKeeper
MySQL
Grafana
```

Check running containers:

```bash
docker compose ps
```

---

# 🐍 Python Environment

Create a virtual environment:

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

# 🗄️ Database Setup

Run the versioned migrations:

```bash
python -m database.migrations.run_migrations
```

The migration runner tracks which migrations have already been applied.

---

# 🧪 Run Tests

Run the complete test suite:

```bash
python -m pytest -q
```

Run unit tests:

```bash
python -m pytest tests/unit -v
```

Run integration tests:

```bash
python -m pytest tests/integration -v
```

Run scenario tests:

```bash
python -m pytest tests/scenarios -v
```

Run failure tests:

```bash
python -m pytest tests/failure -v
```

---

# ▶️ Running RACEPULSE

The exact producer/consumer startup sequence is documented in:

```text
docs/demo-script.md
```

The general flow is:

```text
1. Start Docker infrastructure
        ↓
2. Apply database migrations
        ↓
3. Start race simulator
        ↓
4. Start Kafka producers
        ↓
5. Start analytics consumers
        ↓
6. Generate KPI results
        ↓
7. Persist analytical results
        ↓
8. Open Grafana
        ↓
9. Trigger scenarios
        ↓
10. Observe alerts and dashboard changes
```

---

# 🔍 Example End-to-End Flow

A simplified timing flow:

```text
Race Simulator
      ↓
Timing Producer
      ↓
race.timing
      ↓
Performance Consumer
      ↓
Lap Pace Delta
      ↓
Rule Evaluation
      ↓
Alert
      ↓
analytics.alerts
      ↓
MySQL
      ↓
Grafana
```

A strategy flow:

```text
Timing
Tyres
Weather
Pit Stops
   ↓
Strategy Consumer
   ↓
Windowing
   ↓
Tyre Degradation
   ↓
Strategy Risk
   ↓
Alert
```

A race-control flow:

```text
Telemetry
Timing
Weather
Incidents
   ↓
Race Control Consumer
   ↓
Incident / Track Risk
   ↓
Race Control Alert
```

---

# 🔐 Configuration Philosophy

RACEPULSE separates configuration from analytical logic.

Instead of hardcoding:

```python
if degradation > 0.75:
```

the system uses configuration:

```text
formula
threshold
window
severity
version
```

This makes the analytics layer easier to:

* Test
* Modify
* Demonstrate
* Version
* Audit

---

# 📐 Design Principles

## 1. Event-driven

Business and race events flow through Kafka rather than tightly coupled point-to-point communication.

## 2. Stateful simulation

Events depend on previous state rather than being independently random.

## 3. Config-driven analytics

Thresholds and analytical parameters are externalized.

## 4. Failure-closed

Invalid inputs should not silently corrupt downstream analytics.

## 5. Idempotent processing

Replay should not create duplicate analytical results.

## 6. Separation of concerns

```text
Producer
Consumer
Formula
Window
Rule
Alert
Database
Dashboard
```

have distinct responsibilities.

## 7. Observability

The platform monitors both the **race** and the **streaming system running the race intelligence**.

---

# 🎯 What RACEPULSE Can Tell Users

RACEPULSE is designed to answer questions such as:

### Performance

* Is a car's pace deteriorating?
* Is the gap to the leader widening?
* Is speed changing significantly?

### Tyres

* Are tyres degrading?
* Is degradation accelerating?
* Is grip falling?

### Weather

* Is changing weather affecting track conditions?
* Is grip changing?
* Is performance responding to those changes?

### Strategy

* Is a pit-window signal emerging?
* Is a pit stop efficient?
* Is tyre degradation becoming strategically relevant?

### Race Control

* Has an incident occurred?
* Is a vehicle at risk?
* Has a safety-car event changed race conditions?
* Has a car legitimately retired?

### Commercial

* Is fan engagement increasing?
* Is sponsorship exposure increasing?
* Is a commercial surge occurring?

### Platform Health

* Are events arriving?
* Are consumers processing them?
* Is latency increasing?
* Are events entering the DLQ?
* Has a stream become stale?

---

# 🧩 Composite Intelligence

RACEPULSE can also support configurable composite indicators such as:

* Race Risk Index
* Strategy Risk
* Driver Performance Index
* Fan Excitement Index

These are treated as **configurable analytical heuristics**, not as scientifically validated real-world racing models.

Each composite metric should document:

```text
Inputs
Weights
Normalization
Formula
Thresholds
Version
Rationale
```

---

# 👥 Team Contributions

RACEPULSE was developed as a four-member team.

| Member                       | Responsibility                     |
| ---------------------------- | ---------------------------------- |
| **Parv — 065040**            | Streaming Architecture & Analytics |
| **Awantika Kholia — 065060** | Race Simulation & Core Producers   |
| **Navroop — 065039**         | Reliability & Business Streams     |
| **Yashi Tiwari — 065054**    | Grafana & Business Intelligence    |

---

## Parv — Streaming Architecture & Analytics

Primary areas:

```text
consumers/
engine/
database/
config/
tests/
```

Key responsibilities:

* Streaming consumer architecture
* KPI engine
* Windowing
* Rules
* Alerts
* MySQL analytical layer
* Configuration
* Reliability integration
* Integration testing

---

## Awantika Kholia — Race Simulation & Core Producers

Primary areas:

```text
simulator/
producers/
tests/scenarios/
```

Key responsibilities:

* Stateful race simulation
* Timing producer
* Telemetry producer
* Tyre producer
* Weather producer
* Pit-stop producer
* Incident producer
* Race scenarios

Her contribution establishes the simulation-to-streaming layer, where race state is converted into related Kafka event streams.

---

## Navroop — Reliability & Business Streams

Primary areas:

```text
engine/validation/
producers/fans/
producers/sponsors/
tests/failure/
```

Key responsibilities:

* Extended event validation
* Failure handling
* Fan streams
* Sponsorship streams
* Failure-injection testing

---

## Yashi Tiwari — Grafana & Business Intelligence

Primary areas:

```text
grafana/
grafana/dashboards/
grafana/queries/
grafana/provisioning/
```

Key responsibilities:

* Grafana dashboards
* Business intelligence views
* Executive dashboard
* Strategy dashboard
* Commercial dashboard
* Streaming engineering dashboard

---

# 🌿 Git Workflow

RACEPULSE uses a protected integration workflow.

```text
develop
   ↓
feature/<member>-<task>
   ↓
Build
   ↓
Test
   ↓
Commit
   ↓
Push
   ↓
Pull Request
   ↓
Review
   ↓
Merge → develop
   ↓
Final Integration
   ↓
main
```

No direct development should be performed on `main`.

Feature branches should be deleted after successful merge.

---

# 📚 Documentation

Detailed technical documentation is maintained in:

```text
docs/
```

Important documents:

| Document                | Purpose                     |
| ----------------------- | --------------------------- |
| `architecture.md`       | System architecture         |
| `event-contract.md`     | Kafka event schemas         |
| `kpi-contract.md`       | KPI definitions             |
| `database-contract.md`  | Database structures         |
| `dashboard-contract.md` | Dashboard specifications    |
| `demo-script.md`        | Demonstration sequence      |
| `team-work-division.md` | Ownership and collaboration |
| `contribution-guide.md` | Development workflow        |

---

# 🎓 Academic / Learning Value

RACEPULSE demonstrates multiple concepts from modern data engineering and analytics:

* Event-driven architecture
* Apache Kafka
* Streaming data processing
* Stateful event simulation
* Windowed aggregation
* KPI engineering
* Rule-based alerting
* Data validation
* Dead-letter queues
* Idempotency
* Database persistence
* Configuration management
* Observability
* Dashboard engineering
* Failure testing
* Git-based collaboration
* Containerized infrastructure

---

# ⚠️ Scope & Limitations

RACEPULSE uses simulated race data for educational and demonstration purposes.

It is **not** intended to replace:

* Professional race engineers
* Official timing systems
* FIA/race-control systems
* Validated motorsport strategy software
* Real-world safety-critical systems

The analytical formulas and composite indicators are configurable project models and should not be interpreted as validated real-world racing algorithms.

---

# 🔮 Future Extensions

Potential future work includes:

### Advanced Anomaly Detection

Machine-learning models for detecting unusual telemetry patterns.

### AI Race Explanations

Natural-language explanations of correlated race events.

Example:

> "CAR_07's pace deteriorated during the last three windows while tyre grip declined and track wetness increased."

### External Data Sources

Integration with real-time external racing APIs.

### Advanced Strategy Modeling

Simulation of alternative pit strategies.

### Automated KPI Generation

Controlled generation and registration of new analytical metrics.

### Venue Operations

Integration of:

* Crowd movement
* Entry/exit flows
* Parking
* Concessions
* Venue incidents

---

# 🏁 The RACEPULSE Philosophy

RACEPULSE is built around a simple idea:

> **Raw streaming data is not intelligence.**

The value comes from transforming:

```text
Events
  ↓
Context
  ↓
Patterns
  ↓
Signals
  ↓
Alerts
  ↓
Decision Support
```

The platform therefore focuses on connecting events across domains instead of simply displaying more data.

---

# 📌 One-Line Summary

**RACEPULSE is a real-time event-driven motorsport intelligence platform that converts race, operational, and commercial data streams into configurable KPIs, alerts, and decision-support dashboards using Kafka, Python, MySQL, Docker, and Grafana.**

---

# ⭐ Project Status

**Architecture:** Production-style streaming architecture
**Streaming:** Apache Kafka
**Processing:** Python consumers + configurable analytics engine
**Persistence:** MySQL
**Visualization:** Grafana
**Infrastructure:** Docker
**Testing:** Pytest
**Simulation:** Stateful multi-scenario race simulator

The final release is intended to provide a complete:

```text
SIMULATE
   ↓
STREAM
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
INVESTIGATE
```

pipeline for real-time motorsport event intelligence.

---

## 👨‍💻 Built by the RACEPULSE Team

**FORE School of Management, New Delhi**

PGDM — Big Data Analytics

**Parv · Awantika Kholia · Navroop · Yashi Tiwari**

---

> 🏎️ **RACEPULSE — From Race Events to Real-Time Intelligence.**
