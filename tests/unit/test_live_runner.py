from simulator.live_runner import TOPICS

def test_live_runner_covers_all_required_streams():
    assert set(TOPICS) == {
        "race.timing", "race.telemetry", "race.tyres", "race.weather",
        "race.pitstops", "race.incidents", "business.fans", "business.sponsors",
    }
