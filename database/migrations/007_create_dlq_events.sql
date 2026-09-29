CREATE TABLE IF NOT EXISTS dlq_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_topic VARCHAR(100) NOT NULL,
    raw_key VARCHAR(255) NULL,
    errors TEXT NOT NULL,
    failed_at DATETIME(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dlq_failed_at (failed_at)
);
