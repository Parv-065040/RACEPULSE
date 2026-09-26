CREATE TABLE IF NOT EXISTS kpi_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    lap_number INT NOT NULL,
    lap_time_ms INT NOT NULL,
    best_lap_time_ms INT NOT NULL,
    delta_ms INT NOT NULL,
    severity VARCHAR(10) NOT NULL,
    event_time DATETIME(3) NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_event_kpi (event_id, kpi_id)
);