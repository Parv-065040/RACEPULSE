from tools.dashboard_builder import production

queries = {
    "CURRENT_CAR_STATUS": production.CURRENT_CAR_STATUS,
    "RACE_CONTROL_MATRIX": production.RACE_CONTROL_MATRIX,
    "LATEST_LAP": production.LATEST_LAP,
    "CRITICAL_ALERTS": production.CRITICAL_ALERTS,
    "STRATEGY_SIGNALS": production.STRATEGY_SIGNALS,
    "COMMERCIAL_EVENTS": production.COMMERCIAL_EVENTS,
}

for name, sql in queries.items():
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print(sql)
