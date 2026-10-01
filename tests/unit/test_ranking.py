from types import SimpleNamespace

from engine.race.ranking import RaceRanking


def car(car_id, race_time_ms, running=True):
    return SimpleNamespace(
        car_id=car_id,
        race_time_ms=race_time_ms,
        is_running=running,
        position=99,
        gap_to_leader_ms=999999,
    )


def test_ranking_orders_cars_by_race_time():
    cars = [
        car("CAR_02", 201000),
        car("CAR_01", 200000),
        car("CAR_03", 205000),
    ]

    RaceRanking().update(cars)

    assert cars[1].position == 1
    assert cars[0].position == 2
    assert cars[2].position == 3


def test_ranking_calculates_gap_to_leader():
    cars = [
        car("CAR_01", 100000),
        car("CAR_02", 101500),
        car("CAR_03", 103200),
    ]

    RaceRanking().update(cars)

    assert cars[0].gap_to_leader_ms == 0
    assert cars[1].gap_to_leader_ms == 1500
    assert cars[2].gap_to_leader_ms == 3200


def test_ranking_excludes_retired_cars():
    cars = [
        car("CAR_01", 100000),
        car("CAR_02", 101000),
        car("CAR_03", 90000, running=False),
    ]

    RaceRanking().update(cars)

    assert cars[0].position == 1
    assert cars[1].position == 2
    assert cars[2].position == 99


def test_ranking_produces_unique_positions():
    cars = [
        car("CAR_01", 100000),
        car("CAR_02", 101000),
        car("CAR_03", 102000),
        car("CAR_04", 103000),
    ]

    RaceRanking().update(cars)

    positions = [c.position for c in cars if c.is_running]

    assert sorted(positions) == [1, 2, 3, 4]
