"""
Sponsor-exposure producer - Navroop's ownership (producers/sponsors/).
Publishes business.sponsors, keyed by car_id, driven by the same stateful
RaceSimulator the race producers use (read-only).

Run:  python -m producers.sponsors.producer [--scenario COMMERCIAL_SURGE]
"""
import argparse
import json
import time

from kafka import KafkaProducer

from engine.validation.safe_publish import safe_publish
from producers.sponsors.sponsor_event import build_sponsor_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
SPONSORS_TOPIC = "business.sponsors"
NUMBER_OF_LAPS = 5


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def run_sponsor_producer(scenario: ScenarioType = ScenarioType.NORMAL_RACE,
                         laps: int = NUMBER_OF_LAPS, producer=None, delay_s: float = 0.0) -> int:
    simulator = RaceSimulator(scenario=create_scenario(scenario))
    owns_producer = producer is None
    producer = producer or create_producer()
    published = 0
    try:
        for _ in range(laps):
            simulator.advance_one_lap()
            for car in simulator.race.cars.values():
                if not car.is_running:
                    continue  # a retired car has NO exposure data - never publish zeros
                event = build_sponsor_event(car, simulator.race,
                                            lap_number=simulator.current_lap,
                                            scenario_name=scenario)
                if safe_publish(producer, SPONSORS_TOPIC, event):
                    published += 1
                    print(f"Published sponsor event: {event['car_id']} | {event['sponsor_id']} | "
                          f"lap={event['lap_number']} | impressions={event['impressions']} | "
                          f"clicks={event['clicks']}")
            if delay_s:
                time.sleep(delay_s)
        producer.flush()
    finally:
        if owns_producer:
            producer.close()
    return published


def main() -> None:
    parser = argparse.ArgumentParser(description="RACEPULSE sponsor exposure producer")
    parser.add_argument("--scenario", default="NORMAL_RACE", choices=[s.value for s in ScenarioType])
    parser.add_argument("--laps", type=int, default=NUMBER_OF_LAPS)
    args = parser.parse_args()
    run_sponsor_producer(ScenarioType(args.scenario), laps=args.laps)


if __name__ == "__main__":
    main()
