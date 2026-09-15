"""
Database builder and SQL analytics service module for RetailIQ.
Constructs SQLite star schema (retailiq.db) and provides tested analytical query functions.
"""
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner


def build_database(
    integrated_df: Optional[pd.DataFrame] = None,
    db_path: Optional[Path] = None,
    schema_path: Optional[Path] = None
) -> Path:
    """Builds the SQLite analytical star schema database."""
    base_dir = Path(__file__).resolve().parents[2]
    if db_path is None:
        db_path = base_dir / "retailiq.db"
    if schema_path is None:
        schema_path = base_dir / "sql" / "schema.sql"

    if integrated_df is None:
        parquet_path = base_dir / "data" / "processed" / "integrated_sales.parquet"
        if parquet_path.exists():
            integrated_df = pd.read_parquet(parquet_path)
        else:
            loader = DataLoader()
            train_df = loader.load_train()
            features_df = loader.load_features()
            stores_df = loader.load_stores()
            cleaner = DataCleaner()
            integrated_df, _ = cleaner.integrate_modelling_dataset(train_df, features_df, stores_df)

    print(f"Building star schema in {db_path}...")
    
    # 1. Dimension: Store
    stores_raw = DataLoader().load_stores()
    store_spans = integrated_df.groupby("store_id")["date"].agg(
        first_active_week="min",
        last_active_week="max"
    ).reset_index()
    store_spans["first_active_week"] = store_spans["first_active_week"].dt.strftime("%Y-%m-%d")
    store_spans["last_active_week"] = store_spans["last_active_week"].dt.strftime("%Y-%m-%d")
    
    dim_store = stores_raw.rename(columns={
        "Store": "store_id",
        "Type": "store_type",
        "Size": "store_size"
    }).merge(store_spans, on="store_id", how="left")

    # 2. Dimension: Department
    dim_dept = pd.DataFrame({"dept_id": sorted(integrated_df["dept_id"].unique())})

    # 3. Dimension: Date
    # Include all dates from train, test and features
    loader = DataLoader()
    feat_raw = loader.load_features()
    test_raw = loader.load_test()
    all_dates = pd.Series(pd.concat([
        integrated_df["date"],
        pd.to_datetime(feat_raw["Date"]),
        pd.to_datetime(test_raw["Date"])
    ])).drop_duplicates().sort_values().reset_index(drop=True)

    holiday_dates = set(feat_raw.loc[feat_raw["IsHoliday"] == True, "Date"].dt.strftime("%Y-%m-%d"))

    dim_date = pd.DataFrame({"full_date_dt": all_dates})
    dim_date["date_id"] = dim_date["full_date_dt"].dt.strftime("%Y%m%d").astype(int)
    dim_date["full_date"] = dim_date["full_date_dt"].dt.strftime("%Y-%m-%d")
    dim_date["year"] = dim_date["full_date_dt"].dt.year
    dim_date["quarter"] = dim_date["full_date_dt"].dt.quarter
    dim_date["month"] = dim_date["full_date_dt"].dt.month
    dim_date["month_name"] = dim_date["full_date_dt"].dt.strftime("%B")
    dim_date["week_of_year"] = dim_date["full_date_dt"].dt.isocalendar().week.astype(int)
    dim_date["is_holiday_week"] = dim_date["full_date"].isin(holiday_dates).astype(int)
    dim_date = dim_date.drop(columns=["full_date_dt"])

    # 4. Fact Table: fact_sales
    fact = integrated_df.copy()
    fact["date_id"] = fact["date"].dt.strftime("%Y%m%d").astype(int)
    
    fact_cols = [
        "store_id", "dept_id", "date_id", "weekly_sales", "returns_flag",
        "is_holiday", "temperature", "fuel_price", "cpi", "unemployment",
        "markdown1", "markdown2", "markdown3", "markdown4", "markdown5"
    ]
    fact_sales = fact[fact_cols].copy()

    # Recreate SQLite database
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Apply DDL schema
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Insert dimensions and fact table
    dim_store.to_sql("dim_store", conn, if_exists="append", index=False)
    dim_dept.to_sql("dim_dept", conn, if_exists="append", index=False)
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    fact_sales.to_sql("fact_sales", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    print(f"Database successfully created at {db_path}:")
    print(f"  - dim_store: {len(dim_store):,} rows")
    print(f"  - dim_dept: {len(dim_dept):,} rows")
    print(f"  - dim_date: {len(dim_date):,} rows")
    print(f"  - fact_sales: {len(fact_sales):,} rows")

    return db_path


# Reusable SQL analytics service functions for Phase 2 / API consumption
class RetailAnalyticsService:
    """Service layer abstracting SQL analytics queries for dashboard and assistant."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parents[2] / "retailiq.db"
        else:
            self.db_path = Path(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Build it first.")
        return sqlite3.connect(str(self.db_path))

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Returns high-level KPI summary."""
        query = """
        SELECT 
            COUNT(DISTINCT store_id) AS total_stores,
            COUNT(DISTINCT dept_id) AS total_departments,
            ROUND(SUM(weekly_sales), 2) AS total_revenue,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
            ROUND(100.0 * SUM(CASE WHEN returns_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 3) AS return_rate_pct
        FROM fact_sales;
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")[0]

    def get_sales_trend(self, granularity: str = "monthly") -> List[Dict[str, Any]]:
        """Returns sales time-series aggregated by month or week."""
        if granularity == "monthly":
            query = """
            SELECT 
                d.year,
                d.month,
                d.month_name,
                d.year || '-' || printf('%02d', d.month) AS period,
                ROUND(SUM(f.weekly_sales), 2) AS sales
            FROM fact_sales f
            JOIN dim_date d ON f.date_id = d.date_id
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year, d.month;
            """
        else:
            query = """
            SELECT 
                d.full_date AS period,
                d.year,
                d.week_of_year,
                ROUND(SUM(f.weekly_sales), 2) AS sales
            FROM fact_sales f
            JOIN dim_date d ON f.date_id = d.date_id
            GROUP BY d.full_date, d.year, d.week_of_year
            ORDER BY d.full_date;
            """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    def get_store_ranking(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns top stores ranked by revenue."""
        query = f"""
        SELECT 
            s.store_id,
            s.store_type,
            s.store_size,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        GROUP BY s.store_id, s.store_type, s.store_size
        ORDER BY total_sales DESC
        LIMIT {limit};
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    def get_department_ranking(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns top departments ranked by revenue."""
        query = f"""
        SELECT 
            dept_id,
            ROUND(SUM(weekly_sales), 2) AS total_sales,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales
        FROM fact_sales
        GROUP BY dept_id
        ORDER BY total_sales DESC
        LIMIT {limit};
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    def get_promotional_effectiveness(self) -> List[Dict[str, Any]]:
        """Returns promotional markdown impact summary."""
        query = """
        SELECT 
            CASE 
                WHEN (markdown1 + markdown2 + markdown3 + markdown4 + markdown5) > 0 THEN 'Promo'
                ELSE 'No Promo'
            END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(weekly_sales), 2) AS total_sales
        FROM fact_sales
        GROUP BY period;
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    def get_holiday_analysis(self) -> List[Dict[str, Any]]:
        """Returns holiday vs non-holiday sales lift."""
        query = """
        SELECT 
            CASE WHEN is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(weekly_sales), 2) AS total_sales
        FROM fact_sales
        GROUP BY is_holiday;
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")


if __name__ == "__main__":
    build_database()
