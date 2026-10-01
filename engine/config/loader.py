"""
Live-reloading config loader - Parv's ownership (engine/config/).
Reads config/thresholds.yaml on a background thread every
RELOAD_INTERVAL_SECONDS. Validates before swapping in a new version;
an invalid file is rejected and the last valid config stays active
(failure-closed, per project requirements).
"""
import os
import threading
import time
import traceback
import yaml

CONFIG_PATH = "config/thresholds.yaml"
RELOAD_INTERVAL_SECONDS = 10

_lock = threading.Lock()
_current_config: dict = {}
_last_good_version = 0

REQUIRED_TOP_LEVEL_KEYS = {
    "lap_pace_delta",
    "gap_trend",
    "stale_stream_detection",
    "commercial",
}

def _validate(raw: dict) -> list[str]:
    errors = []
    missing = REQUIRED_TOP_LEVEL_KEYS - raw.keys()
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")
        return errors

    lpd = raw["lap_pace_delta"]
    if lpd["severity_thresholds"]["warning_ms"] >= lpd["severity_thresholds"]["critical_ms"]:
        errors.append("lap_pace_delta: warning_ms must be less than critical_ms")

    gt = raw["gap_trend"]
    if gt["severity_thresholds"]["widening_warning_ms_per_lap"] >= gt["severity_thresholds"]["widening_critical_ms_per_lap"]:
        errors.append("gap_trend: widening_warning_ms_per_lap must be less than widening_critical_ms_per_lap")

    commercial = raw["commercial"]
    for kpi_id in ("COM-001", "COM-003"):
        if kpi_id not in commercial:
            errors.append(f"commercial: missing {kpi_id}")
            continue
        block = commercial[kpi_id]
        if block["warning"] >= block["critical"]:
            errors.append(f"commercial {kpi_id}: warning must be less than critical")
        if block["warning"] < 0 or block["critical"] < 0:
            errors.append(f"commercial {kpi_id}: thresholds must be non-negative")

    return errors

def _load_once() -> None:
    global _current_config, _last_good_version
    absolute_path = os.path.abspath(CONFIG_PATH)
    print(f"[config-watcher] cwd={os.getcwd()}  reading={absolute_path}", flush=True)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        print(f"CONFIG RELOAD FAILED (file read/parse error): {e} -- keeping last valid config (v{_last_good_version})", flush=True)
        return

    print(f"[config-watcher] file says warning_ms={raw['lap_pace_delta']['severity_thresholds']['warning_ms']}  version={raw['lap_pace_delta']['version']}", flush=True)

    errors = _validate(raw)
    if errors:
        print(f"CONFIG RELOAD REJECTED: {errors} -- keeping last valid config (v{_last_good_version})", flush=True)
        return

    with _lock:
        if raw != _current_config:
            _last_good_version += 1
            _current_config = raw
            print(f"CONFIG RELOADED successfully -- now v{_last_good_version}", flush=True)
        else:
            print(f"[config-watcher] no change detected (still v{_last_good_version})", flush=True)

def get_config() -> dict:
    with _lock:
        return _current_config

def _reload_loop() -> None:
    print("[config-watcher] background reload thread started", flush=True)
    while True:
        time.sleep(RELOAD_INTERVAL_SECONDS)
        try:
            _load_once()
        except Exception:
            print("[config-watcher] UNEXPECTED EXCEPTION in reload loop:", flush=True)
            traceback.print_exc()

def start_config_watcher() -> None:
    """Loads the config once synchronously, then starts a background reload thread."""
    _load_once()
    if not _current_config:
        raise RuntimeError(f"Could not load initial config from {CONFIG_PATH} -- cannot start.")
    thread = threading.Thread(target=_reload_loop, daemon=True)
    thread.start()