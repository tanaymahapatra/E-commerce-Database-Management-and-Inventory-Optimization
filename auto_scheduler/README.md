# auto_scheduler

Automated weekly ML pipeline that:
1. Fetches the last 52 weeks of order data from MySQL on every Sunday
2. Trains both a **Simple Exponential Smoothing (SES)** model and a **plain LightGBM** model
3. Picks the better model (lower RMSE)
4. **Anchors the 4 forecast steps to real upcoming Sunday dates** (always future-dated, never stale)
5. Computes `safety_stock`, `reorder_qty`, and `status` for each product × warehouse
6. UPSERTs predictions into the `recommendation` table
7. Logs every run into `scheduler_runs`

> **No files in the original project were modified.**  
> This is a fully self-contained folder.

---

## Folder Structure

```
auto_scheduler/
├── __init__.py              # Package init, exposes run_weekly_pipeline
├── config.py                # All tuneable constants (window size, LGBM params, cron timing)
├── db.py                    # Shared SQLAlchemy engine factory
│
├── data_fetcher.py          # Step 3 – pulls rolling 52-week window from MySQL
├── feature_engineering.py   # Step 4 – builds weekly time series, fills missing weeks
├── model_ses.py             # Step 5 – Simple Exponential Smoothing
├── model_lgbm.py            # Step 6 – Plain LightGBM (no Optuna)
├── model_selector.py        # Step 7 – compares RMSE, picks winner
├── date_anchoring.py        # Step 8 – maps forecast steps to real future Sunday dates ⭐
├── inventory_calculator.py  # Step 9 – safety_stock, reorder_qty, status
├── db_writer.py             # Step 10 – UPSERT into recommendation table
├── run_log.py               # Step 11 – writes run metadata to scheduler_runs
│
├── pipeline.py              # Master orchestrator — calls all steps in order
├── scheduler_app.py         # FastAPI app with APScheduler + API endpoints
│
└── sql/
    ├── create_scheduler_runs.sql   # Run once to create the scheduler_runs table
    └── fetch_training_data.sql     # Rolling-window query used by data_fetcher.py
```

---

## One-Time Setup

### 1. Create the `scheduler_runs` table in MySQL

```sql
-- Run this once in your MySQL client / workbench
source auto_scheduler/sql/create_scheduler_runs.sql;
```

### 2. Install the one new dependency (APScheduler)

```bash
# From the project root, with your .venv active
pip install apscheduler
```

All other dependencies (lightgbm, statsmodels, pandas, sqlalchemy, fastapi) are already in `requirements.txt`.

---

## Running the Scheduler

### Option A — Standalone FastAPI app (recommended for testing)

```bash
# From the project root directory
cd "d:\DBMS Project\E-commerce-Database-Management-and-Inventory-Optimization"
python -m uvicorn auto_scheduler.scheduler_app:app --host 0.0.0.0 --port 8001 --reload
```

Then open: `http://localhost:8001/docs` for the interactive API.

### Option B — Run the pipeline once directly (no server needed)

```bash
# From the project root
python -m auto_scheduler.pipeline
```

This runs the full pipeline immediately and prints the result as JSON.

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET`  | `/scheduler/status`   | Last run summary (model, accuracy, records written) |
| `POST` | `/scheduler/trigger`  | Fire the pipeline right now (background task) |
| `GET`  | `/scheduler/history`  | Last N run records from `scheduler_runs` |
| `GET`  | `/scheduler/next-run` | When will the next automatic Sunday run fire? |

---

## How Date Anchoring Works

This is the key design decision. The models produce **4 raw demand numbers** (step 0 → step 3).  
`date_anchoring.py` maps those to **real calendar dates** relative to `TODAY`:

```
Run on 2026-11-02 (Sunday):
  step 0  →  forecast_date = 2026-11-09
  step 1  →  forecast_date = 2026-11-16
  step 2  →  forecast_date = 2026-11-23
  step 3  →  forecast_date = 2026-11-30

Run on 2026-11-09 (next Sunday):
  step 0  →  forecast_date = 2026-11-16
  step 1  →  forecast_date = 2026-11-23
  ...
```

The frontend query is simply:
```sql
SELECT * FROM recommendation
WHERE product_id = ? AND warehouse_id = ?
  AND forecast_date >= CURDATE()
ORDER BY forecast_date ASC;
```

---

## Configuration

All constants are in [`config.py`](./config.py). Key ones:

| Constant | Default | Meaning |
|----------|---------|---------|
| `TRAINING_WINDOW_WEEKS` | `52` | Rolling window size |
| `FORECAST_STEPS` | `4` | Weeks ahead to predict |
| `Z_SCORE` | `1.65` | Service level for safety stock (95%) |
| `CRON_DAY_OF_WEEK` | `"sun"` | When to fire automatically |
| `CRON_HOUR` | `2` | Hour of automatic run (2 AM) |
| `LGBM_PARAMS` | see config | Fixed LightGBM hyperparameters |

---

## What the `scheduler_runs` Table Records

Every run writes one row:

| Column | Example |
|--------|---------|
| `run_id` | 1 |
| `triggered_at` | 2026-11-02 02:00:01 |
| `triggered_by` | scheduler |
| `run_date_anchor` | 2026-11-02 |
| `model_used` | LightGBM |
| `wmape` | 12.34 |
| `forecast_accuracy` | 87.66 |
| `records_written` | 2840 |
| `status` | SUCCESS |
