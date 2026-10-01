"""Validated loader for the RACEPULSE car-grid configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


CONFIG_PATH = Path("config/cars.yaml")

_REQUIRED_FIELDS = {
    "name",
    "pace_ms",
    "starting_gap_ms",
    "starting_position",
    "degradation_ms_per_lap",
    "gap_change_ms_per_lap",
    "top_speed_kmh",
    "acceleration_factor",
    "tyre_management",
    "fuel_efficiency",
    "wet_weather_performance",
    "mechanical_reliability",
    "aggression",
    "sponsor_id",
}


@dataclass(frozen=True)
class CarConfig:
    car_id: str
    name: str
    pace_ms: int
    starting_gap_ms: int
    starting_position: int
    degradation_ms_per_lap: int
    gap_change_ms_per_lap: int
    top_speed_kmh: int
    acceleration_factor: float
    tyre_management: float
    fuel_efficiency: float
    wet_weather_performance: float
    mechanical_reliability: float
    aggression: float
    sponsor_id: str


def _validate_car(car_id: str, raw: dict) -> None:
    if not isinstance(raw, dict):
        raise ValueError(f"{car_id}: configuration must be a mapping")

    missing = _REQUIRED_FIELDS - raw.keys()
    if missing:
        raise ValueError(
            f"{car_id}: missing required fields: {sorted(missing)}"
        )

    if raw["starting_position"] < 1:
        raise ValueError(f"{car_id}: starting_position must be >= 1")

    if raw["pace_ms"] <= 0:
        raise ValueError(f"{car_id}: pace_ms must be > 0")

    if raw["starting_gap_ms"] < 0:
        raise ValueError(f"{car_id}: starting_gap_ms must be >= 0")

    if raw["degradation_ms_per_lap"] < 0:
        raise ValueError(
            f"{car_id}: degradation_ms_per_lap must be >= 0"
        )

    if raw["top_speed_kmh"] <= 0:
        raise ValueError(f"{car_id}: top_speed_kmh must be > 0")

    # Acceleration is a multiplier, so values around 1.0 are expected.
    if not 0.8 <= float(raw["acceleration_factor"]) <= 1.2:
        raise ValueError(
            f"{car_id}: acceleration_factor must be between 0.8 and 1.2"
        )

    # These characteristics are normalized scores.
    for field in (
        "tyre_management",
        "fuel_efficiency",
        "wet_weather_performance",
        "mechanical_reliability",
        "aggression",
    ):
        value = float(raw[field])
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{car_id}: {field} must be between 0 and 1"
            )


def load_car_configs() -> list[CarConfig]:
    """Load and validate every configured race car."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Car configuration not found: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict) or not isinstance(raw.get("cars"), dict):
        raise ValueError(
            "config/cars.yaml must contain a top-level 'cars' mapping"
        )

    cars = raw["cars"]

    if not cars:
        raise ValueError("config/cars.yaml contains no cars")

    configs = []

    for car_id, car_data in cars.items():
        _validate_car(car_id, car_data)

        configs.append(
            CarConfig(
                car_id=car_id,
                name=str(car_data["name"]),
                pace_ms=int(car_data["pace_ms"]),
                starting_gap_ms=int(car_data["starting_gap_ms"]),
                starting_position=int(car_data["starting_position"]),
                degradation_ms_per_lap=int(
                    car_data["degradation_ms_per_lap"]
                ),
                gap_change_ms_per_lap=int(
                    car_data["gap_change_ms_per_lap"]
                ),
                top_speed_kmh=int(car_data["top_speed_kmh"]),
                acceleration_factor=float(
                    car_data["acceleration_factor"]
                ),
                tyre_management=float(
                    car_data["tyre_management"]
                ),
                fuel_efficiency=float(
                    car_data["fuel_efficiency"]
                ),
                wet_weather_performance=float(
                    car_data["wet_weather_performance"]
                ),
                mechanical_reliability=float(
                    car_data["mechanical_reliability"]
                ),
                aggression=float(car_data["aggression"]),
                sponsor_id=str(car_data["sponsor_id"]),
            )
        )

    positions = [car.starting_position for car in configs]

    if len(positions) != len(set(positions)):
        raise ValueError(
            "Duplicate starting positions in car configuration"
        )

    configs.sort(key=lambda car: car.starting_position)

    return configs


def get_car_config(car_id: str) -> CarConfig:
    """Return the configuration for one car."""
    for config in load_car_configs():
        if config.car_id == car_id:
            return config

    raise KeyError(f"Unknown configured car: {car_id}")


def get_known_car_ids() -> set[str]:
    """Return the configured car IDs."""
    return {config.car_id for config in load_car_configs()}
