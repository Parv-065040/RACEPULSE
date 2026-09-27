from dataclasses import dataclass, field


@dataclass
class CarState:
    car_id: str
    lap_number: int = 0
    lap_time_ms: int = 90000
    gap_to_leader_ms: int = 0
    position: int = 1


@dataclass
class RaceState:
    cars: dict[str, CarState] = field(default_factory=dict)

    def add_car(self, car: CarState) -> None:
        self.cars[car.car_id] = car

    def get_car(self, car_id: str) -> CarState:
        return self.cars[car_id]

    def complete_lap(
        self,
        car_id: str,
        lap_time_ms: int,
        gap_to_leader_ms: int,
        position: int,
    ) -> CarState:
        car = self.get_car(car_id)

        car.lap_number += 1
        car.lap_time_ms = lap_time_ms
        car.gap_to_leader_ms = max(0, gap_to_leader_ms)
        car.position = position

        return car