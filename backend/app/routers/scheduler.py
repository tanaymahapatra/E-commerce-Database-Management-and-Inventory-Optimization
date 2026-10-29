from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.scheduler import (
    SchedulerHistoryResponse,
    SchedulerNextRunResponse,
    SchedulerStatusResponse,
    SchedulerTriggerResponse,
)
from ..services.scheduler_service import (
    JOB_ID,
    next_run_at,
    pipeline_is_running,
    scheduler,
    trigger_manual_run,
)

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# 1. Get latest scheduler run
@router.get("/status", response_model=SchedulerStatusResponse)
def get_status(db: Session = Depends(get_db)):

    row = db.execute(text("""
            SELECT
                run_id,
                triggered_at,
                completed_at,
                triggered_by,
                run_date_anchor,
                model_used,
                training_weeks,
                wmape,
                rmse,
                forecast_accuracy,
                records_written,
                status,
                error_message
            FROM scheduler_runs
            ORDER BY run_id DESC
            LIMIT 1
        """)).mappings().first()

    return {
        "scheduler_running": scheduler.running,
        "pipeline_running": pipeline_is_running(),
        "last_run": dict(row) if row else None,
    }


# 2. Get scheduler history
@router.get("/history", response_model=SchedulerHistoryResponse)
def get_history(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):

    rows = (
        db.execute(
            text("""
            SELECT
                run_id,
                triggered_at,
                completed_at,
                triggered_by,
                run_date_anchor,
                model_used,
                training_weeks,
                wmape,
                rmse,
                forecast_accuracy,
                records_written,
                status,
                error_message
            FROM scheduler_runs
            ORDER BY run_id DESC
            LIMIT :limit
        """),
            {"limit": limit},
        )
        .mappings()
        .all()
    )

    return {"total_returned": len(rows), "runs": [dict(row) for row in rows]}


# 3. Check next scheduled run
@router.get("/next-run", response_model=SchedulerNextRunResponse)
def get_next_run():

    return {"job_id": JOB_ID, "next_run_at": next_run_at(), "timezone": "Asia/Kolkata"}


# 4. Trigger the forecasting pipeline manually
@router.post(
    "/trigger",
    response_model=SchedulerTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_pipeline(background_tasks: BackgroundTasks):

    if not trigger_manual_run(background_tasks):
        raise HTTPException(
            status_code=409, detail="A forecast pipeline run is already in progress"
        )

    return {
        "message": "Forecast run accepted; check /scheduler/status",
        "status": "accepted",
    }
