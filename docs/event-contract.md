# RACEPULSE — Event Contract

> STATUS: DRAFT. `race.timing`, `race.telemetry`, and `race.tyres` are defined as
> draft contracts. These sections need team review before being treated as final.

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