"""
Duplicate-event detector - Navroop's ownership (engine/validation/).

Remembers the last `max_size` (topic, event_id) pairs. Kafka is
at-least-once, so producer retries and consumer restarts legitimately
produce duplicates; dropping the repeat here keeps counters (likes,
impressions, ...) from being double counted before they reach MySQL.

Bounded on purpose: an unbounded set would grow forever in a long race.
Oldest entries are evicted first, so a duplicate that arrives after
`max_size` other events is not caught - MySQL's UNIQUE KEY remains the
final safety net for the KPI tables.
"""
from collections import OrderedDict


class DuplicateDetector:
    def __init__(self, max_size: int = 10_000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._seen: OrderedDict[tuple[str, str], None] = OrderedDict()

    def is_duplicate(self, topic: str, event_id: str) -> bool:
        """True if already seen. Otherwise records it and returns False."""
        key = (topic, event_id)
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = None
        if len(self._seen) > self._max_size:
            self._seen.popitem(last=False)
        return False

    def __len__(self) -> int:
        return len(self._seen)
