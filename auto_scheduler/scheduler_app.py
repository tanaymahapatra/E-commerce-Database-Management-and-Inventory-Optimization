"""
scheduler_app.py
================
Standalone FastAPI application for the auto-scheduler.

What this provides
------------------
• APScheduler fires run_weekly_pipeline() every Sunday at 02:00.
• Three API endpoints for visibility and manual control:

    GET  /scheduler/status    → last run summary (model, accuracy, timestamp)
    POST /scheduler/trigger   → manually fire the pipeline right now
    GET  /scheduler/history   → last N run records from scheduler_runs

Run this app separately from the main backend (different port), or
integrate it by importing the router into your main FastAPI app.

How to run standalone
---------------------
  cd "d:\\DBMS Project\\E-commerce-Database-Management-and-Inventory-Optimization"
  python -m uvicorn auto_scheduler.scheduler_app:app --host 0.0.0.0 --port 8001 --reload

How to integrate into existing main.py (optional, do NOT modify main.py)
------------------------------------------------------------------------
  from auto_scheduler.scheduler_app import app as scheduler_app
  # or just import the router and lifespan separately
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from sqlalchemy import text

from .config import (
    CRON_DAY_OF_WEEK,
    CRON_HOUR,
    CRON_MINUTE,
)
from .db       import get_engine
from .pipeline import run_weekly_pipeline

logger = logging.getLogger(__name__)

# ── APScheduler instance ──────────────────────────────────────────────────────
scheduler = BackgroundScheduler()


# ── Lifespan: start/stop scheduler alongside FastAPI ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting APScheduler — cron: %s %02d:%02d",
        CRON_DAY_OF_WEEK, CRON_HOUR, CRON_MINUTE,
    )
    scheduler.add_job(
        func=run_weekly_pipeline,
        trigger=CronTrigger(
            day_of_week=CRON_DAY_OF_WEEK,
            hour=CRON_HOUR,
            minute=CRON_MINUTE,
        ),
        id="weekly_ml_pipeline",
        name="Weekly ML Forecast Pipeline",
        replace_existing=True,
        kwargs={"triggered_by": "scheduler"},
    )
    scheduler.start()
    logger.info("APScheduler started.")
    yield
    logger.info("Shutting down APScheduler…")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Auto Scheduler — Inventory Forecast",
    description=(
        "Runs the weekly ML pipeline every Sunday and provides "
        "endpoints to check status, trigger manually, and view history."
    ),
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/scheduler/status", summary="Last run summary")
def get_status():
    """
    Returns the most recent run record from scheduler_runs.
    Shows: when it ran, which model won, accuracy, and how many
    rows were written to the recommendation table.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT
                        run_id, triggered_at, completed_at, triggered_by,
                        run_date_anchor, model_used, training_weeks,
                        wmape, rmse, forecast_accuracy, records_written, status
                    FROM scheduler_runs
                    ORDER BY run_id DESC
                    LIMIT 1;
                """)
            ).mappings().first()
    finally:
        engine.dispose()

    if row is None:
        return {"message": "No runs recorded yet. Try POST /scheduler/trigger to run now."}

    return dict(row)


@app.post("/scheduler/trigger", summary="Manually trigger the pipeline")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Fire the ML pipeline immediately in the background.
    Returns instantly; use GET /scheduler/status to check the result.
    """
    logger.info("Manual trigger received via API.")
    background_tasks.add_task(run_weekly_pipeline, triggered_by="manual")
    return {
        "message": "Pipeline triggered in the background.",
        "hint":    "Poll GET /scheduler/status in a few minutes to see the result.",
    }


@app.get("/scheduler/history", summary="Last N run records")
def get_history(limit: int = Query(default=10, ge=1, le=100)):
    """
    Returns the last `limit` rows from scheduler_runs, newest first.
    Useful for spotting repeated failures or accuracy trends over time.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT
                        run_id, triggered_at, completed_at, triggered_by,
                        run_date_anchor, model_used, training_weeks,
                        wmape, rmse, forecast_accuracy, records_written,
                        status, error_message
                    FROM scheduler_runs
                    ORDER BY run_id DESC
                    LIMIT :lim;
                """),
                {"lim": limit},
            ).mappings().all()
    finally:
        engine.dispose()

    return {
        "total_returned": len(rows),
        "runs":           [dict(r) for r in rows],
    }


@app.get("/scheduler/next-run", summary="When will the next automatic run fire?")
def get_next_run():
    """Returns the scheduled next-run time for the weekly pipeline job."""
    job = scheduler.get_job("weekly_ml_pipeline")
    if job is None:
        raise HTTPException(status_code=404, detail="Scheduler job not found.")
    return {
        "job_id":      job.id,
        "job_name":    job.name,
        "next_run_at": str(job.next_run_time),
    }
