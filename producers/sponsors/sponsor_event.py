"""
Sponsor-exposure event builder.

Sponsor assignment is configuration-driven through config/cars.yaml.
SPONSOR_BY_CAR is retained as a public compatibility mapping because
existing tests and modules import it.
"""

import random
from datetime import datetime, timezone
from uuid import uuid4

from engine.config.car_loader import get_car_config, load_car_configs
from producers.fans.excitement import excitement_factor


SPONSOR_BY_CAR = {
    car.car_id: car.sponsor_id
    for car in load_car_configs()
}


BASE_SCREEN_SECONDS = 14.0
SCREEN_SECONDS_LOST_PER_POSITION = 3.0
MIN_SCREEN_SECONDS = 2.0
IMPRESSIONS_PER_SECOND = 1500
CLICK_RATE = 0.004
CONVERSION_RATE = 0.08
JITTER = 0.1


def _jitter(rng: random.Random) -> float:
    return 1.0 + rng.uniform(-JITTER, JITTER)


def build_sponsor_event(
    car,
    race,
    lap_number=None,
    scenario_name=None,
    rng=None,
) -> dict:
    rng = rng or random.Random()

    car_config = get_car_config(car.car_id)

    base = max(
        MIN_SCREEN_SECONDS,
        BASE_SCREEN_SECONDS
        - SCREEN_SECONDS_LOST_PER_POSITION * (car.position - 1),
    )

    visibility = round(
        base
        * excitement_factor(car, race, scenario_name)
        * _jitter(rng),
        2,
    )

    impressions = int(
        IMPRESSIONS_PER_SECOND
        * visibility
        * _jitter(rng)
    )

    clicks = min(
        impressions,
        int(impressions * CLICK_RATE * _jitter(rng)),
    )

    conversions = min(
        clicks,
        int(clicks * CONVERSION_RATE * _jitter(rng)),
    )

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": (
            car.lap_number
            if lap_number is None
            else lap_number
        ),
        "sponsor_id": car_config.sponsor_id,
        "impressions": impressions,
        "visibility_seconds": visibility,
        "clicks": clicks,
        "conversions": conversions,
    }
