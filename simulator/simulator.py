from copy import deepcopy

from engine.config.weather_loader import (
    WeatherConfig,
    get_weather_phase,
    load_weather_config,
)
from simulator.pit_strategy import (
    PitStrategyConfig,
    evaluate_pit_decision,
    load_pit_strategy_config,
)
from simulator.lap_snapshot import RaceLapSnapshot
from simulator.scenario import (
    ScenarioConfig,
    ScenarioType,
    create_scenario,
)
from simulator.state import RaceState


PIT_STOP_PENALTY_MS = 22000


class RaceSimulator:
    def __init__(
        self,
        race: RaceState | None = None,
        scenario: ScenarioConfig | None = None,
        weather_config: WeatherConfig | None = None,
        pit_strategy_config: PitStrategyConfig | None = None,
    ) -> None:
        self.race = race or RaceState.create_default()
        self.scenario = scenario or create_scenario()
        self.weather_config = weather_config or load_weather_config()
        self.pit_strategy_config = (
            pit_strategy_config or load_pit_strategy_config()
        )

        self.current_lap = 0
        self.snapshot_history: list[RaceLapSnapshot] = []

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


    def _apply_safety_car(self) -> None:
        for car in self.race.cars.values():
            if car.car_id == "CAR_01":
                car.gap_to_leader_ms = 0
            else:
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

    def _advance_weather(self) -> None:
        """Advance weather using the configured phase and weather physics."""
        if self.scenario.name == ScenarioType.RAIN:
            self.race.weather.update(
                self.scenario.rain_intensity,
                air_temperature_c=self.race.weather.air_temperature_c,
                track_temperature_c=self.race.weather.track_temperature_c,
                humidity_pct=self.race.weather.humidity_pct,
                wind_speed_kmh=self.race.weather.wind_speed_kmh,
                visibility_km=self.race.weather.visibility_km,
                wetness_rain_gain=self.weather_config.physics.wetness_rain_gain,
                wetness_drying_rate=0.0,
                maximum_wetness=self.weather_config.physics.maximum_wetness,
                grip_loss_factor=self.weather_config.physics.grip_loss_factor,
            )
            self.race.weather.condition = "RAIN"
            return

        phase = get_weather_phase(
            self.current_lap,
            self.weather_config,
        )

        self.race.weather.apply_phase(
            phase,
            self.weather_config,
        )
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

    def _perform_pit_stop(self, car) -> None:
        car.pitstop.pit_entry = True
        car.pitstop.pit_stop = True
        car.pitstop.tyre_change = True
        car.pitstop.repair = False
        car.pitstop.pit_exit = True

        # Record persistent strategy history.
        car.pitstop.pit_stop_count += 1
        car.pitstop.last_pit_lap = self.current_lap
        car.pitstop.total_pit_loss_ms += (
            self.pit_strategy_config.pit_lane_loss_ms
        )
        car.pitstop.last_compound = car.tyre.compound

        # Fit a fresh tyre.
        car.tyre.age_laps = 0
        car.tyre.wear = 0.0
        car.tyre.grip = 1.0

        # Apply pit-lane loss only to this lap.
        car.pit_time_loss_ms = (
            self.pit_strategy_config.pit_lane_loss_ms
        )

    def _apply_explicit_pit_stop(self) -> None:
        if self.scenario.name != ScenarioType.PIT_STOP:
            return

        if self.current_lap != self.scenario.pitstop_lap:
            return

        car_id = self.scenario.pitstop_car_id

        if car_id not in self.race.cars:
            return

        self._perform_pit_stop(
            self.race.get_car(car_id)
        )

    def _apply_strategic_pit_stops(self, cars):
        """Apply configurable strategic pit decisions during a normal race."""
        if self.scenario.name != ScenarioType.NORMAL_RACE:
            return

        for car in cars:
            pit_state = car.pitstop

            laps_since_last_stop = (
                car.lap_number - pit_state.last_pit_lap
                if pit_state.last_pit_lap > 0
                else car.lap_number
            )

            should_stop, reason = evaluate_pit_decision(
                lap_number=car.lap_number,
                tyre_age=car.tyre.age_laps,
                tyre_wear=car.tyre.wear,
                tyre_management=car.tyre_management,
                wet_weather_performance=car.wet_weather_performance,
                weather_condition=self.race.weather.condition,
                pit_stop_count=pit_state.pit_stop_count,
                laps_since_last_stop=laps_since_last_stop,
                config=self.pit_strategy_config,
            )

            pit_state.last_decision = "PIT" if should_stop else "CONTINUE"
            pit_state.last_decision_reason = reason
            pit_state.last_decision_lap = car.lap_number + 1

            if should_stop:
                self._perform_pit_stop(car)

    def _apply_pit_stop(self, cars) -> None:
        self._reset_pit_stop_state()

        if self.scenario.name == ScenarioType.PIT_STOP:
            self._apply_explicit_pit_stop()
            return

        self._apply_strategic_pit_stops(cars)
    def _update_race_ranking(self) -> None:
        """Update race positions and gaps using the canonical race-state ranking."""
        self.race.update_ranking()
    def _capture_lap_snapshots(self, cars):
        """Capture immutable historical state after each completed lap."""
        snapshots = []

        for car in cars:
            snapshots.append(
                RaceLapSnapshot(
                    lap=car.lap_number,
                    weather_condition=self.race.weather.condition,
                    rain_intensity=self.race.weather.rain_intensity,
                    track_wetness=self.race.weather.track_wetness,
                    track_grip=self.race.weather.track_grip,
                    car_id=car.car_id,
                    position=car.position,
                    gap_to_leader_ms=car.gap_to_leader_ms,
                    lap_time_ms=car.lap_time_ms,
                    race_time_ms=car.race_time_ms,
                    tyre_age=car.tyre.age_laps,
                    tyre_wear=car.tyre.wear,
                    tyre_grip=car.tyre.grip,
                    tyre_compound=car.tyre.compound,
                    pit_stop=car.pitstop.pit_stop,
                    pit_stop_count=car.pitstop.pit_stop_count,
                    last_pit_lap=car.pitstop.last_pit_lap,
                    total_pit_loss_ms=car.pitstop.total_pit_loss_ms,
                    strategy_decision=car.pitstop.last_decision,
                    strategy_decision_reason=car.pitstop.last_decision_reason,
                    strategy_decision_lap=car.pitstop.last_decision_lap,
                    is_running=car.is_running,
                )
            )

        self.snapshot_history.extend(snapshots)

    def advance_one_lap(self):
        self.current_lap += 1

        self._advance_weather()
        self._apply_mechanical_failure()

        cars = list(self.race.cars.values())

        self._apply_pit_stop(cars)

        cars = self.race.simulate_all_cars_next_lap()

        self._update_race_ranking()

        if self.scenario.name == ScenarioType.SAFETY_CAR:
            for car in cars:
                if car.car_id == "CAR_01":
                    car.gap_to_leader_ms = 0
                else:
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

        elif self.scenario.name == ScenarioType.CLOSE_BATTLE:
            self._apply_close_battle()

        self._capture_lap_snapshots(cars)

        return cars
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

        print(
            "Weather:",
            simulator.race.weather.condition,
            "| rain=",
            simulator.race.weather.rain_intensity,
            "| wetness=",
            round(simulator.race.weather.track_wetness, 3),
            "| grip=",
            round(simulator.race.weather.track_grip, 3),
        )

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
            f"{simulator.scenario.mechanical_failure_car_id} status:",
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






















