from dataclasses import dataclass, field


@dataclass
class CarState:
    car_id: str
    lap_number: int = 0
    lap_time_ms: int = 90000
    gap_to_leader_ms: int = 0
    position: int = 1
    degradation_ms_per_lap: int = 100


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

    def simulate_next_lap(self, car_id: str) -> CarState:
        car = self.get_car(car_id)

        lap_time_ms = car.lap_time_ms + car.degradation_ms_per_lap
        gap_to_leader_ms = car.gap_to_leader_ms

        return self.complete_lap(
            car_id=car_id,
            lap_time_ms=lap_time_ms,
            gap_to_leader_ms=gap_to_leader_ms,
            position=car.position,
        )

    def simulate_all_cars_next_lap(self) -> list[CarState]:
        updated_cars = []

        for car_id in self.cars:
            updated_car = self.simulate_next_lap(car_id)
            updated_cars.append(updated_car)

        return updated_cars

    @classmethod
    def create_default(cls) -> "RaceState":
        race = cls()

        cars = [
            CarState(
                car_id="CAR_01",
                lap_time_ms=90000,
                gap_to_leader_ms=0,
                position=1,
                degradation_ms_per_lap=150,
            ),
            CarState(
                car_id="CAR_02",
                lap_time_ms=91200,
                gap_to_leader_ms=3000,
                position=2,
                degradation_ms_per_lap=80,
            ),
            CarState(
                car_id="CAR_03",
                lap_time_ms=89800,
                gap_to_leader_ms=5000,
                position=3,
                degradation_ms_per_lap=220,
            ),
        ]

        for car in cars:
            race.add_car(car)

        return race