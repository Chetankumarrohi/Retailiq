"""
Data loader module for RetailIQ.
Handles loading raw datasets from CSV / ZIP archives with schema validation and auditing.
"""
from pathlib import Path
import zipfile
import pandas as pd
from typing import Dict, Any, Optional, Tuple


class DataLoader:
    """Loads and audits raw retail datasets."""

    def __init__(self, raw_dir: Optional[Path] = None):
        if raw_dir is None:
            # Default to project data/raw
            self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
        else:
            self.raw_dir = Path(raw_dir)

    def load_stores(self) -> pd.DataFrame:
        """Loads stores dataset."""
        path = self.raw_dir / "stores.csv"
        if not path.exists():
            raise FileNotFoundError(f"Stores dataset not found at {path}")
        df = pd.read_csv(path)
        required_cols = {"Store", "Type", "Size"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"stores.csv missing required columns: {required_cols - set(df.columns)}")
        return df

    def load_features(self) -> pd.DataFrame:
        """Loads features dataset from CSV or ZIP."""
        csv_path = self.raw_dir / "features.csv"
        zip_path = self.raw_dir / "features.csv.zip"

        if csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=["Date"])
        elif zip_path.exists():
            with zipfile.ZipFile(zip_path, "r") as z:
                # Find features csv inside zip
                csv_files = [f for f in z.namelist() if f.endswith(".csv")]
                if not csv_files:
                    raise FileNotFoundError("No CSV file found inside features.csv.zip")
                df = pd.read_csv(z.open(csv_files[0]), parse_dates=["Date"])
        else:
            raise FileNotFoundError(f"Features dataset not found at {csv_path} or {zip_path}")

        required_cols = {"Store", "Date", "Temperature", "Fuel_Price", "CPI", "Unemployment", "IsHoliday"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"features.csv missing required columns: {required_cols - set(df.columns)}")
        return df

    def load_train(self) -> pd.DataFrame:
        """Loads historical training transactions."""
        path = self.raw_dir / "train.csv"
        if not path.exists():
            raise FileNotFoundError(f"Training dataset not found at {path}")
        df = pd.read_csv(path, parse_dates=["Date"])
        required_cols = {"Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"train.csv missing required columns: {required_cols - set(df.columns)}")
        return df

    def load_test(self) -> pd.DataFrame:
        """Loads test set transactions."""
        path = self.raw_dir / "test.csv"
        if not path.exists():
            raise FileNotFoundError(f"Test dataset not found at {path}")
        df = pd.read_csv(path, parse_dates=["Date"])
        required_cols = {"Store", "Dept", "Date", "IsHoliday"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"test.csv missing required columns: {required_cols - set(df.columns)}")
        return df

    def audit_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Performs a comprehensive technical audit of all available raw datasets."""
        audit_results = {}
        
        datasets = {
            "stores": self.load_stores(),
            "features": self.load_features(),
            "train": self.load_train(),
            "test": self.load_test()
        }

        for name, df in datasets.items():
            report = {
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "missing_values": df.isnull().sum().to_dict(),
                "duplicate_rows": int(df.duplicated().sum()),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
            }
            if "Date" in df.columns:
                report["date_min"] = str(df["Date"].min().date())
                report["date_max"] = str(df["Date"].max().date())
                report["unique_weeks"] = int(df["Date"].nunique())
            if "Store" in df.columns:
                report["unique_stores"] = int(df["Store"].nunique())
            if "Dept" in df.columns:
                report["unique_departments"] = int(df["Dept"].nunique())
            if "Weekly_Sales" in df.columns:
                report["target_available"] = True
                report["negative_sales_count"] = int((df["Weekly_Sales"] < 0).sum())
                report["negative_sales_pct"] = round(float((df["Weekly_Sales"] < 0).mean() * 100), 3)
                report["zero_sales_count"] = int((df["Weekly_Sales"] == 0).sum())
                report["min_sales"] = float(df["Weekly_Sales"].min())
                report["max_sales"] = float(df["Weekly_Sales"].max())
                report["mean_sales"] = round(float(df["Weekly_Sales"].mean()), 2)
                report["median_sales"] = round(float(df["Weekly_Sales"].median()), 2)
            else:
                report["target_available"] = False

            audit_results[name] = report

        return audit_results
