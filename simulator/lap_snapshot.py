from dataclasses import dataclass


@dataclass(frozen=True)
class RaceLapSnapshot:
    lap: int
    weather_condition: str
    rain_intensity: float
    track_wetness: float
    track_grip: float

    car_id: str
    position: int
    gap_to_leader_ms: int
    lap_time_ms: int
    race_time_ms: int

    tyre_age: int
    tyre_wear: float
    tyre_grip: float
    tyre_compound: str

    pit_stop: bool
    pit_stop_count: int
    last_pit_lap: int
    total_pit_loss_ms: int

    is_running: bool

    # Strategy telemetry is optional for backward compatibility.
    strategy_decision: str = "CONTINUE"
    strategy_decision_reason: str = ""
    strategy_decision_lap: int = 0
