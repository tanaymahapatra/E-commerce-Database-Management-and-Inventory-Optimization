"""
data_fetcher.py
===============
Fetches the rolling training window from MySQL.

Design
------
• Uses a parameterised SQL file (sql/fetch_training_data.sql).
• Dynamically queries the LAST 52 WEEKS relative to the latest available
  order in the database (MAX(order_date)), NOT today's calendar date.
• This ensures:
    - Historical datasets (e.g. 2024-2025) never return 0 rows.
    - Live running databases automatically slide the 52-week window as new
      daily orders arrive.
"""

import os
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import text

from .db import get_engine
from .config import TRAINING_WINDOW_WEEKS

logger = logging.getLogger(__name__)

# Path to the SQL file (relative to this file's location)
_SQL_FILE = os.path.join(
    os.path.dirname(__file__), "sql", "fetch_training_data.sql"
)


def fetch_training_data(cutoff_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """
    Pull the last 52 weeks of available data from MySQL.

    Parameters
    ----------
    cutoff_date : Optional[pd.Timestamp]
        Optional reference date (kept for backwards compatibility).
        The SQL query dynamically anchors to MAX(order_date) in the database.

    Returns
    -------
    pd.DataFrame
        Columns: order_date, product_id, warehouse_id, quantity, stock_quantity
        All rows within the 52-week training window, ordered by order_date ASC.

    Raises
    ------
    RuntimeError
        If the query returns zero rows (DB unreachable or table empty).
    """
    logger.info(
        "Fetching training data: last %d weeks of available data from database...",
        TRAINING_WINDOW_WEEKS,
    )

    with open(_SQL_FILE, "r", encoding="utf-8") as fh:
        raw_sql = fh.read()

    query = text(raw_sql)

    engine = get_engine()
    try:
        with engine.connect() as conn:
            chunks = pd.read_sql(
                query,
                conn,
                params={
                    "weeks_back": TRAINING_WINDOW_WEEKS,
                },
                chunksize=50_000,
            )
            df = pd.concat(chunks, ignore_index=True)
    finally:
        engine.dispose()

    if df.empty:
        raise RuntimeError(
            "fetch_training_data returned 0 rows. "
            "Check DB connection and that the orders table has data."
        )

    # ── Ensure correct dtypes ────────────────────────────────────────────────
    df["order_date"]     = pd.to_datetime(df["order_date"])
    df["product_id"]     = df["product_id"].astype(int)
    df["warehouse_id"]   = df["warehouse_id"].astype(int)
    df["quantity"]       = df["quantity"].astype(int)
    df["stock_quantity"] = df["stock_quantity"].astype(int)

    logger.info(
        "Fetched %d rows covering %d product-warehouse combinations (Date range: %s to %s).",
        len(df),
        df.groupby(["product_id", "warehouse_id"]).ngroups,
        df["order_date"].min().date(),
        df["order_date"].max().date(),
    )
    return df
