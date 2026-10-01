-- Migration 008: 15-second tumbling-window KPI results
--
-- KPI-003 = Average Vehicle Speed
-- One row represents one completed event-time window for one car.

CREATE TABLE IF NOT EXISTS windowed_kpi_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    window_id VARCHAR(100) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    window_start DATETIME(3) NOT NULL,
    window_end DATETIME(3) NOT NULL,
    event_count INT NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_windowed_kpi (
        kpi_id,
        window_id,
        car_id
    ),

    INDEX idx_windowed_kpi_time (
        window_start
    ),

    INDEX idx_windowed_kpi_car (
        car_id,
        window_start
    )
);
