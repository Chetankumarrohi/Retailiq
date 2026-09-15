"""
Security validator for RetailIQ analytical queries and assistant execution.
Guarantees strict read-only execution against allowed analytical star schema tables.
"""
import re
from typing import Tuple, List, Set


class SQLSecurityValidator:
    """Validates and sanitizes SQL queries before execution against the analytical database."""

    # Disallowed DDL / DML / administrative commands
    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "ATTACH", "DETACH", "PRAGMA", "REPLACE", "TRUNCATE", "VACUUM",
        "EXEC", "EXECUTE", "GRANT", "REVOKE", "INTO OUTFILE", "LOAD DATA",
        "TRANSACTION", "COMMIT", "ROLLBACK", "SAVEPOINT"
    ]

    ALLOWED_TABLES: Set[str] = {
        "fact_sales",
        "dim_store",
        "dim_dept",
        "dim_date"
    }

    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, str]:
        """
        Validates that a query is strictly a single, read-only SELECT statement
        referencing only approved analytical tables.
        Returns: (is_valid: bool, error_or_cleaned_query: str)
        """
        cleaned = query.strip()
        if not cleaned:
            return False, "Query cannot be empty."

        # Remove trailing semicolon if single query
        if cleaned.endswith(";"):
            cleaned = cleaned[:-1].strip()

        # Check for multiple statements (semicolon inside)
        if ";" in cleaned:
            return False, "Multiple SQL statements in a single execution are prohibited."

        # Check query begins with SELECT or WITH (for CTEs)
        if not re.match(r"^\s*(SELECT|WITH)\b", cleaned, re.IGNORECASE):
            return False, "Only SELECT or WITH queries are permitted."

        # Check for forbidden keywords as standalone tokens
        for kw in cls.FORBIDDEN_KEYWORDS:
            pattern = rf"\b{kw}\b"
            if re.search(pattern, cleaned, re.IGNORECASE):
                return False, f"Forbidden SQL operation detected: '{kw}'."

        # Extract referenced table names and ensure they are permitted
        # Simple regex matching FROM/JOIN tokens
        table_matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", cleaned, re.IGNORECASE)
        for tbl in table_matches:
            tbl_clean = tbl.lower()
            # CTE names can be present, but system tables like sqlite_master or non-analytics tables must be blocked
            if tbl_clean.startswith("sqlite_") or (tbl_clean not in cls.ALLOWED_TABLES and not cls._is_cte_name(tbl_clean, cleaned)):
                return False, f"Access to table or schema '{tbl}' is not permitted."

        return True, cleaned

    @classmethod
    def _is_cte_name(cls, name: str, query: str) -> bool:
        """Checks if a table name is a locally defined Common Table Expression (CTE)."""
        cte_matches = re.findall(r"\bWITH\s+([a-zA-Z0-9_]+)\s+AS|\,\s*([a-zA-Z0-9_]+)\s+AS", query, re.IGNORECASE)
        cte_names = {m[0].lower() or m[1].lower() for m in cte_matches if m[0] or m[1]}
        return name in cte_names
