"""
Data cleaner and integration module for RetailIQ.
Handles data transformations, missing-value imputation, returns flagging, and star-schema preparation.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


class DataCleaner:
    """Cleans and integrates raw retail tables."""

    @staticmethod
    def clean_sales(train_df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans sales transactions:
        - Flags customer returns without modifying original Weekly_Sales.
        - Ensures consistent datatypes and date sorting.
        """
        df = train_df.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Store", "Dept", "Date"]).reset_index(drop=True)

        # Flag negative sales as returns (policy: net return volume exceeding sales)
        df["Returns_Flag"] = (df["Weekly_Sales"] < 0).astype(int)
        
        return df

    @staticmethod
    def clean_features(features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans feature table:
        - Fills missing markdowns with 0.0 (represents no recorded promotional discount event).
        - Computes has_markdown indicator.
        - Forward-fills CPI and Unemployment per Store for continuity.
        """
        df = features_df.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Store", "Date"]).reset_index(drop=True)

        # Markdowns missingness decision: NaN -> 0.0 (no discount active)
        md_cols = [c for c in df.columns if c.startswith("MarkDown")]
        for col in md_cols:
            df[col] = df[col].fillna(0.0)

        df["Has_MarkDown"] = (df[md_cols].sum(axis=1) > 0).astype(int)

        # Economic indicators: forward fill per store, then backward fill if starting values missing
        df["CPI"] = df.groupby("Store")["CPI"].transform(lambda s: s.ffill().bfill())
        df["Unemployment"] = df.groupby("Store")["Unemployment"].transform(lambda s: s.ffill().bfill())

        return df

    @staticmethod
    def compute_store_active_spans(train_df: pd.DataFrame) -> pd.DataFrame:
        """Computes first and last active date per store."""
        spans = train_df.groupby("Store")["Date"].agg(
            first_active_week="min",
            last_active_week="max"
        ).reset_index()
        return spans

    @classmethod
    def integrate_modelling_dataset(
        cls,
        train_df: pd.DataFrame,
        features_df: pd.DataFrame,
        stores_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Merges sales, features, and store metadata safely.
        Validates row counts before and after to ensure no Cartesian products or data loss.
        """
        clean_sales_df = cls.clean_sales(train_df)
        clean_feat_df = cls.clean_features(features_df)

        rows_before = len(clean_sales_df)

        # Drop duplicate IsHoliday from sales before merge if present
        sales_to_merge = clean_sales_df.copy()
        if "IsHoliday" in sales_to_merge.columns and "IsHoliday" in clean_feat_df.columns:
            sales_to_merge = sales_to_merge.drop(columns=["IsHoliday"])

        # Merge 1: Sales + Features on [Store, Date]
        merged = pd.merge(
            sales_to_merge,
            clean_feat_df,
            on=["Store", "Date"],
            how="left",
            validate="many_to_one"
        )

        # Merge 2: + Stores on [Store]
        integrated = pd.merge(
            merged,
            stores_df,
            on="Store",
            how="left",
            validate="many_to_one"
        )

        rows_after = len(integrated)
        if rows_before != rows_after:
            raise ValueError(f"Merge row count mismatch! Before: {rows_before}, After: {rows_after}")

        # Standardize column naming
        integrated = integrated.rename(columns={
            "Store": "store_id",
            "Dept": "dept_id",
            "Date": "date",
            "Weekly_Sales": "weekly_sales",
            "Returns_Flag": "returns_flag",
            "IsHoliday": "is_holiday",
            "Temperature": "temperature",
            "Fuel_Price": "fuel_price",
            "CPI": "cpi",
            "Unemployment": "unemployment",
            "Type": "store_type",
            "Size": "store_size",
            "Has_MarkDown": "has_markdown",
            "MarkDown1": "markdown1",
            "MarkDown2": "markdown2",
            "MarkDown3": "markdown3",
            "MarkDown4": "markdown4",
            "MarkDown5": "markdown5",
        })

        integrated["is_holiday"] = integrated["is_holiday"].astype(int)
        integrated["date"] = pd.to_datetime(integrated["date"])
        integrated = integrated.sort_values(["store_id", "dept_id", "date"]).reset_index(drop=True)

        validation_stats = {
            "rows": len(integrated),
            "columns": len(integrated.columns),
            "stores": int(integrated["store_id"].nunique()),
            "departments": int(integrated["dept_id"].nunique()),
            "date_min": str(integrated["date"].min().date()),
            "date_max": str(integrated["date"].max().date()),
            "null_counts": integrated.isnull().sum().to_dict(),
            "returns_count": int((integrated["weekly_sales"] < 0).sum()),
            "returns_pct": round(float((integrated["weekly_sales"] < 0).mean() * 100), 3)
        }

        return integrated, validation_stats
