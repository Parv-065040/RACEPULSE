-- Migration 002: alerts table (KPI-severity alerts + SYS-STALE stale-stream alerts)
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kpi_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    car_id VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message VARCHAR(255) NOT NULL,
    delta_ms INT NOT NULL,
    event_time DATETIME(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_event_kpi_alert (event_id, kpi_id)
);
