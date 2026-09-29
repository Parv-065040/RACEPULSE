"""
Shared fixtures for integration tests - Parv's ownership (tests/integration/).

These tests require the real Docker stack (Kafka + MySQL) to be running,
since they test actual database writes and actual Kafka message delivery,
not mocked behavior. If the stack isn't up, tests are skipped with a clear
reason instead of failing with a raw connection-refused traceback.

Run with the stack up: docker compose up -d, then:
    pytest tests/integration -v
"""
import socket
import pytest


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


KAFKA_UP = _port_open("localhost", 9092)
MYSQL_UP = _port_open("localhost", 3306)

requires_kafka = pytest.mark.skipif(
    not KAFKA_UP, reason="Kafka not reachable on localhost:9092 - run 'docker compose up -d' first"
)
requires_mysql = pytest.mark.skipif(
    not MYSQL_UP, reason="MySQL not reachable on localhost:3306 - run 'docker compose up -d' first"
)
