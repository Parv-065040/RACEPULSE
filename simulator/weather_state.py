from dataclasses import dataclass

from engine.config.weather_loader import (
    WeatherConfig,
    WeatherPhase,
    load_weather_config,
)


@dataclass
class WeatherState:
    condition: str = "DRY"
    rain_intensity: float = 0.0
    track_wetness: float = 0.0
    track_grip: float = 1.0

    air_temperature_c: float = 29.0
    track_temperature_c: float = 42.0
    humidity_pct: float = 48.0
    wind_speed_kmh: float = 12.0
    visibility_km: float = 10.0

    def update(
        self,
        rain_intensity: float,
        *,
        air_temperature_c: float | None = None,
        track_temperature_c: float | None = None,
        humidity_pct: float | None = None,
        wind_speed_kmh: float | None = None,
        visibility_km: float | None = None,
        wetness_rain_gain: float = 0.20,
        wetness_drying_rate: float = 0.08,
        maximum_wetness: float = 1.0,
        grip_loss_factor: float = 0.50,
    ) -> "WeatherState":

        self.rain_intensity = max(
            0.0,
            min(1.0, rain_intensity),
        )

        if self.rain_intensity == 0.0:
            if self.track_wetness > 0.0:
                self.condition = "DRYING_TRACK"
            else:
                self.condition = "DRY"
        elif self.rain_intensity < 0.4:
            self.condition = "LIGHT_RAIN"
        elif self.rain_intensity < 0.7:
            self.condition = "RAIN"
        else:
            self.condition = "HEAVY_RAIN"

        if self.rain_intensity > 0.0:
            self.track_wetness = min(
                maximum_wetness,
                self.track_wetness
                + self.rain_intensity * wetness_rain_gain,
            )
        else:
            self.track_wetness = max(
                0.0,
                self.track_wetness - wetness_drying_rate,
            )

        self.track_grip = max(
            0.0,
            1.0 - (
                self.track_wetness * grip_loss_factor
            ),
        )

        if air_temperature_c is not None:
            self.air_temperature_c = air_temperature_c

        if track_temperature_c is not None:
            self.track_temperature_c = track_temperature_c

        if humidity_pct is not None:
            self.humidity_pct = humidity_pct

        if wind_speed_kmh is not None:
            self.wind_speed_kmh = wind_speed_kmh

        if visibility_km is not None:
            self.visibility_km = visibility_km

        return self

    def apply_phase(
        self,
        phase: WeatherPhase,
        config: WeatherConfig,
    ) -> "WeatherState":

        physics = config.physics

        self.update(
            phase.rain_intensity,
            air_temperature_c=phase.air_temperature_c,
            track_temperature_c=phase.track_temperature_c,
            humidity_pct=phase.humidity_pct,
            wind_speed_kmh=phase.wind_speed_kmh,
            visibility_km=phase.visibility_km,
            wetness_rain_gain=physics.wetness_rain_gain,
            wetness_drying_rate=physics.wetness_drying_rate,
            maximum_wetness=physics.maximum_wetness,
            grip_loss_factor=physics.grip_loss_factor,
        )

        # The configured weather phase is authoritative.
        # Rain intensity controls physical effects, while the phase
        # name controls the semantic race-weather state.
        self.condition = phase.name

        return self


def create_default_weather() -> WeatherState:
    config = load_weather_config()
    phase = config.phases[0]

    state = WeatherState()

    state.apply_phase(
        phase,
        config,
    )

    return state
