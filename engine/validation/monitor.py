import os
"""
Validation monitor - Navroop's ownership (engine/validation/).

A small standalone consumer that runs every message on the chosen topics
through ValidationGate. Bad JSON / bad fields / unknown entities go to
system.dlq, repeats are counted and dropped, and a stats line is printed
so a demo can show the pipeline surviving bad input.

It uses its OWN consumer group (validation-monitor), so it never steals
messages from Parv's consumers.

race.timing is excluded by default because consumers/performance already
validates and DLQ-routes it; including it here would create two DLQ
records per bad timing event. Use --include-timing to override.

Run:  python -m engine.validation.monitor
"""
import argparse

from kafka import KafkaConsumer

from engine.validation.gate import ValidationGate
from engine.validation.schemas import SCHEMAS

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUP_ID = "validation-monitor"
POLL_TIMEOUT_MS = 5000


def default_topics(include_timing: bool = False) -> list[str]:
    return [t for t in SCHEMAS if include_timing or t != "race.timing"]


def run(topics: list[str], bootstrap: str = BOOTSTRAP, group_id: str = GROUP_ID,
        max_idle_polls: int | None = None) -> ValidationGate:
    """Consume until interrupted (or until max_idle_polls empty polls, used by tests)."""
    gate = ValidationGate()
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        # NO deserializers: raw bytes in, so invalid JSON reaches the gate
        # instead of raising inside consumer.poll().
    )
    print(f"validation-monitor listening on {topics} (group={group_id}) ...", flush=True)
    idle = 0
    try:
        while True:
            records = consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
            if not records:
                idle += 1
                print(f"[validation-monitor] idle  stats={gate.stats}", flush=True)
                if max_idle_polls is not None and idle >= max_idle_polls:
                    break
                continue
            idle = 0
            for _tp, messages in records.items():
                for message in messages:
                    gate.check(message.topic, message.key, message.value)
            print(f"[validation-monitor] stats={gate.stats}", flush=True)
    except KeyboardInterrupt:
        print("validation-monitor stopped", flush=True)
    finally:
        consumer.close()
    return gate


def main() -> None:
    parser = argparse.ArgumentParser(description="RACEPULSE validation monitor")
    parser.add_argument("--topics", nargs="+", help="topics to validate (default: all except race.timing)")
    parser.add_argument("--include-timing", action="store_true")
    args = parser.parse_args()
    run(args.topics or default_topics(args.include_timing))


if __name__ == "__main__":
    main()

