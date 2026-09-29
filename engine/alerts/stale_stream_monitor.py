"""Retirement-aware stale-stream monitor."""
import time
import yaml
from engine.alerts.alert_engine import raise_stale_stream_alert

with open("config/thresholds.yaml", "r", encoding="utf-8-sig") as f:
    THRESHOLD_SECONDS = yaml.safe_load(f)["stale_stream_detection"]["threshold_seconds"]

_last_seen_by_car: dict[str, float] = {}
_flagged: set[str] = set()
_retired: set[str] = set()

def mark_seen(car_id: str) -> None:
    _last_seen_by_car[car_id] = time.time()
    if car_id in _retired:
        _retired.discard(car_id)
    if car_id in _flagged:
        print(f"RECOVERED car={car_id} stream resumed", flush=True)
        _flagged.discard(car_id)

def mark_retired(car_id: str) -> None:
    _retired.add(car_id)
    _flagged.discard(car_id)
    print(f"RETIRED car={car_id} stale monitoring suppressed", flush=True)

def check_for_stale_cars() -> None:
    now = time.time()
    for car_id, last_seen in list(_last_seen_by_car.items()):
        if car_id in _retired:
            continue
        elapsed = now - last_seen
        if elapsed > THRESHOLD_SECONDS and car_id not in _flagged:
            print(f"STALE car={car_id} no data for {elapsed:.1f}s -> alert raised", flush=True)
            raise_stale_stream_alert(car_id, elapsed)
            _flagged.add(car_id)
