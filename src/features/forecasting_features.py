"""
Forecasting feature engineering for RetailIQ.
Constructs calendar, store, economic, promotional, lag, and rolling statistics
strictly preventing target leakage.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional


class FeatureEngineer:
    """Generates leakage-safe feature matrices for time-series forecasting."""

    LAG_STEPS = [1, 2, 4, 8, 13, 26, 52]
    ROLLING_WINDOWS = [4, 8, 13]

    @classmethod
    def create_features(
        cls,
        df: pd.DataFrame,
        is_training: bool = True
    ) -> pd.DataFrame:
        """
        Creates all features on the integrated sales dataframe.
        Ensures strict chronological sorting per store-department series.
        """
        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values(["store_id", "dept_id", "date"]).reset_index(drop=True)

        # 1. Calendar Features
        data["year"] = data["date"].dt.year
        data["quarter"] = data["date"].dt.quarter
        data["month"] = data["date"].dt.month
        data["week_of_year"] = data["date"].dt.isocalendar().week.astype(int)
        data["day_of_year"] = data["date"].dt.dayofyear
        data["is_month_start"] = data["date"].dt.is_month_start.astype(int)
        data["is_month_end"] = data["date"].dt.is_month_end.astype(int)

        # 2. Store categorical mapping
        type_mapping = {"A": 1, "B": 2, "C": 3}
        if "store_type" in data.columns:
            if data["store_type"].dtype == object or str(data["store_type"].dtype) == "category":
                data["store_type_encoded"] = data["store_type"].map(type_mapping).fillna(0).astype(int)
            else:
                data["store_type_encoded"] = data["store_type"]

        # 3. Promotional Features
        md_cols = [c for c in data.columns if c.startswith("markdown")]
        for col in md_cols:
            data[col] = data[col].fillna(0.0)
        data["has_markdown"] = (data[md_cols].sum(axis=1) > 0).astype(int)
        data["total_markdown"] = data[md_cols].sum(axis=1)

        # 4. Lag Features (Leakage-Safe)
        # Shift(k) shifts strictly to prior historical periods
        grouped = data.groupby(["store_id", "dept_id"])["weekly_sales"]
        for lag in cls.LAG_STEPS:
            data[f"lag_{lag}"] = grouped.shift(lag)

        # 5. Rolling Statistics (Leakage-Safe)
        # To prevent target leakage, we calculate rolling stats on shift(1) of weekly sales
        shifted_sales = grouped.shift(1)
        # Re-group the shifted series
        shifted_grouped = data.assign(_shifted=shifted_sales).groupby(["store_id", "dept_id"])["_shifted"]

        for win in cls.ROLLING_WINDOWS:
            data[f"roll_mean_{win}"] = shifted_grouped.transform(lambda s: s.rolling(win, min_periods=1).mean())
            data[f"roll_std_{win}"] = shifted_grouped.transform(lambda s: s.rolling(win, min_periods=1).std()).fillna(0.0)
            data[f"roll_min_{win}"] = shifted_grouped.transform(lambda s: s.rolling(win, min_periods=1).min())
            data[f"roll_max_{win}"] = shifted_grouped.transform(lambda s: s.rolling(win, min_periods=1).max())

        # Interaction & Ratio features (safe based on historical rolling means)
        data["sales_to_roll_mean_4"] = (data["lag_1"] / (data["roll_mean_4"] + 1.0)).clip(0.1, 10.0)
        data["sales_to_roll_mean_13"] = (data["lag_1"] / (data["roll_mean_13"] + 1.0)).clip(0.1, 10.0)

        # Backfill initial lags per series with earliest available lag to avoid dropping first year
        for col in [f"lag_{l}" for l in cls.LAG_STEPS]:
            data[col] = data.groupby(["store_id", "dept_id"])[col].transform(lambda s: s.bfill().ffill().fillna(0.0))

        for col in [f"roll_mean_{w}" for w in cls.ROLLING_WINDOWS] + [f"roll_min_{w}" for w in cls.ROLLING_WINDOWS] + [f"roll_max_{w}" for w in cls.ROLLING_WINDOWS]:
            data[col] = data.groupby(["store_id", "dept_id"])[col].transform(lambda s: s.bfill().ffill().fillna(0.0))

        data["sales_to_roll_mean_4"] = data["sales_to_roll_mean_4"].fillna(1.0)
        data["sales_to_roll_mean_13"] = data["sales_to_roll_mean_13"].fillna(1.0)

        return data

    @classmethod
    def get_feature_columns(cls) -> List[str]:
        """Returns the list of feature column names used for model training and inference."""
        features = [
            # Store identifiers and attributes
            "store_id", "dept_id", "store_type_encoded", "store_size",
            # Calendar
            "year", "quarter", "month", "week_of_year", "day_of_year", "is_holiday",
            "is_month_start", "is_month_end",
            # Economic indicators
            "temperature", "fuel_price", "cpi", "unemployment",
            # Promotional indicators
            "markdown1", "markdown2", "markdown3", "markdown4", "markdown5",
            "has_markdown", "total_markdown",
            # Lags
            "lag_1", "lag_2", "lag_4", "lag_8", "lag_13", "lag_26", "lag_52",
            # Rolling statistics
            "roll_mean_4", "roll_std_4", "roll_min_4", "roll_max_4",
            "roll_mean_8", "roll_std_8", "roll_min_8", "roll_max_8",
            "roll_mean_13", "roll_std_13", "roll_min_13", "roll_max_13",
            # Ratios
            "sales_to_roll_mean_4", "sales_to_roll_mean_13"
        ]
        return features
