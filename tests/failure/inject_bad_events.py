"""
Demo tool - Navroop's ownership (tests/failure/). NOT a pytest test.

Publishes a mix of good and deliberately bad messages to a business topic
so the validation monitor's DLQ routing can be shown live (demo slot
12:30-13:30). Run the monitor first in another terminal:

    python -m engine.validation.monitor
    python tests/failure/inject_bad_events.py            # business.fans
    python tests/failure/inject_bad_events.py --topic business.sponsors
"""
import argparse
import json
import random
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kafka import KafkaProducer  # noqa: E402

from producers.fans.fan_event import build_fan_event  # noqa: E402
from producers.sponsors.sponsor_event import build_sponsor_event  # noqa: E402
from simulator.simulator import RaceSimulator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="business.fans", choices=["business.fans", "business.sponsors"])
    topic = parser.parse_args().topic

    sim = RaceSimulator()
    sim.advance_one_lap()
    car = sim.race.get_car("CAR_01")
    builder = build_fan_event if topic == "business.fans" else build_sponsor_event
    good = builder(car, sim.race, sim.current_lap, rng=random.Random(1))

    missing = {k: v for k, v in good.items() if k != "event_id"}
    wrong_type = {**good, "event_id": str(uuid.uuid4()), "lap_number": "one"}
    unknown_car = {**good, "event_id": str(uuid.uuid4()), "car_id": "CAR_99"}
    negative_field = "impressions" if topic.endswith("sponsors") else "likes"
    negative = {**good, "event_id": str(uuid.uuid4()), negative_field: -1}

    messages = [
        ("good event", good),
        ("duplicate of the good event", good),
        ("missing event_id", missing),
        ("wrong type (lap_number='one')", wrong_type),
        ("unknown car CAR_99", unknown_car),
        ("negative count", negative),
        ("INVALID JSON", b'{"event_id": "abc", "car_id": "CAR_01", '),
    ]

    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    for label, payload in messages:
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        producer.send(topic, key=b"CAR_01", value=raw)
        print(f"sent -> {topic}: {label}")
    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()
