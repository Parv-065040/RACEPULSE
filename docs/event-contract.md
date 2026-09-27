# RACEPULSE — Event Contract

> STATUS: DRAFT. `race.timing`, `race.telemetry`, `race.tyres`, `race.weather`,
> `race.pitstops`, and `race.incidents` are defined as draft contracts. These
> sections need team review before being treated as final.

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