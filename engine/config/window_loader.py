"""
Live-reloading configuration for event-time tumbling windows.

Reads config/windows.yaml independently from the threshold watcher.
Invalid configuration is rejected and the last valid configuration
remains active.

Tumbling-window configuration includes:
- default/standard window sizes
- allowed event-time lateness
- idle-stream finalization timeout
"""

from __future__ import annotations

import os
import threading
import time
import traceback

import yaml


CONFIG_PATH = "config/windows.yaml"
RELOAD_INTERVAL_SECONDS = 5

_lock = threading.Lock()
_current_config: dict = {}
_last_good_version = 0


def _validate(raw: dict) -> list[str]:
    errors = []

    if not isinstance(raw, dict):
        return ["windows configuration must be a mapping"]

    tumbling = raw.get("tumbling")

    if not isinstance(tumbling, dict):
        return ["missing top-level tumbling configuration"]

    required = {
        "default_seconds",
        "short_seconds",
        "medium_seconds",
        "long_seconds",
        "allowed_lateness_seconds",
        "idle_flush_seconds",
    }

    missing = required - tumbling.keys()

    if missing:
        errors.append(
            f"tumbling: missing keys: {sorted(missing)}"
        )
        return errors

    # Standard window sizes must be positive integers.
    for key in (
        "default_seconds",
        "short_seconds",
        "medium_seconds",
        "long_seconds",
    ):
        value = tumbling[key]

        if not isinstance(value, int):
            errors.append(
                f"tumbling.{key}: must be an integer"
            )
            continue

        if value < 1:
            errors.append(
                f"tumbling.{key}: must be greater than 0"
            )

    # Allowed lateness may legitimately be zero.
    value = tumbling["allowed_lateness_seconds"]

    if not isinstance(value, int):
        errors.append(
            "tumbling.allowed_lateness_seconds: "
            "must be an integer"
        )
    elif value < 0:
        errors.append(
            "tumbling.allowed_lateness_seconds: "
            "must be >= 0"
        )

    # Idle flush must be positive because zero would cause
    # continuous immediate finalization.
    value = tumbling["idle_flush_seconds"]

    if not isinstance(value, int):
        errors.append(
            "tumbling.idle_flush_seconds: "
            "must be an integer"
        )
    elif value < 1:
        errors.append(
            "tumbling.idle_flush_seconds: "
            "must be at least 1"
        )

    return errors


def _load_once() -> None:
    global _current_config, _last_good_version

    absolute_path = os.path.abspath(CONFIG_PATH)

    try:
        with open(
            CONFIG_PATH,
            "r",
            encoding="utf-8-sig",
        ) as f:
            raw = yaml.safe_load(f)
    except Exception as exc:
        print(
            f"[window-config] reload failed: {exc} "
            f"-- keeping v{_last_good_version}",
            flush=True,
        )
        return

    errors = _validate(raw)

    if errors:
        print(
            f"[window-config] rejected: {errors} "
            f"-- keeping v{_last_good_version}",
            flush=True,
        )
        return

    with _lock:
        if raw != _current_config:
            _last_good_version += 1
            _current_config = raw

            print(
                f"[window-config] reloaded successfully "
                f"-- default="
                f"{raw['tumbling']['default_seconds']}s "
                f"-- idle-flush="
                f"{raw['tumbling']['idle_flush_seconds']}s "
                f"-- v{_last_good_version}",
                flush=True,
            )
        else:
            print(
                f"[window-config] no change "
                f"-- still v{_last_good_version}",
                flush=True,
            )


def get_window_config() -> dict:
    with _lock:
        return _current_config.copy()


def get_default_window_seconds() -> int:
    with _lock:
        return _current_config[
            "tumbling"
        ]["default_seconds"]


def get_allowed_lateness_seconds() -> int:
    with _lock:
        return _current_config[
            "tumbling"
        ]["allowed_lateness_seconds"]


def get_idle_flush_seconds() -> int:
    with _lock:
        return _current_config[
            "tumbling"
        ]["idle_flush_seconds"]


def _reload_loop() -> None:
    while True:
        time.sleep(RELOAD_INTERVAL_SECONDS)

        try:
            _load_once()
        except Exception:
            print(
                "[window-config] unexpected reload exception:",
                flush=True,
            )
            traceback.print_exc()


def start_window_config_watcher() -> None:
    """Load configuration synchronously and start background watcher."""

    _load_once()

    if not _current_config:
        raise RuntimeError(
            f"Could not load initial configuration "
            f"from {CONFIG_PATH}"
        )

    thread = threading.Thread(
        target=_reload_loop,
        daemon=True,
    )

    thread.start()