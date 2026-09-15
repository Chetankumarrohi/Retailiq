"""
Production demand forecasting predictor for RetailIQ.
Loads trained model artifact, generates recursive multi-step lag/rolling features,
handles future macroeconomic assumptions, and returns structured Python/JSON dictionaries.
"""
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Any, List, Optional
from src.features.forecasting_features import FeatureEngineer


class RetailForecasterPredictor:
    """Production predictor engine for RetailIQ demand forecasting."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        history_path: Optional[Path] = None,
        future_features_path: Optional[Path] = None
    ):
        base_dir = Path(__file__).resolve().parents[2]
        self.model_path = model_path or base_dir / "models" / "trained" / "retailiq_forecaster.pkl"
        self.history_path = history_path or base_dir / "data" / "processed" / "integrated_sales.parquet"
        self.future_features_path = future_features_path or base_dir / "data" / "processed" / "clean_features.parquet"

        self._bundle = None
        self._history_df = None
        self._future_feat_df = None

    def _load_model(self) -> Dict[str, Any]:
        """Loads and caches the model bundle."""
        if self._bundle is None:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model artifact not found at {self.model_path}. Train the model first.")
            self._bundle = joblib.load(self.model_path)
        return self._bundle

    def _load_history(self) -> pd.DataFrame:
        """Loads and caches historical integrated sales data."""
        if self._history_df is None:
            if not self.history_path.exists():
                raise FileNotFoundError(f"Historical sales data not found at {self.history_path}.")
            self._history_df = pd.read_parquet(self.history_path)
            self._history_df["date"] = pd.to_datetime(self._history_df["date"])
        return self._history_df

    def _load_future_features(self) -> pd.DataFrame:
        """Loads and caches store-week macroeconomic and promotional features."""
        if self._future_feat_df is None:
            if self.future_features_path.exists():
                self._future_feat_df = pd.read_parquet(self.future_features_path)
                self._future_feat_df["Date"] = pd.to_datetime(self._future_feat_df["Date"])
            else:
                self._future_feat_df = pd.DataFrame()
        return self._future_feat_df

    def predict(
        self,
        store_id: int,
        dept_id: int,
        horizon_weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Generates recursive multi-step demand forecasts for a given store and department.
        Returns a structured dictionary suitable for direct API serialization.
        """
        if horizon_weeks < 1 or horizon_weeks > 52:
            raise ValueError(f"horizon_weeks must be between 1 and 52, got {horizon_weeks}")

        bundle = self._load_model()
        model = bundle["model"]
        feature_cols = bundle["feature_columns"]
        model_version = bundle.get("model_version", "1.0.0")

        history = self._load_history()
        future_features = self._load_future_features()

        # Filter historical series for this store-dept
        series = history[(history["store_id"] == store_id) & (history["dept_id"] == dept_id)].sort_values("date").reset_index(drop=True)

        if series.empty:
            raise ValueError(
                f"No historical sales records found for store_id={store_id}, dept_id={dept_id}. "
                f"Please provide an existing store and department."
            )

        last_known_row = series.iloc[-1]
        last_date = pd.to_datetime(last_known_row["date"])
        store_type_val = last_known_row.get("store_type", "A")
        store_size_val = last_known_row.get("store_size", 150000)
        store_type_encoded = bundle.get("store_types_map", {}).get(store_type_val, 1)

        # Build list of historical sales for lag and rolling computation
        sales_history = list(series["weekly_sales"].values)
        predictions = []

        # Multi-step recursive forecast loop
        for step in range(1, horizon_weeks + 1):
            future_date = last_date + timedelta(weeks=step)
            assumptions = []

            # 1. Macroeconomic / Promo features lookup
            feat_match = pd.DataFrame()
            if not future_features.empty:
                feat_match = future_features[
                    (future_features["Store"] == store_id) & 
                    (future_features["Date"] == future_date)
                ]

            if not feat_match.empty:
                matched_row = feat_match.iloc[0]
                temp = float(matched_row["Temperature"])
                fuel = float(matched_row["Fuel_Price"])
                cpi = float(matched_row["CPI"])
                unemp = float(matched_row["Unemployment"])
                is_hol = int(matched_row["IsHoliday"])
                md1 = float(matched_row.get("MarkDown1", 0.0))
                md2 = float(matched_row.get("MarkDown2", 0.0))
                md3 = float(matched_row.get("MarkDown3", 0.0))
                md4 = float(matched_row.get("MarkDown4", 0.0))
                md5 = float(matched_row.get("MarkDown5", 0.0))
                assumptions.append("Known calendar features loaded from feature schedule")
            else:
                # Documented fallback: use latest known store economic indicators
                temp = float(last_known_row.get("temperature", 60.0))
                fuel = float(last_known_row.get("fuel_price", 3.5))
                cpi = float(last_known_row.get("cpi", 210.0))
                unemp = float(last_known_row.get("unemployment", 7.5))
                is_hol = 0
                md1 = md2 = md3 = md4 = md5 = 0.0
                assumptions.append("Macroeconomic continuity fallback (latest known values)")

            has_md = int((md1 + md2 + md3 + md4 + md5) > 0)
            tot_md = float(md1 + md2 + md3 + md4 + md5)

            # 2. Build recursive lag features
            row_dict = {
                "store_id": store_id,
                "dept_id": dept_id,
                "store_type_encoded": store_type_encoded,
                "store_size": store_size_val,
                "year": future_date.year,
                "quarter": future_date.quarter,
                "month": future_date.month,
                "week_of_year": int(future_date.isocalendar().week),
                "day_of_year": future_date.dayofyear,
                "is_holiday": is_hol,
                "is_month_start": int(future_date.is_month_start),
                "is_month_end": int(future_date.is_month_end),
                "temperature": temp,
                "fuel_price": fuel,
                "cpi": cpi,
                "unemployment": unemp,
                "markdown1": md1,
                "markdown2": md2,
                "markdown3": md3,
                "markdown4": md4,
                "markdown5": md5,
                "has_markdown": has_md,
                "total_markdown": tot_md
            }

            # Lags
            for lag in FeatureEngineer.LAG_STEPS:
                if len(sales_history) >= lag:
                    row_dict[f"lag_{lag}"] = sales_history[-lag]
                else:
                    row_dict[f"lag_{lag}"] = sales_history[0]

            # Rolling stats
            for win in FeatureEngineer.ROLLING_WINDOWS:
                recent_window = sales_history[-win:] if len(sales_history) >= win else sales_history
                row_dict[f"roll_mean_{win}"] = float(np.mean(recent_window))
                row_dict[f"roll_std_{win}"] = float(np.std(recent_window)) if len(recent_window) > 1 else 0.0
                row_dict[f"roll_min_{win}"] = float(np.min(recent_window))
                row_dict[f"roll_max_{win}"] = float(np.max(recent_window))

            # Ratios
            row_dict["sales_to_roll_mean_4"] = float(np.clip(row_dict["lag_1"] / (row_dict["roll_mean_4"] + 1.0), 0.1, 10.0))
            row_dict["sales_to_roll_mean_13"] = float(np.clip(row_dict["lag_1"] / (row_dict["roll_mean_13"] + 1.0), 0.1, 10.0))

            # DataFrame for prediction
            input_df = pd.DataFrame([row_dict])[feature_cols]
            pred_raw = float(model.predict(input_df)[0])
            pred_val = round(max(0.0, pred_raw), 2)  # demand forecasts non-negative

            predictions.append({
                "step": step,
                "week": future_date.strftime("%Y-%m-%d"),
                "weekly_sales": pred_val,
                "is_holiday": is_hol,
                "assumptions": assumptions
            })

            # Append predicted value to sales history for subsequent recursive steps
            sales_history.append(pred_val)

        return {
            "store_id": store_id,
            "dept_id": dept_id,
            "horizon_weeks": horizon_weeks,
            "model_version": model_version,
            "model_type": bundle.get("model_type", "LightGBM Regressor"),
            "predictions": predictions,
            "historical_summary": {
                "last_known_date": last_date.strftime("%Y-%m-%d"),
                "last_known_sales": round(float(last_known_row["weekly_sales"]), 2),
                "historical_mean_sales": round(float(series["weekly_sales"].mean()), 2),
                "historical_std_sales": round(float(series["weekly_sales"].std()), 2),
                "total_historical_weeks": len(series)
            }
        }


# Quick CLI test
if __name__ == "__main__":
    predictor = RetailForecasterPredictor()
    sample_result = predictor.predict(store_id=1, dept_id=1, horizon_weeks=4)
    import json
    print(json.dumps(sample_result, indent=2))
