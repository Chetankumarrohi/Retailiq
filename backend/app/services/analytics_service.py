"""
Analytics service for Executive Dashboard and data queries.
Interacts with the SQLite star schema database using parameterized queries.
"""
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import pandas as pd
from backend.app.database.connection import get_db_connection


class AnalyticsService:
    """Service providing aggregated business metrics and filter-aware analytics."""

    @staticmethod
    def _build_where_clause(
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        alias: str = "f"
    ) -> Tuple[str, List[Any]]:
        """Builds a safe, parameterized WHERE clause for store and department filters."""
        clauses = []
        params: List[Any] = []
        if store_id is not None:
            clauses.append(f"{alias}.store_id = ?")
            params.append(store_id)
        if dept_id is not None:
            clauses.append(f"{alias}.dept_id = ?")
            params.append(dept_id)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, params

    @staticmethod
    def get_summary(
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates filter-aware executive KPI metrics from fact_sales and dimension tables.
        Recalculates total revenue, average weekly sales, store/dept counts, top performers,
        and holiday/promo lifts for the selected filter combination.
        """
        where_sql, params = AnalyticsService._build_where_clause(store_id, dept_id, alias="f")

        with get_db_connection(read_only=True) as conn:
            # 1. Overall totals on filtered subset
            tot_query = f"""
            SELECT 
                COUNT(DISTINCT f.store_id) AS total_stores,
                COUNT(DISTINCT f.dept_id) AS total_departments,
                COALESCE(ROUND(SUM(f.weekly_sales), 2), 0.0) AS total_revenue,
                COALESCE(ROUND(AVG(f.weekly_sales), 2), 0.0) AS avg_weekly_sales,
                COALESCE(ROUND(100.0 * SUM(CASE WHEN f.returns_flag = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 3), 0.0) AS return_rate_pct
            FROM fact_sales f
            {where_sql};
            """
            tot_row = pd.read_sql(tot_query, conn, params=params).iloc[0]

            # 2. Top Store (or selected store)
            if store_id is not None:
                # If specific store selected, report that store and its sales within filter
                store_q = f"""
                SELECT f.store_id, COALESCE(SUM(f.weekly_sales), 0.0) AS revenue
                FROM fact_sales f
                {where_sql}
                GROUP BY f.store_id;
                """
                store_df = pd.read_sql(store_q, conn, params=params)
                if not store_df.empty:
                    top_store_id = int(store_df.iloc[0]["store_id"])
                    top_store_revenue = float(round(store_df.iloc[0]["revenue"], 2))
                else:
                    top_store_id = store_id
                    top_store_revenue = 0.0
            else:
                top_store_q = f"""
                SELECT f.store_id, COALESCE(SUM(f.weekly_sales), 0.0) AS revenue
                FROM fact_sales f
                {where_sql}
                GROUP BY f.store_id
                ORDER BY revenue DESC
                LIMIT 1;
                """
                top_store_df = pd.read_sql(top_store_q, conn, params=params)
                if not top_store_df.empty:
                    top_store_id = int(top_store_df.iloc[0]["store_id"])
                    top_store_revenue = float(round(top_store_df.iloc[0]["revenue"], 2))
                else:
                    top_store_id = 0
                    top_store_revenue = 0.0

            # 3. Top Department (or selected department)
            if dept_id is not None:
                # If specific dept selected, report that dept and its sales within filter
                dept_q = f"""
                SELECT f.dept_id, COALESCE(SUM(f.weekly_sales), 0.0) AS revenue
                FROM fact_sales f
                {where_sql}
                GROUP BY f.dept_id;
                """
                dept_df = pd.read_sql(dept_q, conn, params=params)
                if not dept_df.empty:
                    top_dept_id = int(dept_df.iloc[0]["dept_id"])
                    top_dept_revenue = float(round(dept_df.iloc[0]["revenue"], 2))
                else:
                    top_dept_id = dept_id
                    top_dept_revenue = 0.0
            else:
                top_dept_q = f"""
                SELECT f.dept_id, COALESCE(SUM(f.weekly_sales), 0.0) AS revenue
                FROM fact_sales f
                {where_sql}
                GROUP BY f.dept_id
                ORDER BY revenue DESC
                LIMIT 1;
                """
                top_dept_df = pd.read_sql(top_dept_q, conn, params=params)
                if not top_dept_df.empty:
                    top_dept_id = int(top_dept_df.iloc[0]["dept_id"])
                    top_dept_revenue = float(round(top_dept_df.iloc[0]["revenue"], 2))
                else:
                    top_dept_id = 0
                    top_dept_revenue = 0.0

            # 4. Holiday lift on filtered subset
            hol_query = f"""
            SELECT f.is_holiday, AVG(f.weekly_sales) AS avg_sales
            FROM fact_sales f
            {where_sql}
            GROUP BY f.is_holiday;
            """
            hol_df = pd.read_sql(hol_query, conn, params=params).set_index("is_holiday")
            hol_avg = hol_df.loc[1, "avg_sales"] if 1 in hol_df.index else None
            non_hol_avg = hol_df.loc[0, "avg_sales"] if 0 in hol_df.index else None
            if hol_avg is not None and non_hol_avg is not None and non_hol_avg > 0:
                hol_lift = round(((hol_avg - non_hol_avg) / non_hol_avg) * 100.0, 2)
            else:
                hol_lift = 0.0

            # 5. Promo lift on filtered subset
            promo_query = f"""
            SELECT 
                CASE WHEN (f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5) > 0 THEN 1 ELSE 0 END AS promo,
                AVG(f.weekly_sales) AS avg_sales
            FROM fact_sales f
            {where_sql}
            GROUP BY promo;
            """
            promo_df = pd.read_sql(promo_query, conn, params=params).set_index("promo")
            promo_avg = promo_df.loc[1, "avg_sales"] if 1 in promo_df.index else None
            non_promo_avg = promo_df.loc[0, "avg_sales"] if 0 in promo_df.index else None
            if promo_avg is not None and non_promo_avg is not None and non_promo_avg > 0:
                promo_lift = round(((promo_avg - non_promo_avg) / non_promo_avg) * 100.0, 2)
            else:
                promo_lift = 0.0

        return {
            "total_revenue": float(tot_row["total_revenue"]),
            "avg_weekly_sales": float(tot_row["avg_weekly_sales"]),
            "total_stores": int(tot_row["total_stores"]),
            "total_departments": int(tot_row["total_departments"]),
            "return_rate_pct": float(tot_row["return_rate_pct"]),
            "top_store_id": top_store_id,
            "top_store_revenue": top_store_revenue,
            "top_dept_id": top_dept_id,
            "top_dept_revenue": top_dept_revenue,
            "holiday_lift_pct": hol_lift,
            "promotion_lift_pct": promo_lift
        }

    @staticmethod
    def get_sales_trend(
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        granularity: str = "monthly",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns time-series revenue aggregated by month or week with optional filters."""
        where_clauses = []
        params = []

        if store_id is not None:
            where_clauses.append("f.store_id = ?")
            params.append(store_id)
        if dept_id is not None:
            where_clauses.append("f.dept_id = ?")
            params.append(dept_id)
        if start_date:
            where_clauses.append("d.full_date >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("d.full_date <= ?")
            params.append(end_date)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with get_db_connection(read_only=True) as conn:
            if granularity == "monthly":
                query = f"""
                SELECT 
                    d.year || '-' || printf('%02d', d.month) AS period,
                    d.year,
                    d.month,
                    NULL AS week,
                    ROUND(SUM(f.weekly_sales), 2) AS sales
                FROM fact_sales f
                JOIN dim_date d ON f.date_id = d.date_id
                {where_sql}
                GROUP BY d.year, d.month
                ORDER BY d.year, d.month;
                """
            else:
                query = f"""
                SELECT 
                    d.full_date AS period,
                    d.year,
                    d.month,
                    d.week_of_year AS week,
                    ROUND(SUM(f.weekly_sales), 2) AS sales
                FROM fact_sales f
                JOIN dim_date d ON f.date_id = d.date_id
                {where_sql}
                GROUP BY d.full_date, d.year, d.month, d.week_of_year
                ORDER BY d.full_date;
                """
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_store_ranking(
        limit: int = 15,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns top stores ranked by revenue, optionally filtered by department."""
        where_sql, params = AnalyticsService._build_where_clause(dept_id=dept_id, alias="f")
        params.append(limit)

        query = f"""
        SELECT 
            s.store_id,
            s.store_type,
            s.store_size,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales
        FROM fact_sales f
        JOIN dim_store s ON f.store_id = s.store_id
        {where_sql}
        GROUP BY s.store_id, s.store_type, s.store_size
        ORDER BY total_sales DESC
        LIMIT ?;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_department_ranking(
        limit: int = 15,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns top departments ranked by revenue, optionally filtered by store."""
        where_sql, params = AnalyticsService._build_where_clause(store_id=store_id, alias="f")
        params.append(limit)

        query = f"""
        WITH dept_totals AS (
            SELECT 
                f.dept_id,
                SUM(f.weekly_sales) AS total_sales,
                AVG(f.weekly_sales) AS avg_weekly_sales
            FROM fact_sales f
            {where_sql}
            GROUP BY f.dept_id
        ),
        grand_total AS (
            SELECT SUM(total_sales) AS chain_sales FROM dept_totals
        )
        SELECT 
            d.dept_id,
            ROUND(d.total_sales, 2) AS total_sales,
            ROUND(d.avg_weekly_sales, 2) AS avg_weekly_sales,
            ROUND(100.0 * d.total_sales / NULLIF(g.chain_sales, 0), 2) AS revenue_share_pct
        FROM dept_totals d
        CROSS JOIN grand_total g
        ORDER BY d.total_sales DESC
        LIMIT ?;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_promotion_effectiveness(
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns promotional markdown impact on filtered subset."""
        where_sql, params = AnalyticsService._build_where_clause(store_id, dept_id, alias="f")

        query = f"""
        SELECT 
            CASE 
                WHEN (f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5) > 0 THEN 'Promo'
                ELSE 'No Promo'
            END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales
        FROM fact_sales f
        {where_sql}
        GROUP BY period;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_holiday_analysis(
        store_id: Optional[int] = None,
        dept_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns holiday vs non-holiday performance comparison on filtered subset."""
        where_sql, params = AnalyticsService._build_where_clause(store_id, dept_id, alias="f")

        query = f"""
        SELECT 
            CASE WHEN f.is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS period,
            f.is_holiday,
            COUNT(*) AS observation_count,
            ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(f.weekly_sales), 2) AS total_sales
        FROM fact_sales f
        {where_sql}
        GROUP BY f.is_holiday;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_store_types(dept_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns performance metrics grouped by store type (A, B, C), optionally filtered by department."""
        where_sql, params = AnalyticsService._build_where_clause(dept_id=dept_id, alias="f")

        query = f"""
        WITH type_totals AS (
            SELECT 
                s.store_type,
                COUNT(DISTINCT s.store_id) AS num_stores,
                AVG(s.store_size) AS avg_store_size,
                SUM(f.weekly_sales) AS total_sales,
                AVG(f.weekly_sales) AS avg_weekly_sales
            FROM fact_sales f
            JOIN dim_store s ON f.store_id = s.store_id
            {where_sql}
            GROUP BY s.store_type
        ),
        grand_total AS (
            SELECT SUM(total_sales) AS chain_sales FROM type_totals
        )
        SELECT 
            t.store_type,
            t.num_stores,
            ROUND(t.avg_store_size, 0) AS avg_store_size,
            ROUND(t.total_sales, 2) AS total_sales,
            ROUND(t.avg_weekly_sales, 2) AS avg_weekly_sales,
            ROUND(100.0 * t.total_sales / NULLIF(g.chain_sales, 0), 2) AS revenue_share_pct
        FROM type_totals t
        CROSS JOIN grand_total g
        ORDER BY t.total_sales DESC;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_stores() -> List[Dict[str, Any]]:
        """Returns all stores and their metadata."""
        query = "SELECT store_id, store_type, store_size, first_active_week, last_active_week FROM dim_store ORDER BY store_id;"
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")

    @staticmethod
    def get_departments(store_id: Optional[int] = None) -> List[int]:
        """Returns unique department IDs (optionally filtered by store)."""
        with get_db_connection(read_only=True) as conn:
            if store_id is not None:
                query = "SELECT DISTINCT dept_id FROM fact_sales WHERE store_id = ? ORDER BY dept_id;"
                df = pd.read_sql(query, conn, params=[store_id])
            else:
                query = "SELECT dept_id FROM dim_dept ORDER BY dept_id;"
                df = pd.read_sql(query, conn)
        return df["dept_id"].tolist()
