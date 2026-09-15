"""
Analytics service for Executive Dashboard and data queries.
Interacts with the SQLite star schema database using parameterized queries.
"""
from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
from backend.app.database.connection import get_db_connection


class AnalyticsService:
    """Service providing aggregated business metrics and filtered trends."""

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """Calculates executive KPI metrics from fact_sales and dimension tables."""
        with get_db_connection(read_only=True) as conn:
            # Overall totals
            tot_query = """
            SELECT 
                COUNT(DISTINCT store_id) AS total_stores,
                COUNT(DISTINCT dept_id) AS total_departments,
                ROUND(SUM(weekly_sales), 2) AS total_revenue,
                ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
                ROUND(100.0 * SUM(CASE WHEN returns_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 3) AS return_rate_pct
            FROM fact_sales;
            """
            tot_row = pd.read_sql(tot_query, conn).iloc[0]

            # Top store
            top_store_query = """
            SELECT store_id, SUM(weekly_sales) AS revenue
            FROM fact_sales GROUP BY store_id ORDER BY revenue DESC LIMIT 1;
            """
            top_store = pd.read_sql(top_store_query, conn).iloc[0]

            # Top department
            top_dept_query = """
            SELECT dept_id, SUM(weekly_sales) AS revenue
            FROM fact_sales GROUP BY dept_id ORDER BY revenue DESC LIMIT 1;
            """
            top_dept = pd.read_sql(top_dept_query, conn).iloc[0]

            # Holiday lift
            hol_query = """
            SELECT is_holiday, AVG(weekly_sales) AS avg_sales
            FROM fact_sales GROUP BY is_holiday;
            """
            hol_df = pd.read_sql(hol_query, conn).set_index("is_holiday")
            hol_avg = hol_df.loc[1, "avg_sales"] if 1 in hol_df.index else 0
            non_hol_avg = hol_df.loc[0, "avg_sales"] if 0 in hol_df.index else 1
            hol_lift = round(((hol_avg - non_hol_avg) / non_hol_avg) * 100.0, 2)

            # Promo lift
            promo_query = """
            SELECT 
                CASE WHEN (markdown1 + markdown2 + markdown3 + markdown4 + markdown5) > 0 THEN 1 ELSE 0 END AS promo,
                AVG(weekly_sales) AS avg_sales
            FROM fact_sales GROUP BY promo;
            """
            promo_df = pd.read_sql(promo_query, conn).set_index("promo")
            promo_avg = promo_df.loc[1, "avg_sales"] if 1 in promo_df.index else 0
            non_promo_avg = promo_df.loc[0, "avg_sales"] if 0 in promo_df.index else 1
            promo_lift = round(((promo_avg - non_promo_avg) / non_promo_avg) * 100.0, 2)

        return {
            "total_revenue": float(tot_row["total_revenue"]),
            "avg_weekly_sales": float(tot_row["avg_weekly_sales"]),
            "total_stores": int(tot_row["total_stores"]),
            "total_departments": int(tot_row["total_departments"]),
            "return_rate_pct": float(tot_row["return_rate_pct"]),
            "top_store_id": int(top_store["store_id"]),
            "top_store_revenue": float(round(top_store["revenue"], 2)),
            "top_dept_id": int(top_dept["dept_id"]),
            "top_dept_revenue": float(round(top_dept["revenue"], 2)),
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
    def get_store_ranking(limit: int = 15) -> List[Dict[str, Any]]:
        """Returns top stores ranked by revenue."""
        query = """
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
        LIMIT ?;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=[limit])
        return df.to_dict(orient="records")

    @staticmethod
    def get_department_ranking(limit: int = 15, store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns top departments ranked by revenue."""
        where_sql = "WHERE store_id = ?" if store_id is not None else ""
        params = [store_id, limit] if store_id is not None else [limit]

        query = f"""
        WITH dept_totals AS (
            SELECT 
                dept_id,
                SUM(weekly_sales) AS total_sales,
                AVG(weekly_sales) AS avg_weekly_sales
            FROM fact_sales
            {where_sql}
            GROUP BY dept_id
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
    def get_promotion_effectiveness(store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns promotional markdown impact."""
        where_sql = "WHERE store_id = ?" if store_id is not None else ""
        params = [store_id] if store_id is not None else []

        query = f"""
        SELECT 
            CASE 
                WHEN (markdown1 + markdown2 + markdown3 + markdown4 + markdown5) > 0 THEN 'Promo'
                ELSE 'No Promo'
            END AS period,
            COUNT(*) AS observation_count,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(weekly_sales), 2) AS total_sales
        FROM fact_sales
        {where_sql}
        GROUP BY period;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_holiday_analysis(store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns holiday vs non-holiday performance comparison."""
        where_sql = "WHERE store_id = ?" if store_id is not None else ""
        params = [store_id] if store_id is not None else []

        query = f"""
        SELECT 
            CASE WHEN is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS period,
            is_holiday,
            COUNT(*) AS observation_count,
            ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
            ROUND(SUM(weekly_sales), 2) AS total_sales
        FROM fact_sales
        {where_sql}
        GROUP BY is_holiday;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df.to_dict(orient="records")

    @staticmethod
    def get_store_types() -> List[Dict[str, Any]]:
        """Returns performance metrics grouped by store type (A, B, C)."""
        query = """
        WITH type_totals AS (
            SELECT 
                s.store_type,
                COUNT(DISTINCT s.store_id) AS num_stores,
                AVG(s.store_size) AS avg_store_size,
                SUM(f.weekly_sales) AS total_sales,
                AVG(f.weekly_sales) AS avg_weekly_sales
            FROM fact_sales f
            JOIN dim_store s ON f.store_id = s.store_id
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
            ROUND(100.0 * t.total_sales / g.chain_sales, 2) AS revenue_share_pct
        FROM type_totals t
        CROSS JOIN grand_total g
        ORDER BY t.total_sales DESC;
        """
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(query, conn)
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
