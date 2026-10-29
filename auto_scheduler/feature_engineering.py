"""
feature_engineering.py
=======================
Converts raw order rows into weekly time series, and creates
the Train / Test splits for real-world accuracy evaluation.

Split strategy
--------------
• Total window: 52 weeks (last 1 year of available data).
• Test window:  Last 8 weeks (~2 months hold-out).
• Train window: First 44 weeks (~10 months) for training during evaluation.
"""

import logging
from typing import Optional

import pandas as pd

from .config import TRAINING_WINDOW_WEEKS, TEST_WINDOW_WEEKS

logger = logging.getLogger(__name__)


def build_weekly_series(
    raw_df: pd.DataFrame,
    cutoff_date: Optional[pd.Timestamp] = None,
    total_window_weeks: int = TRAINING_WINDOW_WEEKS,
    test_window_weeks: int = TEST_WINDOW_WEEKS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex, pd.DatetimeIndex, pd.DatetimeIndex, pd.DataFrame]:
    """
    Parameters
    ----------
    raw_df : pd.DataFrame
        Output of data_fetcher.fetch_training_data().
        Columns: order_date, product_id, warehouse_id, quantity, stock_quantity.

    Returns
    -------
    tuple of:
        weekly_orders     : full weekly aggregated demand
        latest_stock      : latest stock per product × warehouse
        full_date_range   : complete 52-week date range (normalized to midnight)
        train_date_range  : first 44-week date range
        test_date_range   : last 8-week hold-out date range
        test_actuals      : ground truth actual demand for the 8 test weeks
    """
    if raw_df.empty:
        logger.warning("Empty DataFrame passed to build_weekly_series.")
        empty_df = pd.DataFrame()
        empty_idx = pd.DatetimeIndex([])
        return empty_df, empty_df, empty_idx, empty_idx, empty_idx, empty_df

    # Normalize dates to midnight so all timestamps match W-SUN perfectly 
    max_order_date = pd.to_datetime(raw_df["order_date"].max()).normalize()
    if cutoff_date is None or pd.to_datetime(cutoff_date).normalize() > max_order_date:
        window_end = max_order_date
    else:
        window_end = pd.to_datetime(cutoff_date).normalize()

    window_start = (window_end - pd.Timedelta(weeks=total_window_weeks)).normalize()

    df = raw_df[
        (raw_df["order_date"] >= window_start) &
        (raw_df["order_date"] <= window_end + pd.Timedelta(days=1))
    ].copy()

    if df.empty:
        logger.warning("No rows in the training window.")
        empty_df = pd.DataFrame()
        empty_idx = pd.DatetimeIndex([])
        return empty_df, empty_df, empty_idx, empty_idx, empty_idx, empty_df

    # Latest stock snapshot per product × warehouse 
    latest_stock = (
        df.sort_values("order_date")
          .groupby(["product_id", "warehouse_id"])
          .tail(1)[["product_id", "warehouse_id", "stock_quantity"]]
          .rename(columns={"stock_quantity": "current_stock"})
          .reset_index(drop=True)
    )

    # Weekly demand aggregation (W-SUN at midnight) 
    weekly_orders = (
        df.groupby(
            ["product_id", "warehouse_id",
             pd.Grouper(key="order_date", freq="W-SUN")]
        )["quantity"]
        .sum()
        .reset_index()
    )
    weekly_orders.columns = [
        "product_id", "warehouse_id", "week_end_date", "total_quantity"
    ]
    # Ensure week_end_date is strictly midnight for reindex matching
    weekly_orders["week_end_date"] = pd.to_datetime(weekly_orders["week_end_date"]).dt.normalize()

    # Full date range (52 weeks, normalized to midnight)
    full_date_range = pd.date_range(
        start=window_start,
        end=window_end,
        freq="W-SUN",
    ).normalize()

    # Split into Train (first ~44 weeks) and Test (last 8 weeks)
    train_weeks = max(4, len(full_date_range) - test_window_weeks)
    train_date_range = full_date_range[:train_weeks]
    test_date_range = full_date_range[train_weeks:]

    # Build ground-truth test actuals table 
    test_actuals_list = []
    for (p_id, w_id), df_group in weekly_orders.groupby(["product_id", "warehouse_id"]):
        series = (
            df_group.set_index("week_end_date")["total_quantity"]
            .reindex(full_date_range, fill_value=0)
        )
        test_series = series.loc[test_date_range]
        for step, (dt, qty) in enumerate(test_series.items()):
            test_actuals_list.append({
                "product_id":      p_id,
                "warehouse_id":    w_id,
                "step":            step,
                "week_date":       dt,
                "actual_quantity": float(qty),
            })

    test_actuals = pd.DataFrame(test_actuals_list)

    total_actual_demand = test_actuals["actual_quantity"].sum()
    logger.info(
        "Weekly series built: %d combinations. Train: %d weeks (%s to %s), Test: %d weeks (%s to %s). Total test actual demand: %.0f units.",
        weekly_orders.groupby(["product_id", "warehouse_id"]).ngroups,
        len(train_date_range),
        train_date_range[0].date() if len(train_date_range) else "N/A",
        train_date_range[-1].date() if len(train_date_range) else "N/A",
        len(test_date_range),
        test_date_range[0].date() if len(test_date_range) else "N/A",
        test_date_range[-1].date() if len(test_date_range) else "N/A",
        total_actual_demand,
    )

    return (
        weekly_orders,
        latest_stock,
        full_date_range,
        train_date_range,
        test_date_range,
        test_actuals,
    )
