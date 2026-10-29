"""
model_ses.py
============
Simple Exponential Smoothing (SES) model.

Supports two modes:
  1. evaluate_ses:
     Fits on the 44-week training split and forecasts the 8-week test window
     so that real accuracy (WMAPE/RMSE) can be verified against actual orders.
  2. forecast_ses:
     Fits on the full 52-week data and forecasts the 4 upcoming weeks.
"""

import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

from .config import FORECAST_STEPS

logger = logging.getLogger(__name__)


def evaluate_ses(
    weekly_orders:    pd.DataFrame,
    train_date_range: pd.DatetimeIndex,
    test_steps:       int,
) -> pd.DataFrame:
    """
    Train SES on the training split only and forecast test_steps ahead
    for test evaluation.

    Returns
    -------
    pd.DataFrame: [product_id, warehouse_id, step, predicted_demand]
    """
    results = []

    for (p_id, w_id), df_group in weekly_orders.groupby(["product_id", "warehouse_id"]):
        series = (
            df_group.set_index("week_end_date")["total_quantity"]
            .reindex(train_date_range, fill_value=0)
            .astype(float)
        )

        try:
            model = SimpleExpSmoothing(series, initialization_method="estimated")
            fitted = model.fit()
            forecast = fitted.forecast(test_steps)

            for step, pred_val in enumerate(forecast):
                results.append({
                    "product_id":       p_id,
                    "warehouse_id":     w_id,
                    "step":             step,
                    "predicted_demand": max(0.0, float(pred_val)),
                })
        except Exception:
            pass

    return pd.DataFrame(results)


def forecast_ses(
    weekly_orders:   pd.DataFrame,
    latest_stock:    pd.DataFrame,
    full_date_range: pd.DatetimeIndex,
    forecast_steps:  int = FORECAST_STEPS,
    test_rmse:       float = 1.0,
) -> pd.DataFrame:
    """
    Train SES on the full 52-week dataset and generate the final 4-week forecast.

    Returns
    -------
    pd.DataFrame: [product_id, warehouse_id, step, predicted_demand, current_stock, rmse]
    """
    results = []

    for (p_id, w_id), df_group in weekly_orders.groupby(["product_id", "warehouse_id"]):
        series = (
            df_group.set_index("week_end_date")["total_quantity"]
            .reindex(full_date_range, fill_value=0)
            .astype(float)
        )

        stock_row = latest_stock[
            (latest_stock["product_id"]   == p_id) &
            (latest_stock["warehouse_id"] == w_id)
        ]
        current_stock = (
            float(stock_row["current_stock"].iloc[0])
            if not stock_row.empty else 0.0
        )

        try:
            model = SimpleExpSmoothing(series, initialization_method="estimated")
            fitted = model.fit()
            forecast = fitted.forecast(forecast_steps)
            residuals = series.values - fitted.fittedvalues.values
            in_sample_rmse = float(np.sqrt(np.mean(residuals ** 2)))
            effective_rmse = max(in_sample_rmse, test_rmse)

            for step, pred_val in enumerate(forecast):
                results.append({
                    "product_id":       p_id,
                    "warehouse_id":     w_id,
                    "step":             step,
                    "predicted_demand": max(0.0, float(pred_val)),
                    "current_stock":    current_stock,
                    "rmse":             effective_rmse,
                })
        except Exception as exc:
            logger.debug("SES final forecast skipped for (%s, %s): %s", p_id, w_id, exc)

    return pd.DataFrame(results)
