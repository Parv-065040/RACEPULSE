from dataclasses import dataclass


@dataclass
class TyreState:
    compound: str
    age_laps: int = 0
    wear: float = 0.0
    grip: float = 1.0
    degradation_per_lap: float = 0.02

    def complete_lap(self) -> "TyreState":
        self.age_laps += 1
        self.wear = min(1.0, self.wear + self.degradation_per_lap)
        self.grip = max(0.0, 1.0 - self.wear)

        return self


def create_default_tyre() -> TyreState:
    return TyreState(
        compound="MEDIUM",
        age_laps=0,
        wear=0.0,
        grip=1.0,
        degradation_per_lap=0.02,
    )