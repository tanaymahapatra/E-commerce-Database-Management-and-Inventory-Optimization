-- ============================================================
-- Table: scheduler_runs
-- Tracks every automated (or manual) pipeline run.
-- Run this once against your database to create the table.
-- ============================================================

CREATE TABLE IF NOT EXISTS scheduler_runs (
    run_id           INT AUTO_INCREMENT PRIMARY KEY,

    -- When the job started and finished
    triggered_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at     DATETIME     NULL,

    -- "scheduler" (automatic Sunday run) or "manual" (API trigger)
    triggered_by     VARCHAR(20)  NOT NULL DEFAULT 'scheduler',

    -- Sunday date the forecast weeks are anchored to
    run_date_anchor  DATE         NOT NULL,

    -- Which model won the accuracy comparison
    model_used       VARCHAR(30)  NULL,

    -- Training window actually used
    training_weeks   INT          NULL,

    -- Output metrics of the winning model
    wmape            DECIMAL(8,4) NULL,
    rmse             DECIMAL(12,4) NULL,
    forecast_accuracy DECIMAL(8,4) NULL,

    -- How many rows were upserted into the recommendation table
    records_written  INT          NULL,

    -- "RUNNING", "SUCCESS", or "FAILED"
    status           VARCHAR(10)  NOT NULL DEFAULT 'RUNNING',

    -- Null on success; populated with the exception message on failure
    error_message    TEXT         NULL
);
