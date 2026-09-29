# RACEPULSE — Event Contract

> STATUS: DRAFT. `race.timing`, `race.telemetry`, `race.tyres`, `race.weather`,
> `race.pitstops`, `race.incidents`, `business.fans` and `business.sponsors` are
> defined as draft contracts. These sections need team review before being
> treated as final. `business.*` drafted by Navroop - review: Parv (processing),
> Yashi (dashboard fields).

## Topic: race.timing

Emitted per lap completion, per car.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "lap_time_ms": 91234,
  "gap_to_leader_ms": 0,
  "position": 1
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | e.g. "CAR_01" |
| lap_number | integer | 1-indexed |
| lap_time_ms | integer | Completed lap time in milliseconds |
| gap_to_leader_ms | integer | Gap to race leader in milliseconds |
| position | integer | Current race position |

**Partitioning:** Keyed by car_id to preserve per-car lap ordering across partitions.

## Topic: race.telemetry

Emitted per lap completion, per car.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "speed_kmh": 210.0,
  "rpm": 9000,
  "throttle_pct": 80.0,
  "brake_pct": 0.0,
  "gear": 7,
  "engine_temperature_c": 95.0,
  "brake_temperature_c": 450.0,
  "battery_temperature_c": 40.0,
  "fuel_kg": 100.0,
  "energy_kwh": 4.0,
  "location_km": 0.0
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | e.g. "CAR_01" |
| lap_number | integer | Current lap number |
| speed_kmh | number | Vehicle speed in km/h |
| rpm | integer | Engine RPM |
| throttle_pct | number | Throttle percentage |
| brake_pct | number | Brake percentage |
| gear | integer | Current gear |
| engine_temperature_c | number | Engine temperature in Celsius |
| brake_temperature_c | number | Brake temperature in Celsius |
| battery_temperature_c | number | Battery temperature in Celsius |
| fuel_kg | number | Remaining fuel in kilograms |
| energy_kwh | number | Remaining energy in kWh |
| location_km | number | Simulated track location in kilometres |

**Partitioning:** Keyed by car_id to preserve per-car telemetry ordering across partitions.

## Topic: race.tyres

Emitted per lap completion, per car.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "compound": "MEDIUM",
  "age_laps": 1,
  "wear": 0.02,
  "grip": 0.98,
  "degradation_per_lap": 0.02
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | e.g. "CAR_01" |
| lap_number | integer | Current lap number |
| compound | string | Tyre compound |
| age_laps | integer | Tyre age in completed laps |
| wear | number | Tyre wear, from 0.0 to 1.0 |
| grip | number | Current tyre grip, from 0.0 to 1.0 |
| degradation_per_lap | number | Tyre degradation per lap |

**Partitioning:** Keyed by car_id to preserve per-car tyre ordering across partitions.

## Topic: race.weather

Emitted per lap, per car, using the current race weather and track state.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "condition": "DRY",
  "rain_intensity": 0.0,
  "track_wetness": 0.0,
  "track_grip": 1.0
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | e.g. "CAR_01" |
| lap_number | integer | Current lap number |
| condition | string | Current weather condition |
| rain_intensity | number | Rain intensity, from 0.0 to 1.0 |
| track_wetness | number | Track wetness, from 0.0 to 1.0 |
| track_grip | number | Track grip, from 0.0 to 1.0 |

**Partitioning:** Keyed by car_id to preserve per-car weather event ordering across partitions.

## Topic: race.pitstops

Emitted per lap, per car.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "pit_entry": false,
  "pit_stop": false,
  "tyre_change": false,
  "repair": false,
  "pit_exit": false
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | e.g. "CAR_01" |
| lap_number | integer | Current lap number |
| pit_entry | boolean | Whether the car entered the pit lane |
| pit_stop | boolean | Whether a pit stop occurred |
| tyre_change | boolean | Whether tyres were changed |
| repair | boolean | Whether a repair was performed |
| pit_exit | boolean | Whether the car exited the pit lane |

**Partitioning:** Keyed by car_id to preserve per-car pit-stop ordering across partitions.

## Topic: race.incidents

