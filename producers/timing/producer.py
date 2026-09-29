import json

from kafka import KafkaProducer

from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator
from simulator.timing_event import build_timing_event


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TIMING_TOPIC = "race.timing"
NUMBER_OF_LAPS = 3


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


def run_timing_producer(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> None:
    """
    Run the timing producer for the selected race scenario.

    The timing event structure remains unchanged.
    """

    simulator = RaceSimulator(
        scenario=create_scenario(scenario),
    )

    producer = create_producer()

    try:
        for _ in range(NUMBER_OF_LAPS):
            cars = simulator.advance_one_lap()

            for car in cars:
                event = build_timing_event(car)

                publish_timing_event(
                    producer=producer,
                    event=event,
                )

                print(
                    f"Published timing event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"lap_time_ms={event['lap_time_ms']} | "
                    f"gap={event['gap_to_leader_ms']}"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_timing_producer(
        scenario=ScenarioType.NORMAL_RACE,
    )


if __name__ == "__main__":
    main()