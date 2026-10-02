"""Dead-letter queue publisher with a best-effort MySQL audit record."""
import json
from datetime import datetime, timezone

from kafka import KafkaProducer
from database.connection import get_connection

_producer = None


def _safe_raw_value(value):
    """
    Preserve the DLQ raw_value contract.

    - dict -> unchanged
    - bytes/bytearray containing valid JSON object -> parsed dict
    - malformed bytes -> wrapped dict
    - other values -> safely represented
    """
    if isinstance(value, dict):
        return value

    if isinstance(value, (bytes, bytearray)):
        text = bytes(value).decode("utf-8", errors="replace")

        try:
            parsed = json.loads(text)

            if isinstance(parsed, dict):
                return parsed

            return {
                "_non_object_payload": parsed
            }

        except (json.JSONDecodeError, TypeError):
            return {
                "_unparseable_payload": text[:2000]
            }

    if isinstance(value, str):
        try:
            parsed = json.loads(value)

            if isinstance(parsed, dict):
                return parsed

            return {
                "_non_object_payload": parsed
            }

        except (json.JSONDecodeError, TypeError):
            return {
                "_unparseable_payload": value[:2000]
            }

    return value


def _safe_key(value):
    """Convert Kafka key bytes into a readable string."""
    if value is None:
        return None

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, bytearray):
        return bytes(value).decode("utf-8", errors="replace")

    return str(value)


def _get_producer():
    global _producer

    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(
                v,
                ensure_ascii=False,
            ).encode("utf-8"),
        )

    return _producer


def send_to_dlq(source_topic, raw_key, raw_value, errors):
    failed_at = datetime.now(timezone.utc)

    record = {
        "source_topic": source_topic,
        "failed_at": failed_at.isoformat(),
        "key": _safe_key(raw_key),
        "raw_value": _safe_raw_value(raw_value),
        "errors": errors,
    }

    _get_producer().send("system.dlq", value=record)
    _get_producer().flush()

    try:
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dlq_events
                (source_topic, raw_key, errors, failed_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    source_topic,
                    _safe_key(raw_key),
                    json.dumps(errors),
                    failed_at.replace(tzinfo=None),
                ),
            )

        conn.commit()
        conn.close()

    except Exception as exc:
        print(
            f"DLQ audit write failed "
            f"(Kafka DLQ already published): {exc}",
            flush=True,
        )
