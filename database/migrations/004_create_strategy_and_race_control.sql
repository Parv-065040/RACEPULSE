CREATE TABLE IF NOT EXISTS strategy_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    lap_number INT NOT NULL,
    value FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message VARCHAR(255) NOT NULL,
    event_time DATETIME(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_strategy_event_kpi (event_id, kpi_id)
);

CREATE TABLE IF NOT EXISTS race_control_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    lap_number INT NOT NULL,
    value FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message VARCHAR(255) NOT NULL,
    event_time DATETIME(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_race_control_event_kpi (event_id, kpi_id)
);
