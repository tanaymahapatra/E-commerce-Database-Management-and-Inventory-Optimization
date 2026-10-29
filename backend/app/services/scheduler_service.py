import logging
from threading import Lock
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks

from auto_scheduler.config import (
    CRON_DAY_OF_WEEK,
    CRON_HOUR,
    CRON_MINUTE,
)
from auto_scheduler.pipeline import run_weekly_pipeline

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("Asia/Kolkata")
JOB_ID = "weekly_ml_pipeline"

scheduler = BackgroundScheduler(timezone=TIMEZONE)
_run_lock = Lock()


# 1. Execute the original ML pipeline
def _execute_pipeline(triggered_by: str) -> None:
    try:
        result = run_weekly_pipeline(triggered_by=triggered_by)

        if result.get("status") == "FAILED":
            logger.error("Forecast pipeline failed: %s", result.get("error"))

    except Exception:
        logger.exception("Forecast pipeline crashed")

    finally:
        _run_lock.release()


# 2. Automatically execute on schedule
def _scheduled_run() -> None:
    if not _run_lock.acquire(blocking=False):
        logger.warning("Skipping scheduled run: pipeline already running")
        return

    _execute_pipeline("scheduler")


# 3. Start APScheduler
def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        _scheduled_run,
        trigger=CronTrigger(
            day_of_week=CRON_DAY_OF_WEEK,
            hour=CRON_HOUR,
            minute=CRON_MINUTE,
            timezone=TIMEZONE,
        ),
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("Weekly forecast scheduler started")


# 4. Stop APScheduler
def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


# 5. Manual triggering
def trigger_manual_run(background_tasks: BackgroundTasks) -> bool:

    if not _run_lock.acquire(blocking=False):
        return False

    background_tasks.add_task(_execute_pipeline, "manual")

    return True


# 6. Check execution state
def pipeline_is_running() -> bool:
    return _run_lock.locked()


# 7. Get next scheduled execution
def next_run_at():
    job = scheduler.get_job(JOB_ID)
    return job.next_run_time if job else None
