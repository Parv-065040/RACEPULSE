from pathlib import Path
import json

base = Path(r".\grafana\dashboards\generated")

wanted = {
    "Race Pace // Pace Delta",
    "Executive Alert Feed",
    "Strategy Decision Feed",
    "Live Pace Delta",
    "Performance Alert Feed",
    "Race Control Alert Feed",
    "Executive Alert Context",
    "Consumer Lag",
    "Infrastructure Alert Feed",
    "Data Quality / DLQ Feed",
}

for f in sorted(base.glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))

    for p in data.get("panels", []):
        title = p.get("title", "")
        if title in wanted:
            print("\n" + "=" * 100)
            print(f"{f.name}  ->  {title}")
            print("=" * 100)

            print("TYPE:", p.get("type"))
            print("DATASOURCE:", p.get("datasource"))
            print("FORMAT:", p.get("targets", [{}])[0].get("format"))

            for t in p.get("targets", []):
                print("\nREF:", t.get("refId"))
                print("FORMAT:", t.get("format"))
                print("RAW SQL:")
                print(t.get("rawSql", "<NO RAW SQL>"))

            if p.get("transformations"):
                print("\nTRANSFORMATIONS:")
                for tr in p["transformations"]:
                    print(tr.get("id"), tr.get("options"))

            print("\nFIELD CONFIG:")
            print(p.get("fieldConfig", {}))
