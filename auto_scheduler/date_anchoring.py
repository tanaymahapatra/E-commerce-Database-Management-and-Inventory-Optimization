"""
date_anchoring.py
=================
Anchors the 4 forecast steps to real calendar dates from TODAY,
formatted strictly as DATE strings (YYYY-MM-DD, without any T00:00:00 time part).
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

def anchor_dates(
    forecast_df: pd.DataFrame,
    run_date:    pd.Timestamp,
    forecast_steps: int = 4,
) -> pd.DataFrame:
    """
    Replace the `step` column with real `forecast_date` strings (YYYY-MM-DD).

    Parameters
    ----------
    forecast_df : pd.DataFrame
        Must contain a `step` column with values in {0, 1, 2, 3}.
    run_date : pd.Timestamp
        The date the scheduler is running on (TODAY).
    forecast_steps : int
        Number of weeks ahead to forecast (default 4).

    Returns
    -------
    pd.DataFrame
        Same rows, with `step` replaced by `forecast_date` (YYYY-MM-DD string).
    """
    if forecast_df.empty:
        return forecast_df

    # Build the step -> date mapping as pure YYYY-MM-DD string (no time component)
    step_to_date = {
        step: (run_date + pd.Timedelta(weeks=step + 1)).strftime("%Y-%m-%d")
        for step in range(forecast_steps)
    }

    logger.info(
        "Date anchoring: run_date=%s -> forecast dates: %s",
        run_date.date(),
        list(step_to_date.values()),
    )

    df = forecast_df.copy()
    df["forecast_date"] = df["step"].map(step_to_date)
    df = df.drop(columns=["step"])

    return df
