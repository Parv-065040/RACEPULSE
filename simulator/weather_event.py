from datetime import datetime, timezone
from uuid import uuid4

from simulator.weather_state import WeatherState


def build_weather_event(
    weather: WeatherState,
    car_id: str,
    lap_number: int,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car_id,
        "lap_number": lap_number,
        "condition": weather.condition,
        "rain_intensity": weather.rain_intensity,
        "track_wetness": weather.track_wetness,
        "track_grip": weather.track_grip,
    }