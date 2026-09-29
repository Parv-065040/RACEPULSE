import json

from kafka import KafkaProducer

from simulator.pitstop_event import build_pitstop_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
PITSTOP_TOPIC = "race.pitstops"
NUMBER_OF_LAPS = 3


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_pitstop_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        PITSTOP_TOPIC,
        key=event["car_id"],
        value=event,
    )


def run_pitstop_producer(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> None:
    simulator = RaceSimulator(
        scenario=create_scenario(scenario)
    )

    producer = create_producer()

    try:
        for _ in range(NUMBER_OF_LAPS):
            cars = simulator.advance_one_lap()

            for car in cars:
                event = build_pitstop_event(car)

                publish_pitstop_event(
                    producer=producer,
                    event=event,
                )

                print(
                    f"Published pit-stop event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"entry={event['pit_entry']} | "
                    f"stop={event['pit_stop']} | "
                    f"tyres={event['tyre_change']} | "
                    f"repair={event['repair']} | "
                    f"exit={event['pit_exit']}"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_pitstop_producer(
        scenario=ScenarioType.NORMAL_RACE
    )


if __name__ == "__main__":
    main()