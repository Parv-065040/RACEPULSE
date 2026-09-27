"""
Stale-stream monitor - Parv's ownership (engine/alerts/).
Tracks the last time each car_id was seen; flags a car as stale
once it exceeds the configured threshold, and un-flags it once
data resumes (so it can alert again on a future stall).
"""
import time
import yaml
from engine.alerts.alert_engine import raise_stale_stream_alert

with open("config/thresholds.yaml", "r", encoding="utf-8-sig") as f:
    _CONFIG = yaml.safe_load(f)["stale_stream_detection"]

THRESHOLD_SECONDS = _CONFIG["threshold_seconds"]

_last_seen_by_car: dict[str, float] = {}
_flagged: set[str] = set()

def mark_seen(car_id: str) -> None:
    _last_seen_by_car[car_id] = time.time()
    if car_id in _flagged:
        print(f"RECOVERED  car={car_id}  stream resumed")
        _flagged.discard(car_id)

def check_for_stale_cars() -> None:
    now = time.time()
    for car_id, last_seen in _last_seen_by_car.items():
        elapsed = now - last_seen
        if elapsed > THRESHOLD_SECONDS and car_id not in _flagged:
            print(f"STALE  car={car_id}  no data for {elapsed:.1f}s  -> alert raised")
            raise_stale_stream_alert(car_id, elapsed)
            _flagged.add(car_id)