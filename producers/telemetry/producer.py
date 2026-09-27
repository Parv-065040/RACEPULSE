import json

from kafka import KafkaProducer

from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator
from simulator.telemetry_event import build_telemetry_event


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TELEMETRY_TOPIC = "race.telemetry"
NUMBER_OF_LAPS = 3


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_telemetry_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        TELEMETRY_TOPIC,
        key=event["car_id"],
        value=event,
    )


def run_telemetry_producer(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> None:
    """
    Run the telemetry producer for the selected race scenario.
    """

    simulator = RaceSimulator(
        scenario=create_scenario(scenario),
    )

    producer = create_producer()

    try:
        for _ in range(NUMBER_OF_LAPS):
            cars = simulator.advance_one_lap()

            for car in cars:
                event = build_telemetry_event(car)

                publish_telemetry_event(
                    producer=producer,
                    event=event,
                )

                print(
                    f"Published telemetry event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"speed={event['speed_kmh']:.2f} km/h | "
                    f"rpm={event['rpm']} | "
                    f"fuel={event['fuel_kg']:.2f} kg"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_telemetry_producer(
        scenario=ScenarioType.NORMAL_RACE,
    )


if __name__ == "__main__":
    main()