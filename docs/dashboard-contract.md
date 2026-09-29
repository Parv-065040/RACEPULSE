# RACEPULSE Dashboard Contract

All dashboards use the provisioned RACEPULSE MySQL datasource and refresh every 5 seconds.

## Executive Command Center

Question: What is the current state of the race and platform?

- Latest lap
- Critical alerts
- Strategy signals
- Commercial events
- Current race signals
- Latest alerts
- Strategy risk trend
- Commercial activity

## Race Operations

Question: What is happening on track?

- Latest lap
- Critical alerts
- Track risk
- Vehicle risk
- Live pace and gap
- Race-control alerts
- Lap pace delta
- Gap trend

## Strategy

Question: Which strategy conditions require investigation?

- Critical/warning signals
- Pit-window signals
- Latest tyre risk
- Strategy signal table
- Tyre/strategy risk trend
- Pit-window trend

## Commercial Intelligence

Question: What is happening with fan and sponsor activity?

- Fan events
- Sponsor exposure
- Engagement rate
- Visibility
- Sponsor exposure table
- Fan engagement table
- Engagement trend
- Visibility trend

## Streaming Engineering

Question: Is the streaming platform itself healthy?

- DLQ records
- Recent health samples
- Critical alerts
- Health warnings
- Consumer-group lag
- System alerts

## Rule

Dashboards visualize persisted analytical facts. Grafana SQL must not invent KPI values that are not defined by the corresponding consumer.
