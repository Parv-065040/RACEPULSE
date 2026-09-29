CREATE TABLE IF NOT EXISTS commercial_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    lap_number INT NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message VARCHAR(255) NOT NULL,
    event_time DATETIME(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_commercial_event_kpi (event_id, kpi_id)
);
