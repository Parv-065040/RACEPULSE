"""
Fan-engagement event builder - Navroop's ownership (producers/fans/).
Topic: business.fans (see docs/event-contract.md). Raw counts only;
derived KPIs such as engagement rate belong to the analytics layer.
"""
import random
from datetime import datetime, timezone
from uuid import uuid4

from producers.fans.excitement import excitement_factor

BASE_VIEWERS = 50_000
# Position -> popularity: the leader draws the most viewers.
POPULARITY_BY_POSITION_STEP = 0.2
MIN_POPULARITY = 0.5

# Share of viewers producing each interaction this lap (simulation heuristics).
RATIOS = {
    "app_sessions": 0.30,
    "searches": 0.05,
    "likes": 0.12,
    "comments": 0.02,
    "shares": 0.01,
    "merch_clicks": 0.005,
}
JITTER = 0.1  # +/-10% noise on top of the causal value


def _jitter(rng: random.Random) -> float:
    return 1.0 + rng.uniform(-JITTER, JITTER)


def build_fan_event(car, race, lap_number=None, scenario_name=None, rng=None) -> dict:
    rng = rng or random.Random()
    popularity = max(MIN_POPULARITY, 1.2 - POPULARITY_BY_POSITION_STEP * (car.position - 1))
    excitement = excitement_factor(car, race, scenario_name)
    viewers = int(BASE_VIEWERS * popularity * excitement * _jitter(rng))

    event = {
        "event_id": str(uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": car.car_id,
        "lap_number": car.lap_number if lap_number is None else lap_number,
        "viewers": viewers,
    }
    for field, ratio in RATIOS.items():
        event[field] = int(viewers * ratio * _jitter(rng))
    return event
