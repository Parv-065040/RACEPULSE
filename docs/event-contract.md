# RACEPULSE — Event Contract

> STATUS: DRAFT. Only `race.timing` is defined so far, by Parv, to unblock
> consumer development. Needs review with Awantika before being treated as final.

## Topic: race.timing

Emitted per lap completion, per car.

```json
{
  "event_id": "uuid",
  "event_time": "2026-09-26T10:15:30.000Z",
  "car_id": "string",
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
| lap_time_ms | integer | Lap time in milliseconds |
| gap_to_leader_ms | integer | 0 if this car is the leader |
| position | integer | 1-indexed running position |
**Partitioning:** Keyed by car_id to preserve per-car lap ordering across partitions.
