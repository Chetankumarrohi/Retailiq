"""
RetailIQ Comprehensive Automated Test Suite.
Tests API endpoints, database health, forecasting engine, multi-tool assistant, and SQL security guardrails.
"""
import pytest
import sqlite3
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import SQLSecurityValidator
from backend.app.agent.retrieval import PolicyRetriever
from src.forecasting.predictor import RetailForecasterPredictor

client = TestClient(app)


# ==========================================================
# 1. Health & Metadata Tests
# ==========================================================
def test_health_check():
    """Verify backend health endpoint returns 200 and healthy database status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy"]
    assert data["database"]["status"] == "connected"
    assert data["database"]["fact_sales_rows"] == 421570
    assert data["database"]["stores_count"] == 45
    assert data["database"]["departments_count"] == 81


def test_get_stores():
    """Verify store metadata returns 45 stores with types and sizes."""
    response = client.get("/api/stores")
    assert response.status_code == 200
    stores = response.json()
    assert len(stores) == 45
    assert all("store_id" in s and "store_type" in s and "store_size" in s for s in stores)


def test_get_departments():
    """Verify department catalog returns 81 unique departments."""
    response = client.get("/api/departments")
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) == 81
    assert all(isinstance(d, int) for d in depts)


# ==========================================================
# 2. Executive Dashboard Analytics Tests
# ==========================================================
def test_dashboard_summary():
    """Verify KPI summary matches real database calculations."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_stores"] == 45
    assert data["total_departments"] == 81
    assert data["total_revenue"] > 6.7e9  # ~$6.74B
    assert data["avg_weekly_sales"] > 15000.0


def test_sales_trend_monthly_and_weekly():
    """Verify sales trend aggregates across monthly and weekly grains."""
    # Monthly
    res_m = client.get("/api/dashboard/sales-trend?granularity=monthly")
    assert res_m.status_code == 200
    trend_m = res_m.json()
    assert len(trend_m) > 0
    assert "period" in trend_m[0] and "sales" in trend_m[0]

    # Weekly
    res_w = client.get("/api/dashboard/sales-trend?granularity=weekly")
    assert res_w.status_code == 200
    trend_w = res_w.json()
    assert len(trend_w) == 143  # 143 unique weeks in dataset


def test_sales_trend_filtered():
    """Verify sales trend respects store and department filters."""
    res = client.get("/api/dashboard/sales-trend?store_id=1&dept_id=1&granularity=monthly")
    assert res.status_code == 200
    trend = res.json()
    assert len(trend) > 0


def test_store_and_department_rankings():
    """Verify top store and department ranking leaderboards."""
    res_store = client.get("/api/dashboard/store-ranking?limit=10")
    assert res_store.status_code == 200
    stores = res_store.json()
    assert len(stores) == 10
    assert stores[0]["store_id"] == 20  # Top store is Store 20

    res_dept = client.get("/api/dashboard/department-ranking?limit=10")
    assert res_dept.status_code == 200
    depts = res_dept.json()
    assert len(depts) == 10
    assert depts[0]["dept_id"] == 92  # Top dept is Dept 92


def test_holiday_and_promotion_analytics():
    """Verify holiday lift and markdown promotion analytics."""
    res_hol = client.get("/api/dashboard/holiday-analysis")
    assert res_hol.status_code == 200
    hol = res_hol.json()
    assert len(hol) == 2

    res_promo = client.get("/api/dashboard/promotion-effectiveness")
    assert res_promo.status_code == 200
    promo = res_promo.json()
    assert len(promo) == 2


def test_store_types_distribution():
    """Verify store types breakdown for types A, B, and C."""
    res = client.get("/api/dashboard/store-types")
    assert res.status_code == 200
    types = res.json()
    assert len(types) == 3
    type_names = {t["store_type"] for t in types}
    assert type_names == {"A", "B", "C"}


# ==========================================================
# 3. Demand Forecasting Engine Tests
# ==========================================================
def test_forecast_valid_horizons():
    """Test multi-step forecasting across 1, 4, 8, and 12 week horizons."""
    for h in [1, 4, 8, 12]:
        res = client.post("/api/forecast", json={"store_id": 1, "dept_id": 1, "horizon_weeks": h})
        assert res.status_code == 200
        data = res.json()
        assert data["store_id"] == 1
        assert data["dept_id"] == 1
        assert data["horizon_weeks"] == h
        assert len(data["predictions"]) == h
        assert all(p["weekly_sales"] > 0 for p in data["predictions"])


def test_forecast_invalid_inputs():
    """Verify proper validation errors for invalid store, department, or horizon values."""
    # Invalid horizon > 12
    res_h = client.post("/api/forecast", json={"store_id": 1, "dept_id": 1, "horizon_weeks": 53})
    assert res_h.status_code == 422

    # Unknown store
    res_s = client.post("/api/forecast", json={"store_id": 99, "dept_id": 1, "horizon_weeks": 4})
    assert res_s.status_code in [400, 404, 422]

    # Unknown department
    res_d = client.post("/api/forecast", json={"store_id": 1, "dept_id": 999, "horizon_weeks": 4})
    assert res_d.status_code in [400, 404, 422]


