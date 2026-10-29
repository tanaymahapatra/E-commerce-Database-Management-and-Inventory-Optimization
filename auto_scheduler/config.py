"""
config.py
=========
Central configuration for the auto_scheduler.
All tuneable constants live here — change them once, they apply everywhere.
"""

import os
from dotenv import load_dotenv

# ── Load .env from the project root (one level up from this folder) ──────────
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "ITDETAILS")

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE & EVALUATION WINDOWS
# ─────────────────────────────────────────────────────────────────────────────

# Total weeks of historical data to fetch (52 = 1 full year).
TRAINING_WINDOW_WEEKS: int = 52

# Hold-out test window for evaluating real model accuracy (~2 months = 8 weeks).
# Training is done on (TRAINING_WINDOW_WEEKS - TEST_WINDOW_WEEKS) = 44 weeks.
TEST_WINDOW_WEEKS: int = 8

# Production forecast horizon written to MySQL recommendation table (4 weeks).
FORECAST_STEPS: int = 4

# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY FORMULA CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Z-score for target service level (1.28 = 90%, 1.65 = 95%, 2.33 = 99%).
Z_SCORE: float = 1.65

# Lead time in weeks (equals forecast horizon).
LEAD_TIME_WEEKS: int = FORECAST_STEPS

# A product is flagged OVERSHOOT if stock exceeds this multiple of (demand + safety_stock).
OVERSHOOT_FACTOR: float = 2.0

# ─────────────────────────────────────────────────────────────────────────────
# LIGHTGBM & OPTUNA CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# ── OPTUNA TOGGLE TRIGGER ────────────────────────────────────────────────────
# Set to True  -> Run Optuna hyperparameter tuning for each series (more thorough, takes longer)
# Set to False -> Skip Optuna and use fixed LGBM_PARAMS below directly (much faster)
USE_OPTUNA: bool = False

# Number of trials for Optuna hyperparameter optimization (when USE_OPTUNA = True).
N_TRIALS: int = 30
RANDOM_STATE: int = 42

# Default/fallback hyperparameters when Optuna is OFF (or if Optuna fails).
LGBM_PARAMS: dict = {
    "objective":         "regression",
    "metric":            "rmse",
    "n_estimators":      150,
    "learning_rate":     0.05,
    "num_leaves":        15,
    "max_depth":         6,
    "min_child_samples": 5,
    "subsample":         0.8,
    "subsample_freq":    1,
    "colsample_bytree":  0.8,
    "reg_alpha":         0.1,
    "reg_lambda":        0.1,
    "random_state":      RANDOM_STATE,
    "verbosity":         -1,
    "n_jobs":            -1,
}

# Lag features built for each product × warehouse time series.
LAG_FEATURES: list[str] = ["lag_1", "lag_2", "lag_3", "lag_4"]

# Minimum number of weeks required to train LightGBM.
MIN_SERIES_LENGTH: int = 12

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER TIMING
# ─────────────────────────────────────────────────────────────────────────────

# APScheduler cron fields: every Sunday at 02:00 local time.
CRON_DAY_OF_WEEK: str = "sun"
CRON_HOUR:        int = 2
CRON_MINUTE:      int = 0
