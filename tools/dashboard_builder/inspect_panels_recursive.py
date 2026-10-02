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

def walk(obj, path="root"):
    if isinstance(obj, dict):
        if obj.get("title") in wanted:
            yield path, obj
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")

for f in sorted(base.glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))

    for path, p in walk(data):
        print("\n" + "=" * 110)
        print(f"{f.name} -> {p}")
        print("=" * 110)

        print("TITLE:", p.get("title"))
        print("TYPE:", p.get("type"))
        print("DATASOURCE:", p.get("datasource"))

        targets = p.get("targets", [])
        print("TARGET COUNT:", len(targets))

        for t in targets:
            print("\nREF:", t.get("refId"))
            print("FORMAT:", t.get("format"))
            print("RAW SQL:")
            print(t.get("rawSql", "<NO RAW SQL>"))

        transformations = p.get("transformations", [])
        if transformations:
            print("\nTRANSFORMATIONS:")
            for tr in transformations:
                print(tr.get("id"), tr.get("options"))

        print("\nFIELD CONFIG:")
        print(p.get("fieldConfig", {}))

        print("\nOPTIONS:")
        print(p.get("options", {}))
