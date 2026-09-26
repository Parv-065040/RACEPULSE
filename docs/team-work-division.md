# RACEPULSE — Team Work Division & Collaboration Contract

**Project:** RACEPULSE — Real-Time Motorsport Event Intelligence & Race Operations Platform

**Status:** Development
**Primary Branch:** `develop`
**Final Release Branch:** `main`

---

# 1. Purpose

This document is the **official team ownership and collaboration contract** for RACEPULSE.

It defines:

* Team responsibilities
* Module ownership
* File ownership
* Shared components
* Dependencies
* Git workflow
* Pull-request rules
* Testing requirements
* Integration rules
* Collaboration between team members and their LLM assistants

If another document conflicts with this file regarding **team ownership or Git workflow**, this document takes precedence.

Technical architecture and KPI definitions may be updated through the appropriate project contracts in `docs/`.

---

# 2. Team

| Member              |     ID | Primary Area                       |
| ------------------- | -----: | ---------------------------------- |
| **Parv Jhamb**      | 065040 | Streaming Architecture & Analytics |
| **Awantika Kholia** | 065060 | Race Simulation & Core Producers   |
| **Navroop**         | 065039 | Reliability & Business Streams     |
| **Yashi Tiwari**    | 065054 | Grafana & Business Intelligence    |

---

# 3. Core Architecture

All team members must understand the complete pipeline:

```text
Race Simulation
      ↓
Data Producers
      ↓
Kafka + ZooKeeper
      ↓
Stream Consumers
      ↓
KPI / Rule Engine
      ↓
Alerts / Analytical Results
      ↓
MySQL
      ↓
Grafana
```

Product philosophy:

```text
SENSE
  ↓
STREAM
  ↓
ANALYZE
  ↓
ALERT
  ↓
DECIDE
```

---

# 4. Global Ownership Rules

## Rule 1 — Ownership does not mean isolation

Each member owns their area but must understand how it connects to the rest of the system.

## Rule 2 — Do not duplicate work

Before creating a new file, class, service, topic, schema, query, or configuration:

1. Search the repository.
2. Check this document.
3. Check the relevant contract in `docs/`.
4. Reuse an existing component if appropriate.

## Rule 3 — Do not randomly redesign the architecture

Major architectural changes must be discussed with the team before implementation.

## Rule 4 — Shared interfaces must be agreed upon

If one member's work produces data consumed by another member, the interface must be documented before implementation.

## Rule 5 — Never silently modify another member's core module

If a change is required in another member's module:

* Discuss it.
* Explain why.
* Coordinate the change.
* Include the relevant owner in the PR/review.

## Rule 6 — `develop` is the integration branch

Nobody should directly develop on `develop`.

## Rule 7 — `main` is the final release branch

`main` should remain stable and receive the final project only after testing and review.

---

# 5. Git Workflow

## Branches

```text
main
develop
feature/<member>-<task>
```

Examples:

```text
feature/parv-kpi-engine
feature/awantika-race-simulator
feature/navroop-validation-dlq
feature/yashi-grafana-dashboard
```

## Workflow

```text
develop
   ↓
Create feature branch
   ↓
Implement
   ↓
Test
   ↓
Push feature branch
   ↓
Pull Request → develop
   ↓
Review
   ↓
Merge
   ↓
Delete feature branch
```

## Important rules

* No direct development on `main`.
* No direct development on `develop`.
* Every meaningful feature should use a feature branch.
* Pull Requests should be reviewed before merging.
* Feature branches should be deleted after successful merge.
* Keep commits focused and meaningful.

---

# 6. Commit Convention

Use clear commit messages.

Examples:

```text
feat: add telemetry producer
feat: implement tyre degradation KPI
feat: add DLQ validation
feat: create strategy dashboard

fix: handle duplicate events
fix: correct tyre degradation calculation

test: add KPI engine tests

docs: update event contract

chore: update docker configuration
```

Avoid:

```text
update
changes
final
final2
working
test123
```

---

# 7. Parv — Streaming Architecture & Analytics

## Primary ownership

Parv owns the core streaming-processing and analytical layer.

### Main responsibilities

* Kafka architecture
* Consumer framework
* KPI engine
* Formula engine
* Windowing
* Rule evaluation
* Alert generation
* Configuration handling
* MySQL analytical layer
* Integration testing

---

## Primary directories

```text
consumers/
engine/
database/
config/
tests/integration/
```

---

## Initial file ownership

Parv is primarily responsible for files such as:

```text
consumers/performance/
consumers/strategy/
consumers/race_control/

engine/formulas/
engine/windows/
engine/rules/
engine/alerts/
engine/config/

database/schema.sql
database/migrations/
database/queries/

config/formulas.yaml
config/thresholds.yaml
config/windows.yaml
```

Exact filenames inside these directories will be finalized through the relevant contracts.

---

## Parv's key outputs

Parv's components should provide:

