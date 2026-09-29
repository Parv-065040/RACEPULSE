import importlib

def test_retired_car_is_not_reported_stale(monkeypatch):
    monitor = importlib.import_module("engine.alerts.stale_stream_monitor")
    monitor._last_seen_by_car.clear()
    monitor._flagged.clear()
    monitor._retired.clear()

    monkeypatch.setattr(monitor.time, "time", lambda: 100.0)
    monitor.mark_seen("CAR_03")
    monitor.mark_retired("CAR_03")

    called = []
    monkeypatch.setattr(monitor, "raise_stale_stream_alert",
                        lambda car_id, seconds: called.append((car_id, seconds)))
    monkeypatch.setattr(monitor.time, "time", lambda: 1000.0)
    monitor.check_for_stale_cars()

    assert called == []
