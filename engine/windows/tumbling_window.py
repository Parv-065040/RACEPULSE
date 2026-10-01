"""
Event-time tumbling window engine.

Windows are non-overlapping and keyed by entity.
Example with 15 seconds:

00:00–00:14.999 -> window 1
00:15–00:29.999 -> window 2
00:30–00:44.999 -> window 3

The window is selected from event_time, not Kafka arrival time.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class WindowResult:
    entity_id: str
    window_start: datetime
    window_end: datetime
    events: list[dict[str, Any]]

    @property
    def count(self) -> int:
        return len(self.events)


class TumblingWindow:
    """
    Non-overlapping event-time tumbling windows.

    Events are stored by entity and window start.
    When an event arrives in a newer window, completed older windows
    for that entity are emitted.
    """

    def __init__(self, window_seconds: int = 15):
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        self.window_seconds = window_seconds
        self.window_size = window_seconds
        self._windows: dict[
            str, dict[datetime, list[dict[str, Any]]]
        ] = defaultdict(lambda: defaultdict(list))

    def _parse_event_time(self, event_time: str | datetime) -> datetime:
        if isinstance(event_time, datetime):
            dt = event_time
        else:
            dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    def _window_start(self, event_time: datetime) -> datetime:
        epoch = int(event_time.timestamp())
        start_epoch = (
            epoch // self.window_seconds
        ) * self.window_seconds

        return datetime.fromtimestamp(
            start_epoch,
            tz=timezone.utc,
        )

    def add(
        self,
        entity_id: str,
        event_time: str | datetime,
        event: dict[str, Any],
    ) -> list[WindowResult]:
        """
        Add an event and emit completed windows for the entity.

        Returns zero or more completed windows.
        """
        dt = self._parse_event_time(event_time)
        current_start = self._window_start(dt)

        entity_windows = self._windows[entity_id]
        entity_windows[current_start].append(event)

        completed: list[WindowResult] = []

        for window_start in sorted(list(entity_windows)):
            if window_start < current_start:
                events = entity_windows.pop(window_start)

                completed.append(
                    WindowResult(
                        entity_id=entity_id,
                        window_start=window_start,
                        window_end=window_start.replace(
                            microsecond=0
                        ).__class__.fromtimestamp(
                            window_start.timestamp()
                            + self.window_seconds,
                            tz=timezone.utc,
                        ),
                        events=events,
                    )
                )

        return completed

    def advance_watermark(
        self,
        entity_id: str,
        watermark_time: str | datetime,
    ) -> list[WindowResult]:
        """
        Emit windows whose end time is at or before the watermark.

        The watermark represents the latest event-time boundary that the
        caller considers complete. Windows are emitted only when their
        end
        time is <= watermark_time.
        """
        watermark = self._parse_event_time(watermark_time)

        entity_windows = self._windows.get(entity_id, {})
        completed: list[WindowResult] = []

        for window_start in sorted(list(entity_windows)):
            window_end = datetime.fromtimestamp(
                window_start.timestamp() + self.window_seconds,
                tz=timezone.utc,
            )

            if window_end <= watermark:
                events = entity_windows.pop(window_start)

                completed.append(
                    WindowResult(
                        entity_id=entity_id,
                        window_start=window_start,
                        window_end=window_end,
                        events=events,
                    )
                )

        return completed
    
    def flush(self, entity_id: str | None = None) -> list[WindowResult]:
        """
        Flush currently open windows.

        Useful for controlled shutdowns and deterministic tests.
        """
        results: list[WindowResult] = []

        entity_ids = (
            [entity_id]
            if entity_id is not None
            else list(self._windows.keys())
        )

        for current_entity in entity_ids:
            entity_windows = self._windows.get(current_entity, {})

            for window_start in sorted(entity_windows):
                events = entity_windows[window_start]

                results.append(
                    WindowResult(
                        entity_id=current_entity,
                        window_start=window_start,
                        window_end=datetime.fromtimestamp(
                            window_start.timestamp()
                            + self.window_seconds,
                            tz=timezone.utc,
                        ),
                        events=events,
                    )
                )

            if current_entity in self._windows:
                self._windows[current_entity].clear()

        return results

    def resize(self, window_seconds: int) -> None:
        """
        Change the window size for future events.

        Existing open windows are intentionally flushed before resize
        so events from different window definitions are never mixed.
        """
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        self.window_seconds = window_seconds
        self.window_size = window_seconds
        self._windows.clear()
