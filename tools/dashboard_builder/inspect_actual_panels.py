from pathlib import Path
import json

base = Path(r".\grafana\dashboards\generated")

wanted = {
    "RACEPACE // PACE DELTA",
    "EXECUTIVE ALERT FEED",
    "STRATEGY DECISION FEED",
    "LIVE PACE DELTA",
    "PERFORMANCE ALERT FEED",
    "RACE CONTROL ALERT FEED",
    "EXECUTIVE ALERT CONTEXT",
    "CONSUMER LAG",
    "INFRASTRUCTURE ALERT FEED",
    "DATA QUALITY / DLQ FEED",
}

for f in sorted(base.glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))

    for p in data.get("panels", []):
        title = str(p.get("title", "")).upper()

        if title in wanted:
            print("\n" + "=" * 100)
            print(f"{f.name} -> {p.get('title')}")
            print("=" * 100)

            print("TYPE:", p.get("type"))
            print("DATASOURCE:", p.get("datasource"))

            for t in p.get("targets", []):
                print("\nREF:", t.get("refId"))
                print("FORMAT:", t.get("format"))
                print("RAW SQL:")
                print(t.get("rawSql", "<NO RAW SQL>"))

            if p.get("transformations"):
                print("\nTRANSFORMATIONS:")
                for tr in p["transformations"]:
                    print(tr.get("id"), tr.get("options"))

            print("\nTIME OVERRIDE:", p.get("timeFrom"))
            print("TIME SHIFT:", p.get("timeShift"))
