"""
Baseline forecasting models for RetailIQ.
Implements Naive, 4-Week Moving Average, and 52-Week Seasonal Naive benchmarks.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from src.forecasting.evaluate import calculate_metrics


class BaselineForecaster:
    """Computes statistical baseline predictions without machine learning."""

    @staticmethod
    def predict_naive(df: pd.DataFrame) -> np.ndarray:
        """Naive forecast: t = t-1 (lag_1)."""
        if "lag_1" in df.columns:
            return df["lag_1"].values
        raise KeyError("lag_1 column not found in dataframe")

    @staticmethod
    def predict_moving_average(df: pd.DataFrame) -> np.ndarray:
        """Moving Average forecast: t = mean(t-1, ..., t-4)."""
        if "roll_mean_4" in df.columns:
            return df["roll_mean_4"].values
        raise KeyError("roll_mean_4 column not found in dataframe")

    @staticmethod
    def predict_seasonal_naive(df: pd.DataFrame) -> np.ndarray:
        """Seasonal Naive forecast: t = t-52 (lag_52)."""
        if "lag_52" in df.columns:
            return df["lag_52"].values
        raise KeyError("lag_52 column not found in dataframe")

    @classmethod
    def evaluate_all(cls, holdout_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Evaluates all baselines on a given holdout dataframe."""
        y_true = holdout_df["weekly_sales"].values
        is_holiday = holdout_df["is_holiday"].values if "is_holiday" in holdout_df.columns else None

        results = {}

        # 1. Naive
        pred_naive = cls.predict_naive(holdout_df)
        results["Baseline (Naive Lag-1)"] = calculate_metrics(y_true, pred_naive, is_holiday)

        # 2. Moving Average (4w)
        pred_ma = cls.predict_moving_average(holdout_df)
        results["Baseline (4-Week Moving Avg)"] = calculate_metrics(y_true, pred_ma, is_holiday)

        # 3. Seasonal Naive (52w)
        pred_seasonal = cls.predict_seasonal_naive(holdout_df)
        results["Baseline (52-Week Seasonal Naive)"] = calculate_metrics(y_true, pred_seasonal, is_holiday)

        return results
