from tools.dashboard_builder import production

queries = {
    "PACE": production.PACE,
    "STRATEGY_RISK": production.STRATEGY_RISK,
    "STRATEGY_FEED": production.STRATEGY_FEED,
    "ALERT_FEED": production.ALERT_FEED,
    "RACE_CONTROL_FEED": production.RACE_CONTROL_FEED,
    "PERFORMANCE_ALERTS": production.PERFORMANCE_ALERTS,
    "DLQ_TIMELINE": production.DLQ_TIMELINE,
    "DATA_QUALITY": production.DATA_QUALITY,
    "INFRA_FEED": production.INFRA_FEED,
}

for name, sql in queries.items():
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print(sql)
