"""
inventory_calculator.py
=======================
Computes safety_stock, reorder_qty, and status from the raw demand
forecasts — identical logic to the notebook, extracted into a module.

Formulas
--------
  safety_stock  = ceil( Z * RMSE * sqrt(lead_time_weeks) )
  demand_LT     = sum of predicted_demand for the FIRST L forecast weeks
  reorder_qty   = max( 0, ceil(demand_LT + safety_stock - current_stock) )

Status rules (priority order, first match wins)
  CRITICAL     : current_stock <= 0  OR  current_stock < demand_LT
  REORDER_NOW  : current_stock <= reorder_point  (= demand_LT + safety_stock)
  OVERSHOOT    : current_stock > OVERSHOOT_FACTOR * (total_demand + safety_stock)
  OK           : everything else

Returns the input DataFrame augmented with:
    safety_stock | reorder_qty | status
and trimmed to the columns required by the recommendation table:
    product_id | warehouse_id | forecast_date |
    predicted_demand | safety_stock | reorder_qty | status
"""

import logging

import numpy as np
import pandas as pd

from .config import Z_SCORE, LEAD_TIME_WEEKS, OVERSHOOT_FACTOR, FORECAST_STEPS

logger = logging.getLogger(__name__)


def compute_inventory_metrics(forecast_df: pd.DataFrame) -> pd.DataFrame:
    """
    Parameters
    ----------
    forecast_df : pd.DataFrame
        Must contain:
            product_id, warehouse_id, forecast_date,
            predicted_demand, current_stock, rmse

    Returns
    -------
    pd.DataFrame
        Columns: product_id, warehouse_id, forecast_date,
                 predicted_demand, safety_stock, reorder_qty, status
    """
    if forecast_df.empty:
        logger.warning("compute_inventory_metrics received an empty DataFrame.")
        return pd.DataFrame(
            columns=[
                "product_id", "warehouse_id", "forecast_date",
                "predicted_demand", "safety_stock", "reorder_qty", "status",
            ]
        )

    df = (
        forecast_df
        .sort_values(["product_id", "warehouse_id", "forecast_date"])
        .reset_index(drop=True)
        .copy()
    )

    grp = df.groupby(["product_id", "warehouse_id"])

    # Safety stock
    df["safety_stock"] = (
        np.ceil(Z_SCORE * df["rmse"] * np.sqrt(LEAD_TIME_WEEKS))
        .astype(int)
    )

    # Position within the 4-week forecast window 
    df["_wk"] = grp.cumcount()

    # Demand during lead time (all weeks, since lead = forecast horizon)
    df["demand_LT"] = (
        df["predicted_demand"]
        .where(df["_wk"] < LEAD_TIME_WEEKS, other=0)
        .groupby([df["product_id"], df["warehouse_id"]])
        .transform("sum")
    )

    # Total predicted demand across the full 4-week window
    df["total_demand"] = grp["predicted_demand"].transform("sum")

    # Reorder quantity
    df["reorder_qty"] = (
        np.ceil(
            df["demand_LT"] + df["safety_stock"] - df["current_stock"]
        )
        .clip(lower=0)
        .astype(int)
    )

    # Inventory status
    reorder_point = df["demand_LT"] + df["safety_stock"]

    conditions = [
        (df["current_stock"] <= 0) | (df["current_stock"] < df["demand_LT"]),
        df["current_stock"] <= reorder_point,
        df["current_stock"] > OVERSHOOT_FACTOR * (df["total_demand"] + df["safety_stock"]),
    ]
    choices = ["CRITICAL", "REORDER_NOW", "OVERSHOOT"]

    df["status"] = np.select(conditions, choices, default="OK")

    # Round predicted_demand to integer (non-negative)
    df["predicted_demand"] = (
        np.maximum(0, df["predicted_demand"]).round().astype(int)
    )

    # Clean up helper columns
    final_cols = [
        "product_id", "warehouse_id", "forecast_date",
        "predicted_demand", "safety_stock", "reorder_qty", "status",
    ]

    logger.info(
        "Inventory metrics computed: %d rows, status distribution: %s",
        len(df),
        df["status"].value_counts().to_dict(),
    )

    return df[final_cols].copy()
