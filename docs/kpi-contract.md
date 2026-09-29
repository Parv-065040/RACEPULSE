# RACEPULSE — KPI Contract

Owner: Parv (Streaming Architecture & Analytics). This is the source of
truth for every KPI's formula, inputs, thresholds, and versioning.
Update this file whenever a KPI's formula or thresholds change in
`config/thresholds.yaml` — the two should never drift apart.

---

## KPI-001 — Lap Pace Delta

| Field | Value |
|---|---|
| KPI ID | KPI-001 |
| Name | Lap Pace Delta |
| Description | Difference between a car's current lap time and its best lap time so far this race |
| Formula | `current_lap_time_ms - best_lap_time_ms_so_far` |
| Input fields | `lap_time_ms` (from `race.timing`) |
| Window | None — cumulative best-so-far, per car, for the whole race |
| Unit | milliseconds |
| Severity | `warning` at `delta_ms >= warning_ms` (default 500ms), `critical` at `delta_ms >= critical_ms` (default 1500ms) |
| State | In-memory dict keyed by `car_id`, tracking each car's best lap time. Not persisted — resets if the consumer restarts (known limitation; see "Open items" below) |
| Enabled | Yes |
| Version | 1 |
| Owning module | `engine/formulas/lap_pace_delta.py` |
| Output table | `kpi_results` |

**Interpretation:** A positive, growing delta means the car is getting
slower relative to its own best lap — a sign of tyre degradation,
traffic, or a driver mistake. A delta near or below 0 means the car
just set (or matched) its fastest lap of the race.

---

## KPI-002 — Gap Trend

| Field | Value |
|---|---|
| KPI ID | KPI-002 |
| Name | Gap Trend |
| Description | Average change in gap-to-leader per lap, over a rolling window of recent laps |
| Formula | `(gap_to_leader_ms[latest] - gap_to_leader_ms[oldest_in_window]) / (laps_in_window - 1)` |
| Input fields | `gap_to_leader_ms` (from `race.timing`) |
| Window | Rolling last 3 laps (configurable via `window_size`) |
| Unit | milliseconds per lap |
| Severity | **Asymmetric by design.** Only a *widening* gap (positive trend) can alert: `warning` at `>= widening_warning_ms_per_lap` (default 200), `critical` at `>= widening_critical_ms_per_lap` (default 400). A *narrowing* gap (car catching up) is always `none`, regardless of magnitude — that's good news, not an alert condition. |
| State | Rolling window per car (`engine/windows/RollingWindow`), holding the last N `gap_to_leader_ms` values |
| Enabled | Yes |
| Version | 1 |
| Owning module | `engine/formulas/gap_trend.py` |
| Output table | `gap_trend_results` |

**Interpretation:** A consistently positive trend means the car is
losing ground to the race leader lap over lap — worth flagging to race
strategy. A negative trend means the car is closing the gap. The
leader itself always shows `gap_to_leader_ms = 0` and `trend = 0`.

---

## Adding a new KPI — checklist

When adding KPI-003 or beyond, follow this pattern (established by
KPI-001/KPI-002) so the whole engine stays consistent:

1. Add a new top-level block to `config/thresholds.yaml` with `kpi_id`,
   `name`, `description`, `formula`, `input_fields`, `window`, `unit`,
   `severity_thresholds`, `enabled`, `version`.
2. Add validation for the new block's thresholds in
   `engine/config/loader.py`'s `_validate()` (e.g. warning < critical),
   and add the new top-level key to `REQUIRED_TOP_LEVEL_KEYS`.
3. Create `engine/formulas/<new_kpi>.py`. Read live thresholds via
   `engine.config.loader.get_config()` — never hardcode or read the
   YAML file directly from a formula module.
4. If the KPI needs a rolling window, use `engine.windows.RollingWindow`
   rather than a new ad hoc `deque`.
5. If the KPI needs severity classification, use
   `engine.rules.severity_rules.evaluate_severity()` unless the KPI has
   genuinely different severity logic (like KPI-002's asymmetry) — in
   which case document the difference here, explicitly, like the
   asymmetric note above.
6. Add a MySQL table for its results (see `database-contract.md`) and
   a `write_<kpi>_result()` function in `database/writer.py`.
7. Wire it into `consumers/performance/timing_consumer.py` (or the
   relevant consumer) alongside the existing KPI calls.
8. Add unit tests under `tests/unit/test_<new_kpi>.py`, mocking
   `get_config` the same way `test_lap_pace_delta.py` and
   `test_gap_trend.py` do.
9. Document it in this file, in the same table format as above.

## Open items (not yet resolved)

- KPI-001's `_best_lap_by_car` state is in-memory only. If the consumer
  restarts mid-race, each car's "best lap" resets to whatever lap comes
  in first after restart, rather than remembering the true best. Not
  currently a problem for demo purposes (the consumer isn't expected to
  restart mid-run), but worth flagging if the project moves toward
  genuine fault tolerance later.
- Only two KPIs exist so far, both in the "performance" domain fed by
  `race.timing`. No strategy-domain or commercial-domain KPIs exist yet
  — those depend on producers (tyres, weather, pitstops, fans,
  sponsors) that haven't been built by the rest of the team yet.
