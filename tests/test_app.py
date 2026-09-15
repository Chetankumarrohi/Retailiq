"""
Test suite for RetailIQ Streamlit Academic Application.
Tests database analytics, forecasting inference, policy RAG, assistant orchestration, and UI execution.
"""
import pytest
from src.database import AnalyticsService, SQLSecurityValidator
from src.forecasting.predictor import RetailForecasterPredictor
from src.assistant import PolicyRetriever
from src.assistant import RetailIQAssistant
from streamlit.testing.v1 import AppTest


# ==========================================================
# 1. Database & SQL Security Tests
# ==========================================================
def test_database_summary():
    svc = AnalyticsService()
    summary = svc.get_summary()
    assert summary["total_stores"] == 45
    assert summary["total_departments"] == 81
    assert summary["total_sales"] > 6e9


def test_database_filtering():
    svc = AnalyticsService()
    s1_sum = svc.get_summary(store_id=1)
    assert s1_sum["total_stores"] == 1
    assert s1_sum["total_sales"] < 3e8

    s20_d3 = svc.get_summary(store_id=20, dept_id=3)
    assert s20_d3["total_stores"] == 1
    assert s20_d3["total_departments"] == 1
    assert s20_d3["total_sales"] > 2e6


def test_sql_security_guardrails():
    # Dangerous SQL
    assert not SQLSecurityValidator.validate_query("DROP TABLE fact_sales;")[0]
    assert not SQLSecurityValidator.validate_query("DELETE FROM dim_store;")[0]
    assert not SQLSecurityValidator.validate_query("INSERT INTO fact_sales VALUES (1, 1, 1, 100);")[0]
    assert not SQLSecurityValidator.validate_query("SELECT * FROM sqlite_master;")[0]
    assert not SQLSecurityValidator.validate_query("SELECT * FROM fact_sales; SELECT * FROM dim_store;")[0]

    # Safe SQL
    assert SQLSecurityValidator.validate_query("SELECT store_id, SUM(weekly_sales) FROM fact_sales GROUP BY store_id;")[0]


# ==========================================================
# 2. Demand Forecast Predictor Tests
# ==========================================================
def test_forecasting_predictor():
    predictor = RetailForecasterPredictor()
    res = predictor.predict(store_id=20, dept_id=3, horizon_weeks=4)
    assert res["store_id"] == 20
    assert res["dept_id"] == 3
    assert len(res["predictions"]) == 4
    for p in res["predictions"]:
        assert p["weekly_sales"] >= 0.0


def test_forecasting_invalid_store_dept():
    predictor = RetailForecasterPredictor()
    with pytest.raises(ValueError):
        predictor.predict(store_id=999, dept_id=999, horizon_weeks=4)


# ==========================================================
# 3. Policy Retrieval (RAG) Tests
# ==========================================================
def test_policy_retrieval():
    retriever = PolicyRetriever.get_instance()
    res = retriever.search("What is the customer return policy?", top_k=1)
    assert len(res) > 0
    assert "RETURNS POLICY" in res[0]["section"]

    res_inv = retriever.search("reorder inventory policy target cover", top_k=1)
    assert len(res_inv) > 0
    assert "INVENTORY POLICY" in res_inv[0]["section"]


# ==========================================================
# 4. Multi-Tool Assistant Tests
# ==========================================================
def test_assistant_sql_routing():
    agent = RetailIQAssistant()
    res = agent.ask("Which store has the highest sales?")
    assert "SQL Analytics Tool" in res["tools_used"]
    assert "Store 20" in res["answer"]


def test_assistant_forecast_routing():
    agent = RetailIQAssistant()
    res = agent.ask("Forecast Store 20 Department 3 for 4 weeks")
    assert "Demand Forecast Tool" in res["tools_used"]
    assert "LightGBM" in res["answer"]


def test_assistant_policy_routing():
    agent = RetailIQAssistant()
    res = agent.ask("What is our return policy?")
    assert "Policy Retrieval Tool" in res["tools_used"]
    assert "RETURNS POLICY" in res["answer"]


def test_assistant_multi_tool():
    agent = RetailIQAssistant()
    res = agent.ask("Which department performs best in Store 20 and forecast it for the next 4 weeks?")
    assert "SQL Analytics Tool" in res["tools_used"]
    assert "Demand Forecast Tool" in res["tools_used"]


def test_assistant_out_of_scope():
    agent = RetailIQAssistant()
    res = agent.ask("Who is the Prime Minister of Canada?")
    assert "outside RetailIQ's scope" in res["answer"]


# ==========================================================
# 5. Streamlit AppTest Execution Test
# ==========================================================
def test_streamlit_app_headless():
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    assert len(at.tabs) == 3
