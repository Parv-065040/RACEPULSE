import json

from kafka import KafkaProducer

from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator
from simulator.weather_event import build_weather_event


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
WEATHER_TOPIC = "race.weather"
NUMBER_OF_LAPS = 3


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_weather_event(
    producer: KafkaProducer,
    event: dict,
) -> None:
    producer.send(
        WEATHER_TOPIC,
        key=event["car_id"],
        value=event,
    )


def run_weather_producer(
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
                event = build_weather_event(
                    weather=simulator.race.weather,
                    car_id=car.car_id,
                    lap_number=car.lap_number,
                )

                publish_weather_event(
                    producer=producer,
                    event=event,
                )

                print(
                    f"Published weather event: "
                    f"{event['car_id']} | "
                    f"lap={event['lap_number']} | "
                    f"condition={event['condition']} | "
                    f"rain={event['rain_intensity']:.2f} | "
                    f"wetness={event['track_wetness']:.2f} | "
                    f"grip={event['track_grip']:.2f}"
                )

        producer.flush()

    finally:
        producer.close()


def main() -> None:
    run_weather_producer(
        scenario=ScenarioType.RAIN
    )


if __name__ == "__main__":
    main()