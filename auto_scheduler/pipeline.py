"""
pipeline.py
===========
The master orchestrator that wires every module together.

Call  run_weekly_pipeline()  to execute the full pipeline once.
It can be triggered:
  • Automatically  — by APScheduler every Sunday (see scheduler_app.py)
  • Manually       — via the POST /scheduler/trigger API endpoint
  • From a script  — python -m auto_scheduler.pipeline

Complete Evaluation & Forecast Flow:
-------------------------------------
1.  Determine TODAY (the run-date anchor).
2.  Open a run record in scheduler_runs.
3.  Fetch the last 52 weeks of available data from MySQL.
4.  Split into:
      - Training split : First 44 weeks (~10 months)
      - Test split     : Last 8 weeks (~2 months hold-out)
5.  Train SES on the 44-week training split and forecast the 8 test weeks.
6.  Train LightGBM on the 44-week training split (with Optuna/fallback)
    and forecast the 8 test weeks.
7.  Compare both models against the ground-truth test actuals:
      - Calculate true WMAPE, RMSE, MAE, and Accuracy % (never a fake 100%).
      - Select the winning model.
8.  Train the winning model on the FULL 52 weeks and generate the final
    4-week demand predictions.
9.  Anchor the 4 forecast steps to REAL upcoming Sunday dates (from TODAY).
10. Compute safety_stock, reorder_qty, status.
11. UPSERT into MySQL recommendation table (clean past rows first).
12. Close run record with true metrics in scheduler_runs.
"""

import logging
import warnings
from datetime import datetime

import pandas as pd

from .config import TRAINING_WINDOW_WEEKS, TEST_WINDOW_WEEKS, FORECAST_STEPS
from .data_fetcher          import fetch_training_data
from .feature_engineering    import build_weekly_series
from .model_ses             import evaluate_ses, forecast_ses
from .model_lgbm            import evaluate_lgbm, forecast_lgbm
from .model_selector        import compare_and_select_winner
from .date_anchoring        import anchor_dates
from .inventory_calculator  import compute_inventory_metrics
from .db_writer             import write_predictions
from .run_log               import open_run, close_run

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


def _get_run_date() -> pd.Timestamp:
    """
    Return today's date normalised to midnight.
    In production this will be a Sunday (APScheduler fires on Sunday).
    During manual/test runs it will be whatever day you call it.
    """
    return pd.Timestamp(datetime.today().date())


