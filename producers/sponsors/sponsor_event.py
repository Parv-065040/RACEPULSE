"""
Sponsor-exposure event builder - Navroop's ownership (producers/sponsors/).
Topic: business.sponsors (see docs/event-contract.md). Each car carries
one sponsor's livery; exposure follows on-screen time, which follows race
state (leader and dramatic moments get more airtime).
"""
import random
from datetime import datetime, timezone
from uuid import uuid4

from producers.fans.excitement import excitement_factor

SPONSOR_BY_CAR = {
    "CAR_01": "SPONSOR_01",
    "CAR_02": "SPONSOR_02",
    "CAR_03": "SPONSOR_03",
}

BASE_SCREEN_SECONDS = 14.0          # leader's airtime per lap (heuristic)
SCREEN_SECONDS_LOST_PER_POSITION = 3.0
MIN_SCREEN_SECONDS = 2.0
IMPRESSIONS_PER_SECOND = 1500       # heuristic
CLICK_RATE = 0.004                  # clicks / impressions
CONVERSION_RATE = 0.08              # conversions / clicks
JITTER = 0.1


def _jitter(rng: random.Random) -> float:
    return 1.0 + rng.uniform(-JITTER, JITTER)


def build_sponsor_event(car, race, lap_number=None, scenario_name=None, rng=None) -> dict:
    rng = rng or random.Random()
    base = max(MIN_SCREEN_SECONDS,
               BASE_SCREEN_SECONDS - SCREEN_SECONDS_LOST_PER_POSITION * (car.position - 1))
    visibility = round(base * excitement_factor(car, race, scenario_name) * _jitter(rng), 2)
    impressions = int(IMPRESSIONS_PER_SECOND * visibility * _jitter(rng))
    clicks = min(impressions, int(impressions * CLICK_RATE * _jitter(rng)))
    conversions = min(clicks, int(clicks * CONVERSION_RATE * _jitter(rng)))

    return {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number if lap_number is None else lap_number,
        "sponsor_id": SPONSOR_BY_CAR[car.car_id],
        "impressions": impressions,
        "visibility_seconds": visibility,
        "clicks": clicks,
        "conversions": conversions,
    }
