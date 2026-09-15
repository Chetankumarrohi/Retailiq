"""
Analytical service module for RetailIQ Streamlit Application.
Provides parameterized, filter-aware SQL analytics against retailiq.db with strict read-only security.
"""
from pathlib import Path
import sqlite3
import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class SQLSecurityValidator:
    """Strict security validator preventing DDL, DML, multi-statements, and system table access."""

    FORBIDDEN_KEYWORDS = {
        "insert", "update", "delete", "drop", "alter", "create", "replace",
        "truncate", "attach", "detach", "pragma", "reindex", "vacuum",
        "grant", "revoke", "exec", "execute"
    }

    @classmethod
    def validate_query(cls, sql: str) -> Tuple[bool, str]:
        """Validates that a query is a single, safe read-only SELECT statement."""
        if not sql or not sql.strip():
            return False, "Query cannot be empty."

        cleaned = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = cleaned.strip()

        statements = [s.strip() for s in cleaned.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are strictly prohibited."

        if not statements:
            return False, "No valid SQL statement found."

        single_query = statements[0]

        if not re.match(r"^(select|with)\b", single_query, flags=re.IGNORECASE):
            return False, "Only read-only SELECT queries are permitted."

        tokens = set(re.findall(r"\b[a-zA-Z_]+\b", single_query.lower()))
        disallowed = tokens.intersection(cls.FORBIDDEN_KEYWORDS)
        if disallowed:
            return False, f"Forbidden SQL keywords detected: {', '.join(sorted(disallowed))}."

        if re.search(r"\bsqlite_\w+", single_query, flags=re.IGNORECASE):
            return False, "Access to SQLite system metadata tables is prohibited."

        return True, single_query


class AnalyticsService:
    """Service layer abstracting parameterized SQL analytics queries for RetailIQ."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parents[2] / "retailiq.db"
        else:
            self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a read-only SQLite connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Please build it first.")
        conn = sqlite3.connect(f"file:{self.db_path.resolve()}?mode=ro", uri=True)
        return conn

    def _build_where_clause(
        self,
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        alias: str = "f"
    ) -> Tuple[str, List[Any]]:
        """Constructs parameterized WHERE clause and parameter list."""
        conditions = []
        params = []
        prefix = f"{alias}." if alias else ""

        if store_id is not None and str(store_id).strip() not in ("", "None", "0", "all", "All"):
            conditions.append(f"{prefix}store_id = ?")
            params.append(int(store_id))

        if dept_id is not None and str(dept_id).strip() not in ("", "None", "0", "all", "All"):
            conditions.append(f"{prefix}dept_id = ?")
            params.append(int(dept_id))

        if conditions:
            return "WHERE " + " AND ".join(conditions), params
        return "", []

    def get_stores_list(self) -> List[Dict[str, Any]]:
        """Returns list of all active stores with metadata."""
        query = "SELECT store_id, store_type, store_size FROM dim_store ORDER BY store_id;"
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    def get_departments_list(self, store_id: Optional[int] = None) -> List[int]:
        """Returns list of departments, optionally filtered by store_id."""
        where_sql, params = self._build_where_clause(store_id=store_id, alias="")
        query = f"SELECT DISTINCT dept_id FROM fact_sales {where_sql} ORDER BY dept_id;"
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        return df["dept_id"].tolist()

    def get_summary(
        self,
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculates dynamic, filter-aware KPI summary metrics."""
        where_f, params_f = self._build_where_clause(store_id, dept_id, "f")

        query_main = f"""
        SELECT
            COUNT(DISTINCT f.store_id) AS total_stores,
            COUNT(DISTINCT f.dept_id) AS total_departments,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
            ROUND(100.0 * SUM(CASE WHEN f.returns_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 3) AS return_rate_pct
        FROM fact_sales f
        {where_f};
        """

        query_holiday = f"""
        SELECT
            f.is_holiday,
            ROUND(AVG(f.weekly_sales), 2) AS avg_sales
        FROM fact_sales f
        {where_f}
        GROUP BY f.is_holiday;
        """

        query_promo = f"""
        SELECT
            CASE WHEN (f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5) > 0 THEN 1 ELSE 0 END AS has_promo,
            ROUND(AVG(f.weekly_sales), 2) AS avg_sales
        FROM fact_sales f
        {where_f}
        GROUP BY has_promo;
        """

        query_top_store = f"""
        SELECT f.store_id, ROUND(SUM(f.weekly_sales), 2) AS store_sales
        FROM fact_sales f
        {where_f}
        GROUP BY f.store_id
        ORDER BY store_sales DESC
        LIMIT 1;
        """

        query_top_dept = f"""
        SELECT f.dept_id, ROUND(SUM(f.weekly_sales), 2) AS dept_sales
        FROM fact_sales f
        {where_f}
        GROUP BY f.dept_id
        ORDER BY dept_sales DESC
        LIMIT 1;
        """

        with self.get_connection() as conn:
            main_df = pd.read_sql(query_main, conn, params=params_f)
            hol_df = pd.read_sql(query_holiday, conn, params=params_f)
            promo_df = pd.read_sql(query_promo, conn, params=params_f)
            top_store_df = pd.read_sql(query_top_store, conn, params=params_f)
            top_dept_df = pd.read_sql(query_top_dept, conn, params=params_f)

        summary = main_df.to_dict(orient="records")[0] if not main_df.empty else {}

        # Holiday lift calculation
        hol_sales = {row["is_holiday"]: row["avg_sales"] for row in hol_df.to_dict(orient="records")}
        non_hol_avg = hol_sales.get(0, 0.0)
        hol_avg = hol_sales.get(1, 0.0)
        if non_hol_avg and non_hol_avg > 0:
            holiday_lift = round(((hol_avg - non_hol_avg) / non_hol_avg) * 100.0, 2)
        else:
            holiday_lift = 0.0
        summary["holiday_lift_pct"] = holiday_lift

        # Promo lift calculation
        promo_sales = {row["has_promo"]: row["avg_sales"] for row in promo_df.to_dict(orient="records")}
        non_promo_avg = promo_sales.get(0, 0.0)
        promo_avg = promo_sales.get(1, 0.0)
        if non_promo_avg and non_promo_avg > 0:
            promo_lift = round(((promo_avg - non_promo_avg) / non_promo_avg) * 100.0, 2)
        else:
            promo_lift = 0.0
        summary["promotion_lift_pct"] = promo_lift

        # Top store/dept metadata
        if not top_store_df.empty:
            summary["top_store_id"] = int(top_store_df.iloc[0]["store_id"])
            summary["top_store_sales"] = float(top_store_df.iloc[0]["store_sales"])
        else:
            summary["top_store_id"] = store_id or 1
            summary["top_store_sales"] = summary.get("total_sales", 0.0)

        if not top_dept_df.empty:
            summary["top_dept_id"] = int(top_dept_df.iloc[0]["dept_id"])
            summary["top_dept_sales"] = float(top_dept_df.iloc[0]["dept_sales"])
        else:
            summary["top_dept_id"] = dept_id or 1
            summary["top_dept_sales"] = summary.get("total_sales", 0.0)

        return summary

    def get_sales_trend(
        self,
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        granularity: str = "monthly"
    ) -> List[Dict[str, Any]]:
        """Returns time series trend aggregated by month or week."""
        where_f, params_f = self._build_where_clause(store_id, dept_id, "f")

        if granularity == "weekly":
            query = f"""
            SELECT
                d.full_date AS period,
                d.year,
                d.week_of_year,
                ROUND(SUM(f.weekly_sales), 2) AS sales
            FROM fact_sales f
            JOIN dim_date d ON f.date_id = d.date_id
            {where_f}
            GROUP BY d.full_date, d.year, d.week_of_year
            ORDER BY d.full_date ASC;
            """
        else:
            query = f"""
            SELECT
                d.year || '-' || printf('%02d', d.month) AS period,
                d.year,
                d.month,
                d.month_name,
                ROUND(SUM(f.weekly_sales), 2) AS sales
            FROM fact_sales f
            JOIN dim_date d ON f.date_id = d.date_id
            {where_f}
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year ASC, d.month ASC;
            """

        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params_f)
        return df.to_dict(orient="records")

    def get_store_ranking(
        self,
        limit: int = 15,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns top stores ranked by sales."""
        where_f, params_f = self._build_where_clause(None, dept_id, "f")
        query = f"""
        SELECT
            s.store_id,
            s.store_type,
            s.store_size,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        {where_f}
        GROUP BY s.store_id, s.store_type, s.store_size
        ORDER BY total_sales DESC
        LIMIT {limit};
        """
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params_f)
        return df.to_dict(orient="records")

    def get_department_ranking(
        self,
        limit: int = 15,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns top departments ranked by sales."""
        where_f, params_f = self._build_where_clause(store_id, None, "f")
        query = f"""
        SELECT
            f.dept_id,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales
        FROM fact_sales f
        {where_f}
        GROUP BY f.dept_id
        ORDER BY total_sales DESC
        LIMIT {limit};
        """
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params_f)
        return df.to_dict(orient="records")

    def get_holiday_analysis(
        self,
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns holiday vs non-holiday sales breakdown."""
        where_f, params_f = self._build_where_clause(store_id, dept_id, "f")
        query = f"""
        SELECT
            CASE WHEN f.is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales
        FROM fact_sales f
        {where_f}
        GROUP BY f.is_holiday;
        """
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params_f)
        return df.to_dict(orient="records")

    def get_promotion_effectiveness(
        self,
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns promotional markdown impact breakdown."""
        where_f, params_f = self._build_where_clause(store_id, dept_id, "f")
        query = f"""
        SELECT
            CASE
                WHEN (f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5) > 0 THEN 'Promo Markdown'
                ELSE 'No Markdown'
            END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales
        FROM fact_sales f
        {where_f}
        GROUP BY period;
        """
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params_f)
        return df.to_dict(orient="records")

    def execute_safe_query(self, sql: str, max_rows: int = 25) -> Dict[str, Any]:
        """Safely executes custom SQL query with validation and limits."""
        is_valid, validated_sql = SQLSecurityValidator.validate_query(sql)
        if not is_valid:
            return {
                "success": False,
                "error": f"Security validation failed: {validated_sql}",
                "data": None
            }

        try:
            with self.get_connection() as conn:
                df = pd.read_sql(validated_sql, conn)
                preview = df.head(max_rows)
                return {
                    "success": True,
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "data": preview.to_dict(orient="records"),
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"SQL execution error: {str(e)}",
                "data": None
            }
