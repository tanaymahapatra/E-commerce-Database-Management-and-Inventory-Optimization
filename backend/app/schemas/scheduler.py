from datetime import date, datetime
from pydantic import BaseModel


class SchedulerRun(BaseModel):
    run_id: int
    triggered_at: datetime
    completed_at: datetime | None = None
    triggered_by: str
    run_date_anchor: date
    model_used: str | None = None
    training_weeks: int | None = None
    wmape: float | None = None
    rmse: float | None = None
    forecast_accuracy: float | None = None
    records_written: int | None = None
    status: str
    error_message: str | None = None


class SchedulerStatusResponse(BaseModel):
    scheduler_running: bool
    pipeline_running: bool
    last_run: SchedulerRun | None = None


class SchedulerHistoryResponse(BaseModel):
    total_returned: int
    runs: list[SchedulerRun]


class SchedulerNextRunResponse(BaseModel):
    job_id: str
    next_run_at: datetime | None = None
    timezone: str


class SchedulerTriggerResponse(BaseModel):
    message: str
    status: str
