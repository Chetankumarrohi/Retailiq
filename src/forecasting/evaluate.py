"""
Evaluation metrics module for RetailIQ demand forecasting.
Implements RMSE, MAE, safe MAPE, and Holiday-Weighted MAE (WMAE).
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional


def safe_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1.0) -> float:
    """
    Computes safe Mean Absolute Percentage Error (MAPE).
    Uses max(|y_true|, epsilon) in denominator to prevent division by zero or explosion on near-zero sales.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    denominator = np.maximum(np.abs(y_true), epsilon)
    mape = np.mean(np.abs((y_true - y_pred) / denominator)) * 100.0
    return float(mape)


def holiday_wmae(y_true: np.ndarray, y_pred: np.ndarray, is_holiday: np.ndarray, holiday_weight: float = 5.0) -> float:
    """
    Computes Holiday Weighted Mean Absolute Error (WMAE).
    Weights = 5 for holiday weeks and 1 for normal weeks.
    Formula: sum(w_i * |y_i - y_hat_i|) / sum(w_i)
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    is_holiday = np.asarray(is_holiday).astype(bool)

    weights = np.where(is_holiday, holiday_weight, 1.0)
    wmae = np.sum(weights * np.abs(y_true - y_pred)) / np.sum(weights)
    return float(wmae)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    is_holiday: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Computes all standard retail forecasting evaluation metrics.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mape = safe_mape(y_true, y_pred)

    metrics = {
        "RMSE": round(rmse, 2),
        "MAE": round(mae, 2),
        "MAPE": round(mape, 2)
    }

    if is_holiday is not None:
        wmae = holiday_wmae(y_true, y_pred, is_holiday)
        metrics["WMAE"] = round(wmae, 2)

    return metrics


def print_metrics(model_name: str, metrics: Dict[str, float]) -> None:
    """Pretty prints model performance metrics."""
    metrics_str = " | ".join([f"{k}: {v:,.2f}" for k, v in metrics.items()])
    print(f"[{model_name}] -> {metrics_str}")
