from copy import deepcopy

from simulator.scenario import (
    ScenarioConfig,
    ScenarioType,
    create_scenario,
)
from simulator.state import RaceState


class RaceSimulator:
    def __init__(
        self,
        race: RaceState | None = None,
        scenario: ScenarioConfig | None = None,
    ) -> None:
        self.race = race or RaceState.create_default()
        self.scenario = scenario or create_scenario()
        self.current_lap = 0
        self._apply_scenario()

    def _apply_scenario(self) -> None:
        if self.scenario.name == ScenarioType.RAIN:
            self.race.weather.update(
                self.scenario.rain_intensity
            )

        if self.scenario.name == ScenarioType.TYRE_CRISIS:
            for car in self.race.cars.values():
                car.tyre.degradation_per_lap = (
                    self.scenario.tyre_degradation_per_lap
                )

        if self.scenario.name == ScenarioType.SAFETY_CAR:
            self._apply_safety_car()

        if self.scenario.name == ScenarioType.CLOSE_BATTLE:
            self._apply_close_battle()

    def _apply_safety_car(self) -> None:
        for car in self.race.cars.values():
            car.gap_to_leader_ms = int(
                car.gap_to_leader_ms
                * self.scenario.safety_car_gap_factor
            )
            car.gap_change_ms_per_lap = 0

            car.incident.incident_type = "SAFETY_CAR"
            car.incident.active = True
            car.incident.severity = "MEDIUM"
            car.incident.description = (
                "Safety car deployed on the track."
            )

    def _apply_close_battle(self) -> None:
        for car in self.race.cars.values():
            if car.position == 1:
                car.gap_to_leader_ms = 0
                car.gap_change_ms_per_lap = 0
            else:
                car.gap_to_leader_ms = (
                    self.scenario.close_battle_gap_ms
                )

                if car.car_id == "CAR_02":
                    car.gap_change_ms_per_lap = (
                        self.scenario.close_battle_gap_change_ms
                    )
                else:
                    car.gap_change_ms_per_lap = (
                        -self.scenario.close_battle_gap_change_ms
                    )

    def _reset_pit_stop_state(self) -> None:
        for car in self.race.cars.values():
            car.pitstop.pit_entry = False
            car.pitstop.pit_stop = False
            car.pitstop.tyre_change = False
            car.pitstop.repair = False
            car.pitstop.pit_exit = False

    def _apply_mechanical_failure(self) -> None:
        if (
            self.scenario.name
            != ScenarioType.MECHANICAL_FAILURE
        ):
            return

        if (
            self.current_lap
            != self.scenario.mechanical_failure_lap
        ):
            return

        car_id = self.scenario.mechanical_failure_car_id

        if car_id not in self.race.cars:
            return

        car = self.race.get_car(car_id)

        car.incident.incident_type = "MECHANICAL_FAILURE"
        car.incident.active = True
        car.incident.severity = "HIGH"
        car.incident.description = (
            "Mechanical failure caused the car to retire."
        )

        self.race.fail_car(car_id)

    def _apply_pit_stop(self) -> None:
        self._reset_pit_stop_state()

        if self.scenario.name != ScenarioType.PIT_STOP:
            return

        if self.current_lap != self.scenario.pitstop_lap:
            return

        car_id = self.scenario.pitstop_car_id

        if car_id not in self.race.cars:
            return

        car = self.race.get_car(car_id)

        car.pitstop.pit_entry = True
        car.pitstop.pit_stop = True
        car.pitstop.tyre_change = True
        car.pitstop.repair = False
        car.pitstop.pit_exit = True

    def advance_one_lap(self):
        self.current_lap += 1

        self._apply_mechanical_failure()
        self._apply_pit_stop()

        return self.race.simulate_all_cars_next_lap()

    def advance_laps(self, laps: int):
        if laps < 1:
            raise ValueError("laps must be at least 1")

        history = []

        for _ in range(laps):
            cars = self.advance_one_lap()
            snapshot = [
                deepcopy(car)
                for car in cars
            ]
            history.append(snapshot)

        return history


def create_simulator(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> RaceSimulator:
    return RaceSimulator(
        scenario=create_scenario(scenario)
    )


if __name__ == "__main__":
    simulator = create_simulator(
        ScenarioType.MECHANICAL_FAILURE
    )

    print(
        f"Scenario: "
        f"{simulator.scenario.name.value}"
    )

    print(
        f"Failure car: "
        f"{simulator.scenario.mechanical_failure_car_id}"
    )

    print(
        f"Failure lap: "
        f"{simulator.scenario.mechanical_failure_lap}"
    )

    print()

    for lap_number, cars in enumerate(
        simulator.advance_laps(5),
        start=1,
    ):
        print(f"LAP {lap_number}")

        for car in cars:
            print(
                car.car_id,
                "lap=",
                car.lap_number,
                "lap_time_ms=",
                car.lap_time_ms,
                "running=",
                car.is_running,
            )

        failed_car = simulator.race.get_car(
            simulator.scenario.mechanical_failure_car_id
        )

        print(
            "CAR_03 status:",
            "RUNNING"
            if failed_car.is_running
            else "FAILED",
            "| last_lap=",
            failed_car.lap_number,
            "| incident=",
            failed_car.incident.incident_type,
            "| active=",
            failed_car.incident.active,
        )

        print()