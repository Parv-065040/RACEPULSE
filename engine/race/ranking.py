from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RankingResult:
    car_id: str
    position: int
    gap_to_leader_ms: int


class RaceRanking:
    """
    Calculates race position and gap from cumulative race time.

    Lower cumulative race time means a better race position.
    Retired cars are excluded from active ranking.
    """

    def update(self, cars: Iterable[object]) -> list[RankingResult]:
        active_cars = [
            car
            for car in cars
            if getattr(car, "is_running", True)
        ]

        if not active_cars:
            return []

        ordered = sorted(
            active_cars,
            key=lambda car: (
                getattr(car, "race_time_ms", 0),
                car.car_id,
            ),
        )

        leader_time = int(ordered[0].race_time_ms)
        results: list[RankingResult] = []

        for position, car in enumerate(ordered, start=1):
            gap = max(
                0,
                int(car.race_time_ms) - leader_time,
            )

            car.position = position
            car.gap_to_leader_ms = gap

            results.append(
                RankingResult(
                    car_id=car.car_id,
                    position=position,
                    gap_to_leader_ms=gap,
                )
            )

        return results
