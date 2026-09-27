import json

from kafka import KafkaProducer

from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator
from simulator.tyre_event import build_tyre_event


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TYRE_TOPIC = "race.tyres"
NUMBER_OF_LAPS = 3


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_tyre_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        TYRE_TOPIC,
        key=event["car_id"],
        value=event,
    )


def run_tyre_producer(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> None:
    """
    Run the tyre producer for the selected race scenario.
    """

    simulator = RaceSimulator(
        scenario=create_scenario(scenario),
    )

    producer = create_producer()

    try:
        for _ in range(NUMBER_OF_LAPS):
            cars = simulator.advance_one_lap()

            for car in cars:
                event = build_tyre_event(car)

                publish_tyre_event(
                    producer=producer,
                    event=event,
                )

                print(
                    f"Published tyre event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"compound={event['compound']} | "
                    f"age={event['age_laps']} | "
                    f"wear={event['wear']:.2f} | "
                    f"grip={event['grip']:.2f}"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_tyre_producer(
        scenario=ScenarioType.NORMAL_RACE,
    )


if __name__ == "__main__":
    main()