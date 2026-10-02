#!/bin/bash
set -e

echo "Waiting for Kafka..."

until kafka-topics --bootstrap-server kafka:29092 --list >/dev/null 2>&1
do
    sleep 2
done

echo "Kafka is ready."

for topic in \
    race.timing \
    race.telemetry \
    race.tyres \
    race.weather \
    race.pitstops \
    race.incidents \
    business.fans \
    business.sponsors \
    system.dlq \
    analytics.alerts
do
    echo "Creating/checking topic: $topic"

    kafka-topics \
        --bootstrap-server kafka:29092 \
        --create \
        --if-not-exists \
        --topic "$topic" \
        --partitions 3 \
        --replication-factor 1
done

echo "All RACEPULSE topics initialized."
