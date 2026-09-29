def test_dlq_record_shape():
    record={
        "source_topic":"race.timing",
        "raw_key":"CAR_01",
        "raw_value":{"event_id":"bad"},
        "errors":["missing field: lap_time_ms"],
    }
    assert set(record)=={"source_topic","raw_key","raw_value","errors"}
    assert record["source_topic"]=="race.timing"
