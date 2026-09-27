"""
Reusable rolling-window state tracker - Parv's ownership (engine/windows/).

Generalizes the per-entity rolling window pattern originally built inline
inside KPI-002 (Gap Trend), so future windowed KPIs (e.g. a rolling average
speed, a rolling tyre-degradation slope) can reuse this instead of each
formula module hand-rolling its own deque bookkeeping and window-resize
handling.

This does not change KPI-002's behavior - it is a structural extraction,
not a formula change. Same values in, same values out.
"""
from collections import deque


class RollingWindow:
    """
    Tracks a rolling window of values per entity_id (e.g. car_id).

    Supports live window-size changes (so this stays compatible with
    dynamic config reload): resize() truncates/reinitializes each
    entity's history to the new size, keeping the most recent values.
    """

    def __init__(self, window_size: int):
        if window_size < 2:
            raise ValueError("window_size must be at least 2 to compute a trend")
        self.window_size = window_size
        self._history: dict[str, deque] = {}

    def push(self, entity_id: str, value) -> None:
        """Add a new value for entity_id, evicting the oldest if the window is full."""
        history = self._history.get(entity_id)
        if history is None or history.maxlen != self.window_size:
            existing = list(history) if history is not None else []
            history = deque(existing[-self.window_size:], maxlen=self.window_size)
            self._history[entity_id] = history
        history.append(value)

    def get(self, entity_id: str) -> list:
        """Return the current window contents for entity_id, oldest first."""
        return list(self._history.get(entity_id, []))

    def is_full(self, entity_id: str) -> bool:
        """True once entity_id has at least 2 values (enough to compute a trend)."""
        return len(self._history.get(entity_id, [])) >= 2

    def set_window_size(self, window_size: int) -> None:
        """
        Call when config changes window_size live. Existing histories are
        resized (truncated to the most recent `window_size` values) the
        next time push() is called for each entity, not immediately -
        this avoids surprising behavior for entities not seen since the change.
        """
        if window_size < 2:
            raise ValueError("window_size must be at least 2 to compute a trend")
        self.window_size = window_size
