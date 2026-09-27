from dataclasses import dataclass


@dataclass
class WeatherState:
    condition: str = "DRY"
    rain_intensity: float = 0.0
    track_wetness: float = 0.0
    track_grip: float = 1.0

    def update(self, rain_intensity: float) -> "WeatherState":
        self.rain_intensity = max(0.0, min(1.0, rain_intensity))

        if self.rain_intensity == 0.0:
            self.condition = "DRY"
        elif self.rain_intensity < 0.4:
            self.condition = "LIGHT_RAIN"
        else:
            self.condition = "HEAVY_RAIN"

        self.track_wetness = min(
            1.0,
            self.track_wetness + self.rain_intensity * 0.2,
        )

        if self.rain_intensity == 0.0:
            self.track_wetness = max(
                0.0,
                self.track_wetness - 0.05,
            )

        self.track_grip = max(
            0.0,
            1.0 - (self.track_wetness * 0.5),
        )

        return self


def create_default_weather() -> WeatherState:
    return WeatherState(
        condition="DRY",
        rain_intensity=0.0,
        track_wetness=0.0,
        track_grip=1.0,
    )