```text
Raw Kafka Events
      ↓
Validated/Processed Data
      ↓
Windowed Metrics
      ↓
KPIs
      ↓
Rules
      ↓
Alerts
      ↓
MySQL
```

---

# 8. Awantika — Race Simulation & Core Producers

## Primary ownership

Awantika owns the stateful race simulation and core race-data generation.

### Main responsibilities

* Race state
* Car state
* Driver state
* Tyre state
* Weather state
* Track state
* Telemetry
* Timing
* Tyres
* Weather
* Pit stops
* Incidents
* Race scenarios

---

## Primary directories

```text
simulator/

producers/telemetry/
producers/timing/
producers/tyres/
producers/weather/
producers/pitstops/
producers/incidents/

tests/scenarios/
```

---

## Core principle

The simulator must be **stateful and causal**, not just a collection of independent random values.

Example:

```text
Rain
 ↓
Track Wetness
 ↓
Grip
 ↓
Vehicle Performance
 ↓
Lap Time
 ↓
Tyre Behaviour
 ↓
Strategy Signal
```

Randomness can be used for realism, but important values should be derived from the underlying race state.

---

# 9. Navroop — Reliability & Business Streams

## Primary ownership

Navroop owns reliability, validation and commercial data streams.

### Reliability responsibilities

* Schema validation
* Event validation
* Dead Letter Queue
* Duplicate detection
* Idempotency
* Stale-stream detection
* Producer health
* Consumer health
* Failure handling
* Audit events

### Business responsibilities

* Fan engagement stream
* Sponsorship stream
* Commercial KPIs

---

## Primary directories

```text
producers/fans/
producers/sponsors/

engine/validation/

tests/failure/
```

Navroop also collaborates with Parv on:

```text
system.dlq
system.audit
```

---

## Required failure cases

The system should safely handle:

```text
Invalid JSON
Missing fields
Wrong data types
Unknown entities
Duplicate events
Producer failure
Consumer lag
Invalid configuration
```

A malformed event must not crash the complete pipeline.

---

# 10. Yashi — Grafana & Business Intelligence

## Primary ownership

Yashi owns the visualization and dashboard layer.

### Main responsibilities

* Grafana dashboards
* Grafana queries
* Dashboard variables
* Visualization
* Dashboard alerts
* Dashboard QA
* Business interpretation of KPIs

---

## Primary directories

```text
grafana/dashboards/
grafana/queries/
grafana/provisioning/
```

---

# 11. Dashboard Ownership

## CEO Command Center

Answers:

```text
Are we performing?
Are we safe?
Is strategy under pressure?
Is there a commercial signal?
Is streaming healthy?
```

---

## Race Operations

Shows:

* Live positions
* Lap progression
* Gaps
* Lap pace
* Sector performance
* Flags
* Incidents
* Safety car

---

## Strategy

Shows:

* Tyre age
* Tyre degradation
* Grip
* Pit stops
* Pit duration
* Weather
* Track wetness
* Pit-window indicators
* Strategy risk

---

## Commercial

Shows:

* Viewers
* Engagement
* Social activity
* Sponsor impressions
* Sponsor exposure
* Clicks
* Conversions

---

## Streaming Engineering

Shows:

* Events/sec
* Kafka throughput
* Consumer lag
* Processing latency
* Database writes
* Errors
* DLQ
* Producer health
* Consumer health

---

# 12. Shared Responsibilities

Some components cannot belong to only one person.

## Kafka

**Primary:** Parv
**Producers:** Awantika / Navroop
**Consumers:** Parv
**Monitoring:** Yashi + Parv

---

## Configuration

**Primary:** Parv

All members must use the shared configuration system rather than creating private configuration files.

---

## Event Schemas

**Shared responsibility**

* Awantika: race event structures
* Navroop: business/reliability event structures
* Parv: processing requirements
* Yashi: dashboard requirements

Final schemas are documented in:

```text
docs/event-contract.md
```

---

## KPIs

**Primary:** Parv

Other members contribute domain requirements.

Final KPI definitions belong in:

```text
docs/kpi-contract.md
```

---

## Database

**Primary:** Parv

Yashi provides dashboard query requirements.

Final database definitions belong in:

```text
docs/database-contract.md
```

---

## Grafana

**Primary:** Yashi

Parv provides the analytical outputs required by dashboards.

Final dashboard definitions belong in:

```text
docs/dashboard-contract.md
```

---

# 13. Shared Contracts

The following documents are project-level sources of truth:

```text
docs/architecture.md
docs/event-contract.md
docs/kpi-contract.md
docs/database-contract.md
docs/dashboard-contract.md
```

Before changing an interface, check the relevant contract.

If a contract needs to change:

1. Discuss the change.
2. Update the contract.
3. Update affected implementation.
4. Update tests.
5. Mention the change in the PR.

---

# 14. File Ownership Principle

Ownership is primarily based on directories.

