from datetime import datetime, timezone

import pytest

from engine.windows.tumbling_window import TumblingWindow


def test_events_same_15_second_window_are_grouped():
    window = TumblingWindow(15)

    assert window.add(
        "CAR_01",
        "2026-09-30T10:00:01+00:00",
        {"value": 10},
    ) == []

    assert window.add(
        "CAR_01",
        "2026-09-30T10:00:10+00:00",
        {"value": 20},
    ) == []


def test_new_window_emits_previous_window():
    window = TumblingWindow(15)

    window.add(
        "CAR_01",
        "2026-09-30T10:00:01+00:00",
        {"value": 10},
    )

    window.add(
        "CAR_01",
        "2026-09-30T10:00:10+00:00",
        {"value": 20},
    )

    results = window.add(
        "CAR_01",
        "2026-09-30T10:00:16+00:00",
        {"value": 30},
    )

    assert len(results) == 1
    assert results[0].entity_id == "CAR_01"
    assert results[0].count == 2
    assert [e["value"] for e in results[0].events] == [10, 20]


def test_windows_are_non_overlapping():
    window = TumblingWindow(15)

    window.add(
        "CAR_01",
        "2026-09-30T10:00:14+00:00",
        {"value": 14},
    )

    results = window.add(
        "CAR_01",
        "2026-09-30T10:00:15+00:00",
        {"value": 15},
    )

    assert len(results) == 1
    assert results[0].count == 1
    assert results[0].events[0]["value"] == 14


def test_entities_have_independent_windows():
    window = TumblingWindow(15)

    window.add(
        "CAR_01",
        "2026-09-30T10:00:01+00:00",
        {"value": 1},
    )

    window.add(
        "CAR_02",
        "2026-09-30T10:00:01+00:00",
        {"value": 2},
    )

    results = window.add(
        "CAR_01",
        "2026-09-30T10:00:16+00:00",
        {"value": 3},
    )

    assert len(results) == 1
    assert results[0].entity_id == "CAR_01"


def test_flush_returns_open_windows():
    window = TumblingWindow(15)

    window.add(
        "CAR_01",
        "2026-09-30T10:00:01+00:00",
        {"value": 10},
    )

    results = window.flush("CAR_01")

    assert len(results) == 1
    assert results[0].count == 1
    assert window.flush("CAR_01") == []


def test_invalid_window_size():
    with pytest.raises(ValueError):
        TumblingWindow(0)

def test_watermark_emits_completed_window():
    window = TumblingWindow(15)

    window.add(
        "CAR_01",
        "2026-09-30T10:00:01+00:00",
        {"value": 10},
    )

    window.add(
        "CAR_01",
        "2026-09-30T10:00:10+00:00",
        {"value": 20},
    )

    results = window.advance_watermark(
        "CAR_01",
        "2026-09-30T10:00:15+00:00",
    )

    assert len(results) == 1
    assert results[0].entity_id == "CAR_01"
    assert results[0].count == 2
    assert [e["value"] for e in results[0].events] == [10, 20]