def run_weekly_pipeline(
    triggered_by: str = "scheduler",
) -> dict:
    """
    Execute the full ML pipeline with true train/test validation.

    Parameters
    ----------
    triggered_by : str
        "scheduler"  for automatic Sunday runs.
        "manual"     when called from the API trigger endpoint.

    Returns
    -------
    dict with keys:
        status, model_used, wmape, rmse, forecast_accuracy,
        records_written, run_date, run_id, error
    """
    run_date = _get_run_date()
    logger.info("=" * 60)
    logger.info("Pipeline START  run_date=%s  triggered_by=%s", run_date.date(), triggered_by)
    logger.info("=" * 60)

    # Step 2: Open run log 
    run_id = open_run(run_date, triggered_by=triggered_by)

    model_used        = "N/A"
    wmape             = 0.0
    rmse              = 0.0
    forecast_accuracy = 0.0
    records_written   = 0

    try:
        # Step 3: Fetch last 52 weeks of available data
        logger.info("Step 3: Fetching last %d weeks of available data from MySQL...", TRAINING_WINDOW_WEEKS)
        raw_df = fetch_training_data()

        # Step 4: Split into Train (44 weeks) and Test (8 weeks)
        logger.info("Step 4: Splitting into 44 weeks train and 8 weeks hold-out test...")
        (
            weekly_orders,
            latest_stock,
            full_date_range,
            train_date_range,
            test_date_range,
            test_actuals,
        ) = build_weekly_series(
            raw_df=raw_df,
            total_window_weeks=TRAINING_WINDOW_WEEKS,
            test_window_weeks=TEST_WINDOW_WEEKS,
        )

        test_steps = len(test_date_range)
        logger.info("Test split size: %d weeks. Evaluating both models...", test_steps)

        # Step 5: Evaluate SES on Test Split
        logger.info("Step 5: Training SES on train split and forecasting %d test weeks...", test_steps)
        ses_test_preds = evaluate_ses(
            weekly_orders=weekly_orders,
            train_date_range=train_date_range,
            test_steps=test_steps,
        )

        # Step 6: Evaluate LightGBM on Test Split
        logger.info("Step 6: Training LightGBM on train split and forecasting %d test weeks...", test_steps)
        lgbm_test_preds = evaluate_lgbm(
            weekly_orders=weekly_orders,
            train_date_range=train_date_range,
            test_steps=test_steps,
        )

        # Step 7: Compare Real Test Accuracy & Pick Winner
        logger.info("Step 7: Comparing real test accuracy against ground truth...")
        model_used, winner_metrics = compare_and_select_winner(
            test_actuals=test_actuals,
            ses_preds=ses_test_preds,
            lgbm_preds=lgbm_test_preds,
        )

        wmape             = winner_metrics["wmape"]
        rmse              = winner_metrics["rmse"]
        forecast_accuracy = winner_metrics["accuracy"]

        # Step 8: Final 4-Week Production Forecast
        logger.info("Step 8: Training winning model (%s) on full dataset for next 4 weeks...", model_used)
        if model_used == "LightGBM":
            raw_forecast_df = forecast_lgbm(
                weekly_orders=weekly_orders,
                latest_stock=latest_stock,
                full_date_range=full_date_range,
                forecast_steps=FORECAST_STEPS,
                test_rmse=rmse,
            )
            if raw_forecast_df.empty:
                logger.warning("LightGBM produced no forecast rows. Falling back to SES.")
                raw_forecast_df = forecast_ses(
                    weekly_orders=weekly_orders,
                    latest_stock=latest_stock,
                    full_date_range=full_date_range,
                    forecast_steps=FORECAST_STEPS,
                    test_rmse=rmse,
                )
                model_used = "SES"
        else:
            raw_forecast_df = forecast_ses(
                weekly_orders=weekly_orders,
                latest_stock=latest_stock,
                full_date_range=full_date_range,
                forecast_steps=FORECAST_STEPS,
                test_rmse=rmse,
            )

        # Step 9: Date Anchoring to TODAY's upcoming 4 weeks
        logger.info("Step 9: Anchoring 4 forecast steps to upcoming Sundays from TODAY (%s)...", run_date.date())
        anchored_df = anchor_dates(
            forecast_df=raw_forecast_df,
            run_date=run_date,
            forecast_steps=FORECAST_STEPS,
        )

        # Step 10: Inventory Metrics (Safety stock, Reorder qty, Status)
        logger.info("Step 10: Computing safety_stock, reorder_qty, status...")
        final_df = compute_inventory_metrics(anchored_df)

        # Step 11: Write to MySQL recommendation table 
        logger.info("Step 11: Writing recommendations to database...")
        records_written = write_predictions(final_df, run_date=run_date)

        # Step 12: Close Run Log
        close_run(
            run_id,
            model_used=model_used,
            training_weeks=len(train_date_range),
            wmape=wmape,
            rmse=rmse,
            forecast_accuracy=forecast_accuracy,
            records_written=records_written,
            status="SUCCESS",
        )

        logger.info("Pipeline SUCCESS | Winner: %s | Accuracy: %.2f%% | Records: %d",
                    model_used, forecast_accuracy, records_written)

        return {
            "status":            "SUCCESS",
            "model_used":        model_used,
            "wmape":             round(wmape, 4),
            "rmse":              round(rmse, 4),
            "forecast_accuracy": round(forecast_accuracy, 2),
            "records_written":   records_written,
            "run_date":          str(run_date.date()),
            "run_id":            run_id,
            "error":             None,
        }

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.exception("Pipeline FAILED: %s", error_msg)

        close_run(
            run_id,
            model_used=model_used,
            training_weeks=TRAINING_WINDOW_WEEKS,
            wmape=0.0,
            rmse=0.0,
            forecast_accuracy=0.0,
            records_written=0,
            status="FAILED",
            error_message=error_msg,
        )

        return {
            "status":            "FAILED",
            "model_used":        model_used,
            "wmape":             0.0,
            "rmse":              0.0,
            "forecast_accuracy": 0.0,
            "records_written":   0,
            "run_date":          str(run_date.date()),
            "run_id":            run_id,
            "error":             error_msg,
        }


# Allow direct execution
if __name__ == "__main__":
    import json
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    result = run_weekly_pipeline(triggered_by="manual")
    print(json.dumps(result, indent=2))
