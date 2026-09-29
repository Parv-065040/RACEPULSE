"""Create all RACEPULSE Kafka topics deterministically."""
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

BOOTSTRAP="localhost:9092"
TOPICS={
"race.timing":3,"race.telemetry":3,"race.tyres":3,"race.weather":3,
"race.pitstops":3,"race.incidents":3,"business.fans":3,"business.sponsors":3,
"analytics.performance":3,"analytics.strategy":3,"analytics.commercial":3,
"analytics.alerts":3,"system.dlq":1,"system.audit":1,"system.config":1,
"system.health":1,
}
def main():
    admin=KafkaAdminClient(bootstrap_servers=BOOTSTRAP,client_id="racepulse-topic-init")
    try:
        created=0
        for name,partitions in TOPICS.items():
            try:
                admin.create_topics([NewTopic(name,num_partitions=partitions,replication_factor=1)])
                print(f"created {name} ({partitions} partitions)")
                created+=1
            except TopicAlreadyExistsError:
                print(f"exists  {name}")
        print(f"topic bootstrap complete: {created} created / {len(TOPICS)} declared")
    finally:
        admin.close()
if __name__=="__main__": main()
