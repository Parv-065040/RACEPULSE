from dataclasses import dataclass


@dataclass
class PitStopState:
    pit_entry: bool = False
    pit_stop: bool = False
    tyre_change: bool = False
    repair: bool = False
    pit_exit: bool = False


def create_default_pitstop() -> PitStopState:
    return PitStopState()