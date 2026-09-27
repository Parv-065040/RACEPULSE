import json

from kafka import KafkaProducer

from simulator.state import RaceState
from simulator.timing_event import build_timing_event


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TIMING_TOPIC = "race.timing"


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_timing_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        TIMING_TOPIC,
        key=event["car_id"],
        value=event,
    )


def main() -> None:
    race = RaceState.create_default()
    producer = create_producer()

    try:
        cars = race.simulate_all_cars_next_lap()

        for car in cars:
            event = build_timing_event(car)

            publish_timing_event(
                producer=producer,
                event=event,
            )

            print(f"Published timing event: {event}")

        producer.flush()

    finally:
        producer.close()


if __name__ == "__main__":
    main()