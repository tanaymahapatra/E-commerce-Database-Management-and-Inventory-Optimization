"""
model_selector.py
=================
Evaluates SES and LightGBM models against the real 8-week hold-out test set,
computes true ground-truth accuracy metrics (WMAPE, RMSE, MAE), and selects
the winning model.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _evaluate_model_performance(
    test_actuals: pd.DataFrame,
    predictions:  pd.DataFrame,
    model_name:   str,
) -> dict:
    """
    Compute real test metrics by comparing predictions to ground-truth actuals.
    """
    if predictions.empty or test_actuals.empty:
        logger.warning("%s produced no predictions for the test split.", model_name)
        return {
            "wmape":    float("inf"),
            "rmse":     float("inf"),
            "mae":      float("inf"),
            "accuracy": 0.0,
        }

    merged = pd.merge(
        test_actuals,
        predictions,
        on=["product_id", "warehouse_id", "step"],
        how="left",
    )
    merged["predicted_demand"] = merged["predicted_demand"].fillna(0.0)

    y_true = merged["actual_quantity"].values
    y_pred = merged["predicted_demand"].values

    total_actual = float(np.sum(y_true))
    total_error  = float(np.sum(np.abs(y_true - y_pred)))

    if total_actual <= 0:
        logger.error(
            "%s evaluation failed: Total actual demand in test period is 0. Check data timestamps and date ranges!",
            model_name,
        )
        return {
            "wmape":    float("inf"),
            "rmse":     float("inf"),
            "mae":      float("inf"),
            "accuracy": 0.0,
        }

    # WMAPE = (Total Absolute Error / Total Actuals) * 100
    wmape = (total_error / total_actual * 100.0)
    accuracy = max(0.0, 100.0 - wmape)

    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae  = float(np.mean(np.abs(y_true - y_pred)))

    logger.info(
        "%s Test Evaluation — Total Actuals: %.0f | WMAPE: %.2f%% | Accuracy: %.2f%% | RMSE: %.4f | MAE: %.4f",
        model_name, total_actual, wmape, accuracy, rmse, mae,
    )

    return {
        "wmape":    round(wmape, 4),
        "rmse":     round(rmse, 4),
        "mae":      round(mae, 4),
        "accuracy": round(accuracy, 2),
    }


def compare_and_select_winner(
    test_actuals: pd.DataFrame,
    ses_preds:    pd.DataFrame,
    lgbm_preds:   pd.DataFrame,
) -> tuple[str, dict]:
    """
    Compare real test accuracy of SES and LightGBM and declare the winner.

    Returns
    -------
    tuple: (winning_model_name, winning_metrics_dict)
    """
    ses_metrics  = _evaluate_model_performance(test_actuals, ses_preds, "SES")
    lgbm_metrics = _evaluate_model_performance(test_actuals, lgbm_preds, "LightGBM")

    # Pick the model with higher accuracy (lower WMAPE)
    if lgbm_metrics["accuracy"] >= ses_metrics["accuracy"] and np.isfinite(lgbm_metrics["rmse"]) and lgbm_metrics["accuracy"] > 0:
        winner = "LightGBM"
        winner_metrics = lgbm_metrics
    elif np.isfinite(ses_metrics["rmse"]) and ses_metrics["accuracy"] > 0:
        winner = "SES"
        winner_metrics = ses_metrics
    elif np.isfinite(lgbm_metrics["rmse"]):
        winner = "LightGBM"
        winner_metrics = lgbm_metrics
    else:
        winner = "SES"
        winner_metrics = ses_metrics

    logger.info(
        "🏆 Model Selection WINNER: %s (Test Accuracy: %.2f%%, RMSE: %.4f, WMAPE: %.2f%%)",
        winner,
        winner_metrics["accuracy"],
        winner_metrics["rmse"],
        winner_metrics["wmape"],
    )

    return winner, winner_metrics
