# RACEPULSE — Database Contract

Owner: Parv (Streaming Architecture & Analytics). This is the source of
truth for every table's shape and purpose. Update this file whenever a
migration adds or changes a table — the two should never drift apart.

Schema is managed as versioned migrations under `database/migrations/`,
applied in filename order via `python -m database.migrations.run_migrations`
(tracked in a `schema_migrations` table so re-running is always safe).
Do not hand-edit tables directly in MySQL outside of a migration file —
that defeats the point of having a tracked, reproducible schema.

---

## `kpi_results`

Stores every KPI-001 (Lap Pace Delta) computation, one row per
`(event_id, kpi_id)` pair.

| Column | Type | Notes |
|---|---|---|
| id | BIGINT, auto-increment | Primary key |
| kpi_id | VARCHAR(20) | Always `KPI-001` currently |
| event_id | VARCHAR(36) | The source Kafka event's UUID — this is the idempotency key |
| car_id | VARCHAR(20) | e.g. `CAR_01` |
| lap_number | INT | |
| lap_time_ms | INT | |
| best_lap_time_ms | INT | Best lap time for this car so far in the race, as of this computation |
| delta_ms | INT | `lap_time_ms - best_lap_time_ms` (can be negative if this lap IS the new best) |
| severity | VARCHAR(10) | `none`, `warning`, or `critical` |
| event_time | DATETIME(3) | Event-time (when the lap actually happened), not processing-time |
| computed_at | TIMESTAMP | When this row was written/last updated |

**Unique key:** `(event_id, kpi_id)` — a replayed or duplicate Kafka
message overwrites the same row (`ON DUPLICATE KEY UPDATE`) instead of
inserting a second one. Proven via replay testing (see project notes).

**Written by:** `database/writer.py :: write_kpi_result()`

---

## `gap_trend_results`

Stores every KPI-002 (Gap Trend) computation, one row per
`(event_id, kpi_id)` pair.

| Column | Type | Notes |
|---|---|---|
| id | BIGINT, auto-increment | Primary key |
| kpi_id | VARCHAR(20) | Always `KPI-002` currently |
| event_id | VARCHAR(36) | Idempotency key, same convention as `kpi_results` |
| car_id | VARCHAR(20) | |
| lap_number | INT | |
| gap_to_leader_ms | INT | Raw gap value for this lap (0 for the race leader) |
| trend_ms_per_lap | FLOAT | Average per-lap change in gap over the rolling window. Positive = falling behind, negative = catching up |
| severity | VARCHAR(10) | `none` or `warning`/`critical` — only ever non-`none` for a *positive* (widening) trend |
| event_time | DATETIME(3) | |
| computed_at | TIMESTAMP | |

**Unique key:** `(event_id, kpi_id)` — same idempotency pattern.

**Written by:** `database/writer.py :: write_gap_trend_result()`

**Note:** kept as a separate table from `kpi_results` rather than a
shared generic table, since `trend_ms_per_lap` (a float, can be
negative) isn't the same kind of value as `delta_ms` (an int) — forcing
both into one table would mean nullable columns for whichever KPI
didn't apply, which is worse than two small, clearly-typed tables.

---

## `alerts`

Stores every alert raised — both KPI-severity alerts (from KPI-001 or
KPI-002 crossing `warning`/`critical`) and infrastructure alerts (e.g.
`SYS-STALE` from stale-stream detection).

| Column | Type | Notes |
|---|---|---|
| id | BIGINT, auto-increment | Primary key |
| kpi_id | VARCHAR(20) | `KPI-001`, `KPI-002`, or `SYS-STALE` for non-KPI infra alerts |
| event_id | VARCHAR(36) | For KPI alerts, the source event's UUID. For `SYS-STALE`, a freshly generated UUID (there is no source event — the alert IS the absence of one) |
| car_id | VARCHAR(20) | |
| severity | VARCHAR(10) | Currently always `warning` or `critical` — alerts are never raised for `none` |
| message | VARCHAR(255) | Human-readable summary, e.g. `"Car CAR_03 lap pace delta 1540ms (CRITICAL) vs best 90020ms"` |
| delta_ms | INT | For `SYS-STALE` alerts, this holds `seconds_since_last_seen * 1000` (reusing the column rather than adding a stale-specific one) |
| event_time | DATETIME(3) | |
| created_at | TIMESTAMP | |

**Unique key:** `(event_id, kpi_id)` — same idempotency pattern as the
other two tables.

**Written by:** `engine/alerts/alert_engine.py` (`raise_alert_if_needed`
for KPI alerts, `raise_stale_stream_alert` for `SYS-STALE`)

**Known gotcha (already hit and fixed):** early on, `SYS-STALE`
`event_id` values embedded a full ISO timestamp and overflowed
`VARCHAR(36)` (sized for a UUID). Fixed by generating a real UUID for
stale alerts too, same as normal events. If anyone adds a new kind of
non-KPI alert, generate its `event_id` the same way — don't build a
custom string ID.

---

## `schema_migrations`

Internal bookkeeping table, not a data table. Created automatically by
`database/migrations/run_migrations.py` the first time it runs. Records
which migration files have been applied so re-running the script is
always safe.

| Column | Type | Notes |
|---|---|---|
| filename | VARCHAR(255) | Primary key, e.g. `001_create_kpi_results.sql` |
| applied_at | TIMESTAMP | |

---

## Adding a new table — checklist

1. Add a new numbered file under `database/migrations/` (e.g.
   `004_create_<name>.sql`), following the naming pattern of the
   existing three.
2. Run `python -m database.migrations.run_migrations` to apply it.
3. Document the new table here, in the same format as above.
4. If Yashi's dashboards will query it, add an example query under
   `database/queries/` (see the four examples already there for the
   expected style — one query per file, a comment explaining the
   intended Grafana panel).
