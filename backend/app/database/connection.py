"""
SQLite database connection and query execution helper for RetailIQ.
Provides safe read-only connections and parameterized query utilities.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator
import pandas as pd
from backend.app.core.config import settings


@contextmanager
def get_db_connection(read_only: bool = True) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding a SQLite connection.
    Defaults to read-only URI mode to prevent accidental database mutations.
    """
    db_path = settings.DATABASE_PATH
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Verify Phase 1 database build.")

    if read_only:
        # Open in read-only URI mode
        uri = f"file:{db_path.resolve()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10.0)
    else:
        conn = sqlite3.connect(str(db_path), timeout=10.0)

    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: Optional[tuple] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Executes a SQL SELECT query with parameter binding and returns a list of dictionaries."""
    with get_db_connection(read_only=True) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchmany(limit)
        return [dict(row) for row in rows]


def check_database_health() -> Dict[str, Any]:
    """Checks database availability and returns row counts for health endpoints."""
    try:
        with get_db_connection(read_only=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fact_sales")
            fact_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dim_store")
            store_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dim_dept")
            dept_count = cursor.fetchone()[0]
            return {
                "status": "connected",
                "fact_sales_rows": fact_count,
                "stores_count": store_count,
                "departments_count": dept_count
            }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }
