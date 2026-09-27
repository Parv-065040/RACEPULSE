from simulator.scenario import ScenarioConfig, ScenarioType, create_scenario
from simulator.state import RaceState


class RaceSimulator:
    """
    Controls the progression of the synthetic race.

    RaceSimulator owns the simulation loop while RaceState
    owns the actual race data and state transitions.
    """

    def __init__(
        self,
        race: RaceState | None = None,
        scenario: ScenarioConfig | None = None,
    ) -> None:
        self.race = race or RaceState.create_default()
        self.scenario = scenario or create_scenario()

    def advance_one_lap(self):
        """
        Advance every car by one simulated lap.

        Returns:
            list of updated CarState objects.
        """
        return self.race.simulate_all_cars_next_lap()

    def advance_laps(self, laps: int):
        """
        Advance the race by multiple laps.

        Args:
            laps: Number of laps to simulate.

        Returns:
            List of lists containing the car states for each lap.
        """
        if laps < 1:
            raise ValueError("laps must be at least 1")

        history = []

        for _ in range(laps):
            cars = self.advance_one_lap()
            history.append(cars)

        return history


def create_simulator(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> RaceSimulator:
    """Create a simulator with the selected race scenario."""
    return RaceSimulator(
        scenario=create_scenario(scenario),
    )


if __name__ == "__main__":
    simulator = create_simulator(ScenarioType.NORMAL_RACE)

    print(f"Scenario: {simulator.scenario.name.value}")

    for lap_number, cars in enumerate(
        simulator.advance_laps(3),
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
                "tyre_age=",
                car.tyre.age_laps,
                "track_grip=",
                round(simulator.race.weather.track_grip, 2),
            )

        print()