```text
AWANTIKA
├── simulator/
└── producers/
    ├── telemetry/
    ├── timing/
    ├── tyres/
    ├── weather/
    ├── pitstops/
    └── incidents/

NAVROOP
├── engine/validation/
└── producers/
    ├── fans/
    └── sponsors/

PARV
├── consumers/
├── engine/
│   ├── formulas/
│   ├── windows/
│   ├── rules/
│   ├── alerts/
│   └── config/
├── database/
└── config/

YASHI
└── grafana/
```

This is the **default ownership map**.

Cross-module changes still require coordination.

---

# 15. Testing Ownership

## Parv

Owns:

* KPI tests
* Consumer tests
* Integration tests
* Database integration

## Awantika

Owns:

* Simulator tests
* Producer tests
* Scenario tests
* State consistency tests

## Navroop

Owns:

* Validation tests
* Failure tests
* DLQ tests
* Duplicate/idempotency tests
* Commercial producer tests

## Yashi

Owns:

* Dashboard QA
* Query validation
* Visualization correctness
* Dashboard refresh testing

Everyone is responsible for testing their own code.

---

# 16. Integration Rules

Before opening a PR:

```text
Code
 ↓
Local Test
 ↓
Integration Test where applicable
 ↓
Git Status
 ↓
Commit
 ↓
Push
 ↓
Pull Request
```

A PR should explain:

```text
What changed?
Why?
Files changed?
Dependencies?
How was it tested?
Does another teammate need to review anything?
```

---

# 17. No Breaking Changes Without Coordination

Do not silently change:

* Kafka topic names
* Event fields
* Field types
* KPI names
* KPI formulas
* Database columns
* Database table names
* Configuration keys
* Dashboard data sources

Such changes can break another teammate's work.

Coordinate first.

---

# 18. Baby-Step Development Rule

Every member should work incrementally.

Recommended cycle:

```text
Understand
 ↓
Create one small component
 ↓
Run it
 ↓
Verify it
 ↓
Test it
 ↓
Commit it
 ↓
Integrate
 ↓
Continue
```

Do not build an entire subsystem before testing the basic interface.

---

# 19. LLM Collaboration Rule

Each team member may use an LLM as a coding assistant.

However, the LLM must:

1. Read the project documentation.
2. Inspect the existing repository.
3. Read the relevant contracts.
4. Check this team-work document.
5. Identify the member's ownership.
6. Reuse existing files/interfaces.
7. Avoid duplicate implementations.
8. Make small changes.
9. Test changes.
10. Explain the implementation.

The LLM must **not independently redesign RACEPULSE**.

---

# 20. What LLMs Must Never Do

An LLM must not:

* Create a competing architecture.
* Create duplicate Kafka topics.
* Create duplicate KPI engines.
* Create duplicate configuration systems.
* Rename shared interfaces without coordination.
* Modify another member's core module unnecessarily.
* Dump a complete untested subsystem.
* Assume a feature works without testing.
* Replace project conventions with personal preferences.
* Invent data contracts.
* Invent database structures that conflict with `docs/database-contract.md`.

---

# 21. Definition of Done

A feature is complete only when:

* Code works.
* Tests pass.
* Required Kafka integration works.
* Required MySQL integration works.
* Required Grafana integration works.
* Errors are handled.
* Documentation is updated.
* The owner understands the implementation.
* Another teammate can understand the interface.
* The feature survives a clean restart where applicable.

---

# 22. P0 / P1 / P2 Priority

## P0 — Mandatory

```text
Kafka
ZooKeeper
MySQL
Grafana

Telemetry
Timing
Tyres
Weather
Pit Stops
Incidents

Windowed analytics
KPI engine
Configuration
Alerts
Validation

Core dashboards
```

## P1 — Differentiation

```text
Fan Engagement
Sponsorship
Scenario Engine
Replay Mode
Formula Versioning
Audit Trail
Commercial Dashboard
```

## P2 — Stretch

```text
Venue Operations
Automatic KPI Creation
External APIs
AI Explanations
Advanced Anomaly Detection
```

**Never sacrifice P0 stability for P1/P2 features.**

---

# 23. Final Git Strategy

During development:

```text
main
  ↓
Final stable release only

develop
  ↓
Integration branch

feature/*
  ↓
Individual member work
```

At project completion:

```text
All feature branches
        ↓
develop
        ↓
Final testing
        ↓
Final documentation
        ↓
Final demo validation
        ↓
Pull Request
        ↓
main
```

After the final project is accepted and stable, `main` becomes the final submission/release version.

---

# 24. Final Team Principle

RACEPULSE is one system, not four separate projects.

Every member should think:

```text
MY MODULE
    ↓
TEAM INTERFACE
    ↓
RACEPULSE
```

The goal is not simply to complete individual assignments.

The goal is to produce one coherent, reliable, demonstrable streaming analytics platform.

**SENSE → STREAM → ANALYZE → ALERT → DECIDE**
