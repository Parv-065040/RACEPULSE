"""
Fan-engagement producer - Navroop's ownership (producers/fans/).
Publishes business.fans, keyed by car_id, driven by the same stateful
RaceSimulator the race producers use (read-only).

Run:  python -m producers.fans.producer [--scenario RAIN]
"""
import argparse
import json
import time

from kafka import KafkaProducer

from engine.validation.safe_publish import safe_publish
from producers.fans.fan_event import build_fan_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
FANS_TOPIC = "business.fans"
NUMBER_OF_LAPS = 5


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def run_fan_producer(scenario: ScenarioType = ScenarioType.NORMAL_RACE,
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
                    continue  # a retired car has NO fan data - never publish zeros
                event = build_fan_event(car, simulator.race,
                                        lap_number=simulator.current_lap,
                                        scenario_name=scenario)
                if safe_publish(producer, FANS_TOPIC, event):
                    published += 1
                    print(f"Published fan event: {event['car_id']} | lap={event['lap_number']} | "
                          f"viewers={event['viewers']} | likes={event['likes']}")
            if delay_s:
                time.sleep(delay_s)
        producer.flush()
    finally:
        if owns_producer:
            producer.close()
    return published


def main() -> None:
    parser = argparse.ArgumentParser(description="RACEPULSE fan engagement producer")
    parser.add_argument("--scenario", default="NORMAL_RACE", choices=[s.value for s in ScenarioType])
    parser.add_argument("--laps", type=int, default=NUMBER_OF_LAPS)
    args = parser.parse_args()
    run_fan_producer(ScenarioType(args.scenario), laps=args.laps)


if __name__ == "__main__":
    main()