Emitted when an active race incident occurs.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_03",
  "lap_number": 3,
  "incident_type": "MECHANICAL_FAILURE",
  "active": true,
  "severity": "HIGH",
  "description": "Mechanical failure caused the car to retire."
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | Car associated with the incident |
| lap_number | integer | Lap on which the incident occurred |
| incident_type | string | Type of race incident |
| active | boolean | Whether the incident is active |
| severity | string | Incident severity |
| description | string | Human-readable incident description |

**Partitioning:** Keyed by car_id to preserve per-car incident ordering across partitions.

## Topic: business.fans

DRAFT (Navroop) - review: Parv, Yashi.

Emitted per lap, per running car. Raw engagement counts for that lap; derived
metrics (e.g. Fan Engagement Rate) are computed downstream, not by the producer.
A retired car emits nothing (no data is not zero).

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "viewers": 62755,
  "app_sessions": 18826,
  "searches": 3137,
  "likes": 7604,
  "comments": 1255,
  "shares": 627,
  "merch_clicks": 313
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | Car (driver/team) the engagement is attributed to |
| lap_number | integer | Lap the counts refer to |
| viewers | integer, >= 0 | Simulated viewers attributed to this car this lap |
| app_sessions | integer, >= 0 | Fan-app sessions |
| searches | integer, >= 0 | Searches |
| likes | integer, >= 0 | Likes |
| comments | integer, >= 0 | Comments |
| shares | integer, >= 0 | Shares |
| merch_clicks | integer, >= 0 | Merchandise link clicks |

**Simulation note:** counts follow race state (position, rain, active incident,
close gap, pit stop, `COMMERCIAL_SURGE`) via `producers/fans/excitement.py`.
The weights are simulation heuristics, not validated marketing metrics.

**Partitioning:** Keyed by car_id to preserve per-car ordering across partitions.

## Topic: business.sponsors

DRAFT (Navroop) - review: Parv, Yashi.

Emitted per lap, per running car. Each car carries one sponsor's livery
(`CAR_01`->`SPONSOR_01`, `CAR_02`->`SPONSOR_02`, `CAR_03`->`SPONSOR_03`).

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "CAR_01",
  "lap_number": 1,
  "sponsor_id": "SPONSOR_01",
  "impressions": 65766,
  "visibility_seconds": 26.9,
  "clicks": 247,
  "conversions": 19
}
```

| Field | Type | Notes |
|---|---|---|
| event_id | string (UUID) | For idempotency/duplicate detection |
| event_time | ISO 8601 timestamp | Event-time, not processing-time |
| car_id | string | Car carrying the sponsor's livery |
| lap_number | integer | Lap the counts refer to |
| sponsor_id | string | e.g. "SPONSOR_01" |
| impressions | integer, >= 0 | Simulated impressions this lap |
| visibility_seconds | number, >= 0 | Seconds the livery was visible on broadcast this lap |
| clicks | integer, >= 0 | Must be <= impressions |
| conversions | integer, >= 0 | Must be <= clicks |

**Partitioning:** Keyed by car_id (not sponsor_id) so business and race events
join on the same key and keep per-car ordering.

## Validation rules (engine/validation/)

Owner: Navroop. Schemas live in `engine/validation/schemas.py` and must match
the sections above; change both in the same PR.

| Failure | Behaviour |
|---|---|
| Invalid JSON / non-object JSON | Rejected, sent to `system.dlq` |
| Missing field, wrong type (a boolean is not a number), out-of-range value, bad UUID, bad timestamp | Rejected, sent to `system.dlq` |
| Unknown `car_id` / `sponsor_id` | Rejected, sent to `system.dlq` |
| Cross-field violation (`clicks > impressions`, `conversions > clicks`) | Rejected, sent to `system.dlq` |
| Duplicate `event_id` on the same topic | Dropped and counted (not a DLQ case) |
| Extra unknown fields | Tolerated |

DLQ record shape (unchanged, from `engine/validation/dlq.py`):
`{source_topic, failed_at, key, raw_value, errors}`. `raw_value` is always a JSON
object: an unparseable payload is wrapped as `{"_unparseable_payload": "<text>"}`.
