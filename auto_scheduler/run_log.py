"""
run_log.py
==========
Records every pipeline run (automated or manual) into the
`scheduler_runs` table.

Usage pattern
-------------
1. Call open_run()  at the START  of the pipeline → get a run_id.
2. Call close_run() at the END    of the pipeline → mark SUCCESS / FAILED.

This two-step approach means the row exists in the DB even if the
pipeline crashes mid-way, making it easy to diagnose failures.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import text

from .db import get_engine

logger = logging.getLogger(__name__)

_OPEN_RUN_SQL = text("""
INSERT INTO scheduler_runs
    (triggered_at, triggered_by, run_date_anchor, status)
VALUES
    (:triggered_at, :triggered_by, :run_date_anchor, 'RUNNING');
""")

_CLOSE_RUN_SQL = text("""
UPDATE scheduler_runs
SET
    completed_at     = :completed_at,
    model_used       = :model_used,
    training_weeks   = :training_weeks,
    wmape            = :wmape,
    rmse             = :rmse,
    forecast_accuracy = :forecast_accuracy,
    records_written  = :records_written,
    status           = :status,
    error_message    = :error_message
WHERE run_id = :run_id;
""")


def open_run(
    run_date_anchor: datetime,
    triggered_by: str = "scheduler",
) -> Optional[int]:
    """
    Insert an OPEN run record and return the new run_id.

    Returns None if the insert fails (non-fatal — the pipeline still runs).
    """
    engine = get_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                _OPEN_RUN_SQL,
                {
                    "triggered_at":    datetime.utcnow().isoformat(sep=" "),
                    "triggered_by":    triggered_by,
                    "run_date_anchor": run_date_anchor.date().isoformat(),
                },
            )
            run_id = result.lastrowid
        logger.info("Opened run_id=%d (triggered_by=%s).", run_id, triggered_by)
        return run_id
    except Exception as exc:
        logger.warning("Could not open run log: %s", exc)
        return None
    finally:
        engine.dispose()


def close_run(
    run_id:           Optional[int],
    *,
    model_used:       str,
    training_weeks:   int,
    wmape:            float,
    rmse:             float,
    forecast_accuracy: float,
    records_written:  int,
    status:           str,          # "SUCCESS" or "FAILED"
    error_message:    Optional[str] = None,
) -> None:
    """
    Update the run record with final metrics and status.

    If run_id is None (open_run failed), this is a no-op.
    """
    if run_id is None:
        return

    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                _CLOSE_RUN_SQL,
                {
                    "run_id":           run_id,
                    "completed_at":     datetime.utcnow().isoformat(sep=" "),
                    "model_used":       model_used,
                    "training_weeks":   training_weeks,
                    "wmape":            round(wmape, 4),
                    "rmse":             round(rmse, 4),
                    "forecast_accuracy": round(forecast_accuracy, 4),
                    "records_written":  records_written,
                    "status":           status,
                    "error_message":    error_message,
                },
            )
        logger.info(
            "Closed run_id=%d  status=%s  model=%s  accuracy=%.2f%%",
            run_id, status, model_used, forecast_accuracy,
        )
    except Exception as exc:
        logger.warning("Could not close run log for run_id=%d: %s", run_id, exc)
    finally:
        engine.dispose()
