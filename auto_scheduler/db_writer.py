"""
db_writer.py
============
Writes the final forecast DataFrame to the `recommendation` table
using the ON DUPLICATE KEY UPDATE strategy.

Ensures `forecast_date` is pushed strictly as a DATE string (YYYY-MM-DD)
without any T00:00:00 time component.
"""

import logging

import pandas as pd
from sqlalchemy import text

from .db import get_engine

logger = logging.getLogger(__name__)

# SQL for upserting
_UPSERT_SQL = text("""
INSERT INTO recommendation (
    product_id,
    warehouse_id,
    forecast_date,
    predicted_demand,
    safety_stock,
    reorder_qty,
    status
)
VALUES (
    :product_id,
    :warehouse_id,
    :forecast_date,
    :predicted_demand,
    :safety_stock,
    :reorder_qty,
    :status
)
ON DUPLICATE KEY UPDATE
    predicted_demand = VALUES(predicted_demand),
    safety_stock     = VALUES(safety_stock),
    reorder_qty      = VALUES(reorder_qty),
    status           = VALUES(status);
""")

# SQL to remove stale past-dated predictions before each run
_CLEANUP_SQL = text("""
DELETE FROM recommendation
WHERE forecast_date < :today;
""")


def write_predictions(
    final_df:  pd.DataFrame,
    run_date:  pd.Timestamp,
) -> int:
    """
    Write the forecast DataFrame to MySQL.

    Parameters
    ----------
    final_df : pd.DataFrame
        Columns: product_id, warehouse_id, forecast_date,
                 predicted_demand, safety_stock, reorder_qty, status
    run_date : pd.Timestamp
        The Sunday the pipeline runs on.

    Returns
    -------
    int
        Number of records written.
    """
    if final_df.empty:
        logger.warning("write_predictions called with an empty DataFrame — nothing to write.")
        return 0

    # Prepare the upload DataFrame with clean date format (YYYY-MM-DD)
    upload_df = final_df.copy()
    upload_df["forecast_date"]    = pd.to_datetime(upload_df["forecast_date"]).dt.strftime("%Y-%m-%d")
    upload_df["predicted_demand"] = upload_df["predicted_demand"].astype(int)
    upload_df["safety_stock"]     = upload_df["safety_stock"].astype(int)
    upload_df["reorder_qty"]      = upload_df["reorder_qty"].astype(int)

    records = upload_df.to_dict(orient="records")

    engine = get_engine()
    try:
        with engine.begin() as conn:
            # 1. Remove past-dated stale predictions
            conn.execute(_CLEANUP_SQL, {"today": run_date.date().isoformat()})
            logger.info("Cleaned up past-dated rows (forecast_date < %s).", run_date.date())

            # 2. Upsert new predictions
            conn.execute(_UPSERT_SQL, records)

        logger.info("Successfully upserted %d forecast records with clean dates (YYYY-MM-DD).", len(records))
        return len(records)

    finally:
        engine.dispose()
