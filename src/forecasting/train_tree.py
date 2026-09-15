"""
Tree-based forecasting model training and forward-chaining validation module for RetailIQ.
Trains LightGBM with expanding-window time-series CV, computes commercial error analysis,
and saves production model artifacts.
"""
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from typing import Dict, Any, List, Tuple, Optional
from src.features.forecasting_features import FeatureEngineer
from src.forecasting.evaluate import calculate_metrics, print_metrics


class TreeForecasterTrainer:
    """Trains and validates tree-based models with forward-chaining CV."""

    def __init__(
        self,
        data_path: Optional[Path] = None,
        models_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None
    ):
        base_dir = Path(__file__).resolve().parents[2]
        self.data_path = data_path or base_dir / "data" / "processed" / "integrated_sales.parquet"
        self.models_dir = models_dir or base_dir / "models"
        self.reports_dir = reports_dir or base_dir / "reports"

        self.models_dir.mkdir(parents=True, exist_ok=True)
        (self.models_dir / "trained").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "metadata").mkdir(parents=True, exist_ok=True)
        (self.reports_dir / "metrics").mkdir(parents=True, exist_ok=True)

    def load_and_prepare_features(self) -> pd.DataFrame:
        """Loads integrated data and applies feature engineering."""
        print(f"Loading data from {self.data_path}...")
        df = pd.read_parquet(self.data_path)
        print("Applying feature engineering (lags, rolling stats, calendar, promo)...")
        feat_df = FeatureEngineer.create_features(df, is_training=True)
        return feat_df

    def forward_chaining_cv(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes 3-fold expanding-window forward-chaining time-series validation.
        Guarantees that all training data strictly precedes validation data.
        """
        feature_cols = FeatureEngineer.get_feature_columns()
        target_col = "weekly_sales"

        # Define 3 temporal validation splits
        splits = [
            {
                "fold": 1,
                "train_end": "2011-09-30",
                "val_start": "2011-10-01",
                "val_end": "2012-01-31"
            },
            {
                "fold": 2,
                "train_end": "2012-01-31",
                "val_start": "2012-02-01",
                "val_end": "2012-05-31"
            },
            {
                "fold": 3,
                "train_end": "2012-05-31",
                "val_start": "2012-06-01",
                "val_end": "2012-10-26"
            }
        ]

        cv_results = []
        lgb_params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "n_estimators": 350,
            "learning_rate": 0.05,
            "num_leaves": 63,
            "min_child_samples": 20,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1
        }

        print("\n==========================================")
        print("Executing 3-Fold Forward-Chaining CV")
        print("==========================================")

        for sp in splits:
            fold_idx = sp["fold"]
            train_mask = df["date"] <= sp["train_end"]
            val_mask = (df["date"] >= sp["val_start"]) & (df["date"] <= sp["val_end"])

            train_data = df[train_mask]
            val_data = df[val_mask]

            X_tr, y_tr = train_data[feature_cols], train_data[target_col]
            X_val, y_val = val_data[feature_cols], val_data[target_col]

            model = lgb.LGBMRegressor(**lgb_params)
            model.fit(X_tr, y_tr)

            preds = model.predict(X_val)
            # Clip predictions at 0 for metrics since demand/sales cannot be negative in forecasts
            # but note we evaluated against true y_val
            metrics = calculate_metrics(y_val.values, preds, val_data["is_holiday"].values)

            print(f"Fold {fold_idx} ({sp['val_start']} to {sp['val_end']}): "
                  f"Train rows={len(train_data):,}, Val rows={len(val_data):,} | "
                  f"RMSE: {metrics['RMSE']:,.2f}, MAE: {metrics['MAE']:,.2f}, "
                  f"MAPE: {metrics['MAPE']:.2f}%, WMAE: {metrics['WMAE']:,.2f}")

            cv_results.append({
                "fold": fold_idx,
                "train_end": sp["train_end"],
                "val_start": sp["val_start"],
                "val_end": sp["val_end"],
                "train_rows": len(train_data),
                "val_rows": len(val_data),
                **metrics
            })

        cv_df = pd.DataFrame(cv_results)
        cv_summary = {
            "mean_rmse": round(float(cv_df["RMSE"].mean()), 2),
            "std_rmse": round(float(cv_df["RMSE"].std()), 2),
            "mean_mae": round(float(cv_df["MAE"].mean()), 2),
            "mean_mape": round(float(cv_df["MAPE"].mean()), 2),
            "mean_wmae": round(float(cv_df["WMAE"].mean()), 2)
        }

        print(f"\nForward CV Mean -> RMSE: {cv_summary['mean_rmse']:,.2f} (±{cv_summary['std_rmse']:.2f}), "
              f"MAE: {cv_summary['mean_mae']:,.2f}, MAPE: {cv_summary['mean_mape']:.2f}%, "
              f"WMAE: {cv_summary['mean_wmae']:,.2f}")

        # Save CV metrics
        cv_csv_path = self.reports_dir / "metrics" / "forecast_cv_results.csv"
        cv_df.to_csv(cv_csv_path, index=False)
        print(f"CV results saved to {cv_csv_path}")

        return cv_df, cv_summary

    def train_final_production_model(self, df: pd.DataFrame) -> Tuple[lgb.LGBMRegressor, Dict[str, Any]]:
        """
        Trains final LightGBM model on all available history and evaluates on the final 20-week holdout.
        """
        feature_cols = FeatureEngineer.get_feature_columns()
        target_col = "weekly_sales"

        # Holdout split: train up to 2012-05-31, holdout = 2012-06-01 to 2012-10-26 (20 weeks)
        cutoff_date = "2012-05-31"
        train_mask = df["date"] <= cutoff_date
        holdout_mask = df["date"] > cutoff_date

        train_data = df[train_mask]
        holdout_data = df[holdout_mask]

        lgb_params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "n_estimators": 400,
            "learning_rate": 0.04,
            "num_leaves": 63,
            "min_child_samples": 20,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1
        }

        print("\n==========================================")
        print("Training Final LightGBM Forecaster")
        print("==========================================")
        model = lgb.LGBMRegressor(**lgb_params)
        model.fit(train_data[feature_cols], train_data[target_col])

        holdout_preds = model.predict(holdout_data[feature_cols])
        holdout_metrics = calculate_metrics(
            holdout_data[target_col].values,
            holdout_preds,
            holdout_data["is_holiday"].values
        )

        print_metrics("LightGBM Final Holdout Evaluation", holdout_metrics)

        # Feature importances
        importances = pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

        # Retrain on full historical dataset for production deployment
        prod_model = lgb.LGBMRegressor(**lgb_params)
        prod_model.fit(df[feature_cols], df[target_col])

        # Production model bundle
        bundle = {
            "model": prod_model,
            "feature_columns": feature_cols,
            "target": "weekly_sales",
            "model_version": "1.0.0",
            "model_type": "LightGBM Regressor",
            "training_date_cutoff": str(df["date"].max().date()),
            "metrics": holdout_metrics,
            "store_types_map": {"A": 1, "B": 2, "C": 3}
        }

        prod_model_path = self.models_dir / "trained" / "retailiq_forecaster.pkl"
        joblib.dump(bundle, prod_model_path)
        print(f"Production model bundle saved to {prod_model_path}")

        # Metadata
        metadata = {
            "model_name": "RetailIQ Demand Forecaster",
            "version": "1.0.0",
            "algorithm": "LightGBM GBDT Regressor",
            "granularity": "Store + Department + Week",
            "training_samples": len(df),
            "features_count": len(feature_cols),
            "features": feature_cols,
            "top_10_features": importances.head(10).to_dict(orient="records"),
            "holdout_evaluation": holdout_metrics,
            "parameters": lgb_params,
            "target": "Weekly_Sales"
        }

        meta_path = self.models_dir / "metadata" / "model_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Model metadata saved to {meta_path}")

        # Commercial error analysis
        self._run_commercial_error_analysis(holdout_data, holdout_preds)

        return prod_model, holdout_metrics

    def _run_commercial_error_analysis(self, holdout_df: pd.DataFrame, preds: np.ndarray) -> None:
        """Calculates commercial forecasting error across business segments."""
        eval_df = holdout_df.copy()
        eval_df["pred"] = preds
        eval_df["abs_error"] = (eval_df["weekly_sales"] - eval_df["pred"]).abs()
        eval_df["sq_error"] = (eval_df["weekly_sales"] - eval_df["pred"]) ** 2

        print("\n==========================================")
        print("Commercial Error Analysis Breakdown")
        print("==========================================")

        # 1. By Store Type
        type_perf = eval_df.groupby("store_type").apply(
            lambda g: pd.Series({
                "RMSE": np.sqrt(g["sq_error"].mean()),
                "MAE": g["abs_error"].mean(),
                "Avg_Sales": g["weekly_sales"].mean()
            })
        )
        print("--- Error by Store Type ---")
        print(type_perf.round(2))

        # 2. By Holiday vs Non-Holiday
        holiday_perf = eval_df.groupby("is_holiday").apply(
            lambda g: pd.Series({
                "RMSE": np.sqrt(g["sq_error"].mean()),
                "MAE": g["abs_error"].mean(),
                "Avg_Sales": g["weekly_sales"].mean()
            })
        )
        print("\n--- Error by Holiday Status (1=Holiday, 0=Normal) ---")
        print(holiday_perf.round(2))


def run_training_pipeline():
    trainer = TreeForecasterTrainer()
    df = trainer.load_and_prepare_features()
    trainer.forward_chaining_cv(df)
    trainer.train_final_production_model(df)


if __name__ == "__main__":
    run_training_pipeline()
