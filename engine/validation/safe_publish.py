"""
Safe publish helper - Navroop's ownership (engine/validation/).

Producers call safe_publish() instead of producer.send() directly:

    invalid event   -> system.dlq        (never published to the real topic)
    Kafka send fails -> system.dlq       (best effort; failure is logged)
    otherwise        -> topic, keyed by car_id

Returns True only if the event was handed to Kafka.
"""
from engine.validation.validator import validate_event


def safe_publish(producer, topic: str, event: dict, dlq_sender=None) -> bool:
    if dlq_sender is None:
        from engine.validation.dlq import send_to_dlq

        dlq_sender = send_to_dlq

    key = event.get("car_id") if isinstance(event, dict) else None

    errors = validate_event(topic, event)
    if errors:
        print(f"INVALID event built for {topic}: {errors}  -> sent to system.dlq", flush=True)
        _dlq(dlq_sender, topic, key, event, errors)
        return False

    try:
        producer.send(topic, key=key, value=event)
    except Exception as exc:
        print(f"PUBLISH FAILED on {topic} key={key}: {exc}", flush=True)
        _dlq(dlq_sender, topic, key, event, [f"publish failed: {exc}"])
        return False
    return True


def _dlq(dlq_sender, topic, key, event, errors) -> None:
    payload = event if isinstance(event, dict) else {"_non_object_payload": event}
    try:
        dlq_sender(topic, key, payload, errors)
    except Exception as exc:
        print(f"DLQ SEND FAILED for {topic} key={key}: {exc}", flush=True)
