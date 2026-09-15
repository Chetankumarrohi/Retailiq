"""
Autonomous tool definitions and execution functions for RetailIQ AI Assistant.
Tools:
1. sql_analytics_tool: Sandboxed, read-only SQL queries against retailiq.db
2. forecast_tool: Multi-step ML predictions via ForecastService
3. retrieval_tool: Grounded internal documentation lookup via PolicyRetriever
"""
import json
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Tuple
from backend.app.core.security import SQLSecurityValidator
from backend.app.database.connection import get_db_connection
from backend.app.services.forecast_service import ForecastService
from backend.app.schemas.forecast import ForecastRequest
from backend.app.agent.retrieval import PolicyRetriever


# ==========================================================
# Tool 1: SQL Analytics Tool
# ==========================================================
def sql_analytics_tool(query: str) -> Dict[str, Any]:
    """
    Executes a read-only SQL query against the analytical star schema.
    Applies security validation to block DDL/DML, multi-statements, and system tables.
    """
    is_valid, validated_or_error = SQLSecurityValidator.validate_query(query)
    if not is_valid:
        return {
            "success": False,
            "error": f"Security validation failed: {validated_or_error}",
            "data": None
        }

    try:
        with get_db_connection(read_only=True) as conn:
            df = pd.read_sql(validated_or_error, conn)
            # Limit results to top 25 rows for assistant consumption
            preview_df = df.head(25)
            return {
                "success": True,
                "row_count": len(df),
                "columns": list(df.columns),
                "data": preview_df.to_dict(orient="records"),
                "formatted_table": preview_df.to_markdown(index=False) if not preview_df.empty else "No records found."
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"SQL execution error: {str(e)}",
            "data": None
        }


# ==========================================================
# Tool 2: Forecast Tool
# ==========================================================
def forecast_tool(store_id: int, dept_id: int, horizon_weeks: int = 4) -> Dict[str, Any]:
    """
    Invokes the production LightGBM forecasting engine for a given store and department.
    """
    try:
        req = ForecastRequest(store_id=store_id, dept_id=dept_id, horizon_weeks=horizon_weeks)
        forecast_resp = ForecastService.generate_forecast(req)
        
        preds_summary = [
            f"Week {p.week} (Step {p.step}): ${p.weekly_sales:,.2f} {'[Holiday]' if p.is_holiday else ''}"
            for p in forecast_resp.predictions
        ]
        
        return {
            "success": True,
            "store_id": store_id,
            "dept_id": dept_id,
            "horizon_weeks": horizon_weeks,
            "model_version": forecast_resp.model_version,
            "historical_mean_sales": forecast_resp.historical_summary.historical_mean_sales,
            "last_known_sales": forecast_resp.historical_summary.last_known_sales,
            "predictions": [p.model_dump() for p in forecast_resp.predictions],
            "summary_text": "\n".join(preds_summary)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "store_id": store_id,
            "dept_id": dept_id
        }


# ==========================================================
# Tool 3: Policy Retrieval Tool
# ==========================================================
def retrieval_tool(query: str) -> Dict[str, Any]:
    """
    Searches internal documentation (policy_docs.txt) for inventory rules, markdowns, returns, SOPs.
    """
    try:
        retriever = PolicyRetriever.get_instance()
        results = retriever.search(query, top_k=2)
        if not results:
            return {
                "success": True,
                "found": False,
                "message": "No relevant policy section found matching the query.",
                "citations": []
            }
        
        return {
            "success": True,
            "found": True,
            "citations": results,
            "primary_section": results[0]["section"],
            "primary_text": results[0]["text"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Retrieval error: {str(e)}",
            "citations": []
        }


# ==========================================================
# Tool Schemas for AI Planners (OpenAI / Claude Tool-Calling)
# ==========================================================
AGENT_TOOL_DEFINITIONS = [
    {
        "name": "sql_analytics_tool",
        "description": "Run a read-only SQL query against the SQLite star schema database (fact_sales, dim_store, dim_dept, dim_date) to answer historical sales, rankings, aggregations, and business metrics questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A single valid SQLite SELECT query adhering to the star schema."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "forecast_tool",
        "description": "Generate future weekly demand forecasts for a specific store and department across 1 to 12 weeks using the trained LightGBM ML model.",
        "parameters": {
            "type": "object",
            "properties": {
                "store_id": {"type": "integer", "description": "Store ID (1 to 45)."},
                "dept_id": {"type": "integer", "description": "Department ID (1 to 99)."},
                "horizon_weeks": {"type": "integer", "description": "Number of future weeks to forecast (1 to 12, default 4)."}
            },
            "required": ["store_id", "dept_id"]
        }
    },
    {
        "name": "retrieval_tool",
        "description": "Search internal company policy documents for rules on customer returns, promotional markdowns, inventory coverage targets, supplier terms, and standard operating procedures (SOPs).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query or natural language policy question."
                }
            },
            "required": ["query"]
        }
    }
]
