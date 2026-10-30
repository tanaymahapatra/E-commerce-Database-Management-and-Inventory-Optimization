CREATE TABLE IF NOT EXISTS scheduler_runs (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    triggered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    triggered_by VARCHAR(20) NOT NULL DEFAULT 'scheduler',
    run_date_anchor DATE NOT NULL,
    model_used VARCHAR(30) NULL,
    training_weeks INT NULL,
    wmape DECIMAL(8,4) NULL,
    rmse DECIMAL(12,4) NULL,
    forecast_accuracy DECIMAL(8,4) NULL,
    records_written INT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'RUNNING',
    error_message TEXT NULL
);