# ==========================================================
# 4. AI Business Assistant & Multi-Tool Routing Tests
# ==========================================================
def test_assistant_sql_analytics_routing():
    """Verify natural language historical question routes to SQL analytics tool."""
    res = client.post("/api/assistant/chat", json={"message": "Which store had the highest total sales?"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["answer"]) > 10
    assert "sql_analytics_tool" in data["tools_used"]
    assert len(data["trace"]) > 0
    assert data["trace"][0]["tool"] == "sql_analytics_tool"


def test_assistant_forecast_routing():
    """Verify forecast question routes to forecasting tool."""
    res = client.post("/api/assistant/chat", json={"message": "Forecast weekly sales for Store 1 Department 1 for 4 weeks."})
    assert res.status_code == 200
    data = res.json()
    assert "forecast_tool" in data["tools_used"]
    assert len(data["trace"]) > 0
    assert data["trace"][0]["tool"] == "forecast_tool"


def test_assistant_policy_retrieval_routing():
    """Verify policy question routes to retrieval tool and includes source citations."""
    res = client.post("/api/assistant/chat", json={"message": "What is the return policy for clearance items?"})
    assert res.status_code == 200
    data = res.json()
    assert "retrieval_tool" in data["tools_used"]
    assert len(data["sources"]) > 0
    assert data["sources"][0]["document"] == "policy_docs.txt"


def test_assistant_inventory_limitation_guardrail():
    """Verify physical inventory inquiries return honest dataset limitation explanation."""
    res = client.post("/api/assistant/chat", json={"message": "What is Store 5's current physical inventory stock on hand?"})
    assert res.status_code == 200
    data = res.json()
    assert "not present in the supplied Walmart sales dataset" in data["answer"] or "inventory" in data["answer"].lower()


# ==========================================================
# 5. Security & SQL Guardrail Tests
# ==========================================================
def test_sql_validator_blocks_ddl_and_dml():
    """Verify SQLSecurityValidator blocks DROP, DELETE, UPDATE, INSERT, ALTER."""
    dangerous_queries = [
        "DROP TABLE fact_sales;",
        "DELETE FROM fact_sales WHERE store_id = 1;",
        "UPDATE dim_store SET store_type = 'Z';",
        "INSERT INTO dim_dept (dept_id) VALUES (999);",
        "ALTER TABLE fact_sales ADD COLUMN secret TEXT;",
        "PRAGMA table_info(fact_sales);",
        "VACUUM;",
        "ATTACH DATABASE 'hack.db' AS hack;"
    ]
    for q in dangerous_queries:
        is_valid, err = SQLSecurityValidator.validate_query(q)
        assert not is_valid, f"Security validator failed to block dangerous query: {q}"


def test_sql_validator_blocks_multistatements():
    """Verify SQLSecurityValidator blocks multi-statement SQL injections."""
    multi_statements = [
        "SELECT * FROM fact_sales; DROP TABLE fact_sales;",
        "SELECT COUNT(*) FROM dim_store; DELETE FROM dim_store;",
        "SELECT 1; VACUUM;"
    ]
    for q in multi_statements:
        is_valid, err = SQLSecurityValidator.validate_query(q)
        assert not is_valid, f"Failed to block multi-statement injection: {q}"


def test_sql_validator_blocks_system_tables():
    """Verify access to sqlite_master and non-whitelisted tables is blocked."""
    sys_queries = [
        "SELECT * FROM sqlite_master;",
        "SELECT name FROM sqlite_master WHERE type='table';",
        "SELECT * FROM sqlite_sequence;"
    ]
    for q in sys_queries:
        is_valid, err = SQLSecurityValidator.validate_query(q)
        assert not is_valid, f"Failed to block access to system table: {q}"


def test_sql_validator_allows_valid_selects():
    """Verify valid analytical SELECT queries pass validation."""
    valid_queries = [
        "SELECT COUNT(*) FROM fact_sales;",
        "SELECT s.store_id, SUM(f.weekly_sales) FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id GROUP BY s.store_id;",
        "WITH top_stores AS (SELECT store_id, SUM(weekly_sales) as s FROM fact_sales GROUP BY store_id) SELECT * FROM top_stores LIMIT 5;"
    ]
    for q in valid_queries:
        is_valid, cleaned = SQLSecurityValidator.validate_query(q)
        assert is_valid, f"Validator incorrectly rejected valid query: {q} (Error: {cleaned})"


# ==========================================================
# 6. Policy Retrieval Relevance Tests
# ==========================================================
def test_retrieval_relevance_threshold():
    """Verify relevant queries return correct policy sections and irrelevant queries return empty/low score."""
    retriever = PolicyRetriever.get_instance()
    
    # Relevant queries
    res_inv = retriever.search("inventory cover target weeks", top_k=1)
    assert len(res_inv) > 0
    assert "INVENTORY" in res_inv[0]["section"]

    res_ret = retriever.search("customer return receipt refund", top_k=1)
    assert len(res_ret) > 0
    assert "RETURNS" in res_ret[0]["section"]

    # Irrelevant nonsense query
    res_irr = retriever.search("quantum teleportation in outer space astrophysics", top_k=1)
    assert len(res_irr) == 0 or res_irr[0]["score"] < 0.1
