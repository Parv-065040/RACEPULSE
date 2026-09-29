CREATE TABLE IF NOT EXISTS stream_health (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    topic VARCHAR(100) NULL,
    consumer_group VARCHAR(150) NULL,
    lag BIGINT NULL,
    events_seen BIGINT NULL,
    last_event_at DATETIME(3) NULL,
    status VARCHAR(20) NOT NULL,
    message VARCHAR(255) NOT NULL,
    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stream_health_observed (observed_at),
    INDEX idx_stream_health_component (component)
);

CREATE TABLE IF NOT EXISTS infra_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    signal VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message VARCHAR(255) NOT NULL,
    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
