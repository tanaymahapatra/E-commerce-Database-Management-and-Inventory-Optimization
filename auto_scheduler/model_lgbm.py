"""
model_lgbm.py
=============
LightGBM forecaster with Optuna hyperparameter optimization and fallback.

Supports two modes:
  1. evaluate_lgbm:
     Fits on the 44-week training split and forecasts the 8-week test window
     so that real accuracy (WMAPE/RMSE) can be verified against actual orders.
  2. forecast_lgbm:
     Fits on the full 52-week data and forecasts the 4 upcoming weeks.

Optuna toggle:
  Controlled via USE_OPTUNA in config.py (True = tune with Optuna, False = use LGBM_PARAMS).
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_squared_error

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

from .config import (
    FORECAST_STEPS,
    LGBM_PARAMS,
    LAG_FEATURES,
    MIN_SERIES_LENGTH,
    N_TRIALS,
    RANDOM_STATE,
    USE_OPTUNA,
)

logger = logging.getLogger(__name__)


def _build_lag_df(series_values: np.ndarray) -> pd.DataFrame:
    """Build a DataFrame with lag columns from a 1-D series array."""
    df = pd.DataFrame({"y": series_values.astype(float)})
    for lag in range(1, len(LAG_FEATURES) + 1):
        df[f"lag_{lag}"] = df["y"].shift(lag)
    return df.dropna().reset_index(drop=True)


def _tune_with_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_trials: int = N_TRIALS,
    random_state: int = RANDOM_STATE,
) -> tuple[dict, float]:
    """
    Run Optuna hyperparameter optimization to minimize validation RMSE.
    """
    if not HAS_OPTUNA:
        raise RuntimeError("Optuna is not installed.")

    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective":         "regression",
            "metric":            "rmse",
            "n_estimators":      trial.suggest_int("n_estimators", 30, 300),
            "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves":        trial.suggest_int("num_leaves", 5, 31),
            "max_depth":         trial.suggest_int("max_depth", 2, 10),
            "min_child_samples": trial.suggest_int("min_child_samples", 2, 15),
            "subsample":         trial.suggest_float("subsample", 0.7, 1.0),
            "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.7, 1.0),
            "reg_alpha":         trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
            "reg_lambda":        trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
            "subsample_freq":    1,
            "random_state":      random_state,
            "verbosity":         -1,
            "n_jobs":            -1,
        }

        model = lgb.LGBMRegressor(**params)
        model.fit(X_train, y_train)

        predictions = np.maximum(model.predict(X_valid), 0.0)
        return float(np.sqrt(mean_squared_error(y_valid, predictions)))

    sampler = optuna.samplers.TPESampler(seed=random_state)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    if study.best_trial is None or not np.isfinite(study.best_value):
        raise ValueError("Optuna study did not produce a valid best value.")

    best_params = study.best_params.copy()
    best_params.update({
        "objective":      "regression",
        "metric":         "rmse",
        "random_state":   random_state,
        "verbosity":      -1,
        "n_jobs":         -1,
        "subsample_freq": 1,
    })
    return best_params, float(study.best_value)


def _recursive_forecast(
    model: lgb.LGBMRegressor,
    series: pd.Series,
    steps: int,
) -> list[float]:
    """Perform multi-step recursive forecasting with LightGBM."""
    last_vals = list(series.iloc[-len(LAG_FEATURES):])
    predictions = []

    for _ in range(steps):
        X_pred = pd.DataFrame(
            [[last_vals[-1], last_vals[-2], last_vals[-3], last_vals[-4]]],
            columns=LAG_FEATURES,
        )
        pred = max(0.0, float(model.predict(X_pred)[0]))
        predictions.append(pred)
        last_vals.append(pred)
        last_vals.pop(0)

    return predictions


def evaluate_lgbm(
    weekly_orders:    pd.DataFrame,
    train_date_range: pd.DatetimeIndex,
    test_steps:       int,
) -> pd.DataFrame:
    """
    Train LightGBM on the training split only and forecast test_steps ahead
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

        if len(series) < MIN_SERIES_LENGTH:
            continue

        try:
            lag_df = _build_lag_df(series.values)
            val_size = min(4, max(1, len(lag_df) // 5))
            if len(lag_df) - val_size < 2:
                continue

            train_df = lag_df.iloc[:-val_size]
            valid_df = lag_df.iloc[-val_size:]

            X_train = train_df[LAG_FEATURES]
            y_train = train_df["y"]
            X_valid = valid_df[LAG_FEATURES]
            y_valid = valid_df["y"]
            X_full  = lag_df[LAG_FEATURES]
            y_full  = lag_df["y"]

            # Check USE_OPTUNA trigger from config
            if USE_OPTUNA:
                try:
                    chosen_params, _ = _tune_with_optuna(
                        X_train, y_train, X_valid, y_valid, n_trials=N_TRIALS, random_state=RANDOM_STATE
                    )
                except Exception:
                    chosen_params = LGBM_PARAMS.copy()
            else:
                chosen_params = LGBM_PARAMS.copy()

            model = lgb.LGBMRegressor(**chosen_params)
            model.fit(X_full, y_full)

            predictions = _recursive_forecast(model, series, test_steps)

            for step, pred_val in enumerate(predictions):
                results.append({
                    "product_id":       p_id,
                    "warehouse_id":     w_id,
                    "step":             step,
                    "predicted_demand": pred_val,
                })
        except Exception:
            pass

    return pd.DataFrame(results)


def forecast_lgbm(
    weekly_orders:   pd.DataFrame,
    latest_stock:    pd.DataFrame,
    full_date_range: pd.DatetimeIndex,
    forecast_steps:  int = FORECAST_STEPS,
    test_rmse:       float = 1.0,
) -> pd.DataFrame:
    """
    Train LightGBM on the full 52-week dataset and generate the final 4-week forecast.

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

        if len(series) < MIN_SERIES_LENGTH:
            continue

        stock_row = latest_stock[
            (latest_stock["product_id"]   == p_id) &
            (latest_stock["warehouse_id"] == w_id)
        ]
        current_stock = (
            float(stock_row["current_stock"].iloc[0])
            if not stock_row.empty else 0.0
        )

        try:
            lag_df = _build_lag_df(series.values)
            val_size = min(4, max(1, len(lag_df) // 5))
            if len(lag_df) - val_size < 2:
                continue

            train_df = lag_df.iloc[:-val_size]
            valid_df = lag_df.iloc[-val_size:]

            X_train = train_df[LAG_FEATURES]
            y_train = train_df["y"]
            X_valid = valid_df[LAG_FEATURES]
            y_valid = valid_df["y"]
            X_full  = lag_df[LAG_FEATURES]
            y_full  = lag_df["y"]

            # Check USE_OPTUNA trigger from config
            if USE_OPTUNA:
                try:
                    chosen_params, _ = _tune_with_optuna(
                        X_train, y_train, X_valid, y_valid, n_trials=N_TRIALS, random_state=RANDOM_STATE
                    )
                except Exception:
                    chosen_params = LGBM_PARAMS.copy()
            else:
                chosen_params = LGBM_PARAMS.copy()

            model = lgb.LGBMRegressor(**chosen_params)
            model.fit(X_full, y_full)

            predictions = _recursive_forecast(model, series, forecast_steps)

            for step, pred_val in enumerate(predictions):
                results.append({
                    "product_id":       p_id,
                    "warehouse_id":     w_id,
                    "step":             step,
                    "predicted_demand": pred_val,
                    "current_stock":    current_stock,
                    "rmse":             test_rmse,
                })
        except Exception as exc:
            logger.debug("LightGBM final forecast skipped for (%s, %s): %s", p_id, w_id, exc)

    return pd.DataFrame(results)
