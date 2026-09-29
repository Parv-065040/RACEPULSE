"""
Shared continuous race runner.

One RaceSimulator feeds every stream so timing, tyres, weather, pit stops,
incidents, fans and sponsors stay causally aligned during a live demo.
"""
from __future__ import annotations
import argparse
import json
import time
from kafka import KafkaProducer
from engine.validation.safe_publish import safe_publish
from producers.fans.fan_event import build_fan_event
from producers.sponsors.sponsor_event import build_sponsor_event
from simulator.incident_event import build_incident_event
from simulator.pitstop_event import build_pitstop_event
from simulator.scenario import ScenarioType, create_scenario
from simulator.simulator import RaceSimulator
from simulator.telemetry_event import build_telemetry_event
from simulator.timing_event import build_timing_event
from simulator.tyre_event import build_tyre_event
from simulator.weather_event import build_weather_event

BOOTSTRAP="localhost:9092"
TOPICS=("race.timing","race.telemetry","race.tyres","race.weather",
        "race.pitstops","race.incidents","business.fans","business.sponsors")

def create_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        key_serializer=lambda k: str(k).encode(),
        value_serializer=lambda v: json.dumps(v).encode(),
        acks="all", retries=3,
    )

def publish_snapshot(producer, simulator):
    count=0
    for car in simulator.race.cars.values():
        if not car.is_running:
            continue
        events=[
            ("race.timing",build_timing_event(car)),
            ("race.telemetry",build_telemetry_event(car)),
            ("race.tyres",build_tyre_event(car)),
            ("race.weather",build_weather_event(simulator.race.weather,car.car_id,car.lap_number)),
            ("race.pitstops",build_pitstop_event(car)),
            ("business.fans",build_fan_event(car,simulator.race,car.lap_number,simulator.scenario.name)),
            ("business.sponsors",build_sponsor_event(car,simulator.race,car.lap_number,simulator.scenario.name)),
        ]
        for topic,event in events:
            if safe_publish(producer,topic,event):
                count+=1
    for car in simulator.race.cars.values():
        if car.incident.active:
            if safe_publish(producer,"race.incidents",
                            build_incident_event(car,simulator.current_lap)):
                count+=1
    producer.flush()
    return count

def run_live(scenario=ScenarioType.NORMAL_RACE,delay=1.0,max_laps=None,producer=None):
    simulator=RaceSimulator(scenario=create_scenario(scenario))
    owns=producer is None
    producer=producer or create_producer()
    try:
        while max_laps is None or simulator.current_lap<max_laps:
            simulator.advance_one_lap()
            count=publish_snapshot(producer,simulator)
            print(f"[live-runner] lap={simulator.current_lap} scenario={scenario.value} events={count}",flush=True)
            if delay>0: time.sleep(delay)
    finally:
        if owns: producer.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scenario",default="NORMAL_RACE",choices=[s.value for s in ScenarioType])
    p.add_argument("--delay",type=float,default=1.0)
    p.add_argument("--laps",type=int,default=None)
    a=p.parse_args()
    run_live(ScenarioType(a.scenario),a.delay,a.laps)

if __name__=="__main__": main()
