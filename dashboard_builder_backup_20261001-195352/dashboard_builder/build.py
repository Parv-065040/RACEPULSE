"""Build RACEPULSE Grafana dashboards from Python definitions."""

from __future__ import annotations

import json
from pathlib import Path

from .executive import build as build_executive


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "grafana" / "dashboards" / "generated"


DASHBOARDS = {
    "racepulse-ceo-command-center.json": build_executive,
}


def validate_dashboard(dashboard: dict) -> None:
    """Perform structural validation before writing Grafana JSON."""

    required = {
        "uid",
        "title",
        "schemaVersion",
        "panels",
        "time",
        "refresh",
    }

    missing = required - dashboard.keys()

    if missing:
        raise ValueError(
            f"Dashboard {dashboard.get('title', '<unknown>')} "
            f"is missing required fields: {sorted(missing)}"
        )

    if not isinstance(dashboard["panels"], list):
        raise TypeError("dashboard.panels must be a list")

    if not dashboard["panels"]:
        raise ValueError("dashboard must contain at least one panel")

    for index, panel in enumerate(dashboard["panels"]):
        for field in ("type", "title", "gridPos"):
            if field not in panel:
                raise ValueError(
                    f"Panel {index} is missing required field '{field}'"
                )

        grid = panel["gridPos"]

        for field in ("x", "y", "w", "h"):
            if field not in grid:
                raise ValueError(
                    f"Panel {index} gridPos missing '{field}'"
                )

        if grid["x"] < 0 or grid["x"] + grid["w"] > 24:
            raise ValueError(
                f"Panel {index} exceeds 24-column grid: {grid}"
            )

        if grid["w"] <= 0 or grid["h"] <= 0:
            raise ValueError(
                f"Panel {index} has invalid dimensions: {grid}"
            )


def write_dashboard(filename: str, builder) -> Path:
    dashboard = builder()

    validate_dashboard(dashboard)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / filename

    output_path.write_text(
        json.dumps(
            dashboard,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    print("=" * 70)
    print("RACEPULSE DASHBOARD BUILDER")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, builder in DASHBOARDS.items():
        output_path = write_dashboard(filename, builder)

        dashboard = json.loads(
            output_path.read_text(encoding="utf-8")
        )

        print(
            f"[OK] {dashboard['title']}: "
            f"{len(dashboard['panels'])} panels"
        )
        print(f"     {output_path}")

    print("=" * 70)
    print("Dashboard generation complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
