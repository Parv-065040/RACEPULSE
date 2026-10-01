from dataclasses import dataclass
from pathlib import Path

import yaml


CONFIG_PATH = Path("config/weather.yaml")


@dataclass(frozen=True)
class WeatherPhase:
    name: str
    start_lap: int
    end_lap: int
    rain_intensity: float
    air_temperature_c: float
    track_temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    visibility_km: float


@dataclass(frozen=True)
class WeatherPhysics:
    wetness_rain_gain: float
    wetness_drying_rate: float
    minimum_drying_grip: float
    maximum_wetness: float
    grip_loss_factor: float


@dataclass(frozen=True)
class WeatherConfig:
    enabled: bool
    race_laps: int
    phases: tuple[WeatherPhase, ...]
    physics: WeatherPhysics


def _validate_phase(phase: WeatherPhase) -> None:
    if not phase.name:
        raise ValueError("weather phase name cannot be empty")

    if phase.start_lap < 1:
        raise ValueError("weather phase start_lap must be >= 1")

    if phase.end_lap < phase.start_lap:
        raise ValueError(
            f"weather phase {phase.name}: end_lap must be >= start_lap"
        )

    if not 0.0 <= phase.rain_intensity <= 1.0:
        raise ValueError(
            f"weather phase {phase.name}: rain_intensity must be 0..1"
        )

    if not 0.0 <= phase.humidity_pct <= 100.0:
        raise ValueError(
            f"weather phase {phase.name}: humidity_pct must be 0..100"
        )

    if phase.visibility_km <= 0:
        raise ValueError(
            f"weather phase {phase.name}: visibility_km must be > 0"
        )


def _validate_config(config: WeatherConfig) -> None:
    if config.race_laps < 1:
        raise ValueError("race_laps must be >= 1")

    if not config.phases:
        raise ValueError("weather configuration must contain phases")

    sorted_phases = sorted(
        config.phases,
        key=lambda phase: phase.start_lap,
    )

    expected_start = 1

    for phase in sorted_phases:
        _validate_phase(phase)

        if phase.start_lap != expected_start:
            raise ValueError(
                "weather phases must cover every race lap "
                f"without gaps; expected lap {expected_start}, "
                f"got {phase.start_lap}"
            )

        expected_start = phase.end_lap + 1

    if expected_start != config.race_laps + 1:
        raise ValueError(
            "weather phases must cover the configured race length"
        )

    physics = config.physics

    if not 0.0 <= physics.wetness_rain_gain <= 1.0:
        raise ValueError("wetness_rain_gain must be 0..1")

    if not 0.0 <= physics.wetness_drying_rate <= 1.0:
        raise ValueError("wetness_drying_rate must be 0..1")

    if not 0.0 <= physics.minimum_drying_grip <= 1.0:
        raise ValueError("minimum_drying_grip must be 0..1")

    if not 0.0 <= physics.maximum_wetness <= 1.0:
        raise ValueError("maximum_wetness must be 0..1")

    if not 0.0 <= physics.grip_loss_factor <= 1.0:
        raise ValueError("grip_loss_factor must be 0..1")


def load_weather_config(
    path: Path = CONFIG_PATH,
) -> WeatherConfig:
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError("weather configuration must be a mapping")

    weather = raw.get("weather")

    if not isinstance(weather, dict):
        raise ValueError("missing 'weather' configuration")

    phases_raw = weather.get("phases")

    if not isinstance(phases_raw, list):
        raise ValueError("weather.phases must be a list")

    phases = tuple(
        WeatherPhase(
            name=str(item["name"]),
            start_lap=int(item["start_lap"]),
            end_lap=int(item["end_lap"]),
            rain_intensity=float(item["rain_intensity"]),
            air_temperature_c=float(item["air_temperature_c"]),
            track_temperature_c=float(item["track_temperature_c"]),
            humidity_pct=float(item["humidity_pct"]),
            wind_speed_kmh=float(item["wind_speed_kmh"]),
            visibility_km=float(item["visibility_km"]),
        )
        for item in phases_raw
    )

    physics_raw = weather.get("physics")

    if not isinstance(physics_raw, dict):
        raise ValueError("missing 'weather.physics' configuration")

    config = WeatherConfig(
        enabled=bool(weather.get("enabled", True)),
        race_laps=int(weather["race_laps"]),
        phases=phases,
        physics=WeatherPhysics(
            wetness_rain_gain=float(
                physics_raw["wetness_rain_gain"]
            ),
            wetness_drying_rate=float(
                physics_raw["wetness_drying_rate"]
            ),
            minimum_drying_grip=float(
                physics_raw["minimum_drying_grip"]
            ),
            maximum_wetness=float(
                physics_raw["maximum_wetness"]
            ),
            grip_loss_factor=float(
                physics_raw["grip_loss_factor"]
            ),
        ),
    )

    _validate_config(config)

    return config


def get_weather_phase(
    lap_number: int,
    config: WeatherConfig | None = None,
) -> WeatherPhase:
    if lap_number < 1:
        raise ValueError("lap_number must be >= 1")

    config = config or load_weather_config()

    for phase in config.phases:
        if phase.start_lap <= lap_number <= phase.end_lap:
            return phase

    raise ValueError(
        f"no weather phase configured for lap {lap_number}"
    )
