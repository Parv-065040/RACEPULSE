from dataclasses import dataclass


@dataclass
class PitStopState:
    pit_entry: bool = False
    pit_stop: bool = False
    tyre_change: bool = False
    repair: bool = False
    pit_exit: bool = False

    # Persistent race-strategy metrics.
    pit_stop_count: int = 0
    last_pit_lap: int = 0
    total_pit_loss_ms: int = 0
    last_compound: str = ""

    # Strategy decision telemetry.
    last_decision: str = "CONTINUE"
    last_decision_reason: str = ""
    last_decision_lap: int = 0


def create_default_pitstop() -> PitStopState:
    return PitStopState()
