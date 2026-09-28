from simulator.state import RaceState
from simulator.telemetry_event import build_telemetry_event


def test_build_telemetry_event():
    race = RaceState.create_default()
    car = race.get_car("CAR_01")

    race.simulate_next_lap("CAR_01")

    event = build_telemetry_event(car)

    assert event["car_id"] == "CAR_01"
    assert event["lap_number"] == 1

    assert "event_id" in event
    assert "event_time" in event

    assert event["speed_kmh"] > 0
    assert event["rpm"] > 0
    assert event["throttle_pct"] >= 0
    assert event["brake_pct"] >= 0
    assert event["gear"] >= 1

    assert event["engine_temperature_c"] > 0
    assert event["brake_temperature_c"] > 0
    assert event["battery_temperature_c"] > 0

    assert event["fuel_kg"] >= 0
    assert event["energy_kwh"] >= 0
    assert event["location_km"] > 0