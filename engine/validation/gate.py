"""
Validation gate - Navroop's ownership (engine/validation/).

ValidationGate.check(topic, key, raw) is the one call that turns a raw
Kafka message into either a trusted event dict or None:

    raw bytes/str/dict
      -> parse JSON            (bad JSON      -> DLQ)
      -> validate schema       (bad fields    -> DLQ)
      -> duplicate check       (repeat        -> dropped + counted)
      -> event dict

Nothing here raises on bad input: one bad message must never crash the
pipeline. Rejected messages are always sent to system.dlq via
engine.validation.dlq.send_to_dlq (never silently dropped) and counted
in gate.stats.

DLQ records always carry a *dict* raw_value (unparseable payloads are
wrapped as {"_unparseable_payload": "..."}), because existing tooling
reads record["raw_value"].get(...).
"""
import json

from engine.validation.dedup import DuplicateDetector
from engine.validation.validator import validate_event

MAX_RAW_CHARS = 2000


def _to_text(raw) -> str:
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw).decode("utf-8", errors="replace")
    return str(raw)


def safe_key(key) -> str | None:
    if key is None:
        return None
    if isinstance(key, (bytes, bytearray)):
        return bytes(key).decode("utf-8", errors="replace")
    return str(key)


class ValidationGate:
    def __init__(self, dlq_sender=None, dedup: DuplicateDetector | None = None) -> None:
        if dlq_sender is None:
            # imported lazily so tests / tools can build a gate without Kafka
            from engine.validation.dlq import send_to_dlq

            dlq_sender = send_to_dlq
        self._send_to_dlq = dlq_sender
        self._dedup = dedup if dedup is not None else DuplicateDetector()
        self.stats = {"accepted": 0, "invalid": 0, "duplicate": 0}

    def _reject(self, topic: str, key, raw_value: dict, errors: list[str]) -> None:
        self.stats["invalid"] += 1
        print(f"INVALID event on {topic} key={key}: {errors}  -> sent to system.dlq", flush=True)
        try:
            self._send_to_dlq(topic, key, raw_value, errors)
        except Exception as exc:  # DLQ itself failing must not crash the caller
            print(f"DLQ SEND FAILED for {topic} key={key}: {exc}", flush=True)

    def check(self, topic: str, key, raw) -> dict | None:
        key = safe_key(key)

        if isinstance(raw, dict):
            event = raw
        else:
            text = _to_text(raw)
            try:
                event = json.loads(text)
            except ValueError as exc:
                self._reject(
                    topic, key, {"_unparseable_payload": text[:MAX_RAW_CHARS]},
                    [f"invalid JSON: {exc}"],
                )
                return None

        errors = validate_event(topic, event)
        if errors:
            payload = event if isinstance(event, dict) else {"_non_object_payload": event}
            self._reject(topic, key, payload, errors)
            return None

        if self._dedup.is_duplicate(topic, event["event_id"]):
            self.stats["duplicate"] += 1
            print(f"DUPLICATE event on {topic} event_id={event['event_id']}  -> dropped", flush=True)
            return None

        self.stats["accepted"] += 1
        return event
