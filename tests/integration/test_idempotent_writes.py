"""
Integration test: idempotent MySQL writes for KPI-001 results.

This is the automated version of the manual replay test done earlier
(sending the same 18 Kafka messages twice and confirming the row count
stayed at 18 instead of becoming 36). Requires the real Docker MySQL
container to be running with the schema already applied.

Run with: pytest tests/integration/test_idempotent_writes.py -v
"""
from datetime import datetime, timezone
from conftest import requires_mysql
from database.connection import get_connection
from database.writer import write_kpi_result

TEST_EVENT_ID = "aaaaaaaa-0000-0000-0000-000000000001"  # 36 chars, fits VARCHAR(36)
TEST_CAR_ID = "TEST_CAR_IDEM"  # kept short, well under VARCHAR(20)


def _make_test_event_and_kpi(lap_time_ms: int, delta_ms: int, severity: str):
    event = {
        "event_id": TEST_EVENT_ID,
        "event_time": datetime.now(timezone.utc).isoformat(),
        "car_id": TEST_CAR_ID,
        "lap_number": 1,
    }
    kpi = {
        "kpi_id": "KPI-001",
        "car_id": TEST_CAR_ID,
        "lap_time_ms": lap_time_ms,
        "best_lap_time_ms": lap_time_ms,
        "delta_ms": delta_ms,
        "severity": severity,
    }
    return event, kpi


def _cleanup():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM kpi_results WHERE event_id = %s", (TEST_EVENT_ID,))
    conn.close()


def _count_rows_for_test_event() -> int:
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM kpi_results WHERE event_id = %s", (TEST_EVENT_ID,))
        (count,) = cursor.fetchone()
    conn.close()
    return count


@requires_mysql
def test_writing_the_same_event_twice_does_not_duplicate_the_row():
    _cleanup()  # ensure a clean slate even if a previous run crashed mid-test
    try:
        event, kpi = _make_test_event_and_kpi(lap_time_ms=90000, delta_ms=0, severity="none")

        write_kpi_result(kpi, event)
        assert _count_rows_for_test_event() == 1

        # Same event_id + kpi_id again, simulating a Kafka replay/duplicate delivery
        write_kpi_result(kpi, event)
        assert _count_rows_for_test_event() == 1  # still 1, not 2
    finally:
        _cleanup()


@requires_mysql
def test_replaying_the_same_event_with_updated_values_overwrites_not_appends():
    _cleanup()
    try:
        event, kpi_v1 = _make_test_event_and_kpi(lap_time_ms=90000, delta_ms=0, severity="none")
        write_kpi_result(kpi_v1, event)

        _, kpi_v2 = _make_test_event_and_kpi(lap_time_ms=92000, delta_ms=2000, severity="critical")
        write_kpi_result(kpi_v2, event)  # same event_id, different computed values

        assert _count_rows_for_test_event() == 1

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT delta_ms, severity FROM kpi_results WHERE event_id = %s", (TEST_EVENT_ID,)
            )
            delta_ms, severity = cursor.fetchone()
        conn.close()

        assert delta_ms == 2000
        assert severity == "critical"
    finally:
        _cleanup()