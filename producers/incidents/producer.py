import json

from kafka import KafkaProducer

from simulator.incident_event import build_incident_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
INCIDENT_TOPIC = "race.incidents"
NUMBER_OF_LAPS = 5


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_incident_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        INCIDENT_TOPIC,
        key=event["car_id"],
        value=event,
    )


def run_incident_producer(
    scenario: ScenarioType = ScenarioType.NORMAL_RACE,
) -> None:
    simulator = RaceSimulator(
        scenario=create_scenario(scenario)
    )

    producer = create_producer()

    published_incidents: set[tuple[str, str]] = set()

    try:
        for _ in range(NUMBER_OF_LAPS):
            simulator.advance_one_lap()

            for car in simulator.race.cars.values():
                if not car.incident.active:
                    continue

                incident_key = (
                    car.car_id,
                    car.incident.incident_type,
                )

                if incident_key in published_incidents:
                    continue

                event = build_incident_event(
                    car=car,
                    lap_number=simulator.current_lap,
                )

                publish_incident_event(
                    producer=producer,
                    event=event,
                )

                published_incidents.add(incident_key)

                print(
                    f"Published incident event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"type={event['incident_type']} | "
                    f"active={event['active']} | "
                    f"severity={event['severity']}"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_incident_producer(
        scenario=ScenarioType.MECHANICAL_FAILURE
    )


if __name__ == "__main__":
    main()