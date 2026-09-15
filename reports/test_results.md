# RetailIQ Automated Backend Test Suite Report

**Test Suite Execution Date:** 2026-09-15  
**Framework:** Pytest 7.4.0 with FastAPI `TestClient`  
**Execution Time:** 3.27s  
**Results:** **20 Passed / 0 Failed (100% Pass Rate)**

---

## Detailed Test Case Breakdown

| Test ID | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| `test_health_check` | Health | Verifies `/api/health` connectivity, SQLite row count (421,570), and stores/dept counts. | ✅ PASS |
| `test_get_stores` | Metadata | Verifies `/api/stores` returns 45 stores with types and physical footprint sizes. | ✅ PASS |
| `test_get_departments` | Metadata | Verifies `/api/departments` returns 81 valid merchandise department IDs. | ✅ PASS |
| `test_dashboard_summary` | Analytics | Verifies `/api/dashboard/summary` returns $6.74B revenue and $15,981 avg weekly sales. | ✅ PASS |
| `test_sales_trend_monthly_and_weekly` | Analytics | Verifies time-series aggregation for both monthly (33 periods) and weekly (143 periods). | ✅ PASS |
| `test_sales_trend_filtered` | Analytics | Verifies parameterized store and department filtering against the database. | ✅ PASS |
| `test_store_and_department_rankings` | Analytics | Verifies leaderboards: Store 20 ($301.4M) and Department 92 ($483.9M) top rankings. | ✅ PASS |
| `test_holiday_and_promotion_analytics` | Analytics | Verifies +7.13% holiday lift and +1.92% promotion markdown lift calculations. | ✅ PASS |
| `test_store_types_distribution` | Analytics | Verifies Type A (22 stores), Type B (17 stores), Type C (6 stores) categorical breakdown. | ✅ PASS |
| `test_forecast_valid_horizons` | Forecasting | Tests recursive multi-step forecasting across 1, 4, 8, and 12-week horizons. | ✅ PASS |
| `test_forecast_invalid_inputs` | Forecasting | Verifies 422/400 validation rejections for horizon > 12, unknown store, or unknown dept. | ✅ PASS |
| `test_assistant_sql_analytics_routing` | Agent | Verifies historical questions route to `sql_analytics_tool` with generated visible trace. | ✅ PASS |
| `test_assistant_forecast_routing` | Agent | Verifies demand questions route to `forecast_tool` with structured multi-week predictions. | ✅ PASS |
| `test_assistant_policy_retrieval_routing` | Agent | Verifies policy inquiries search `policy_docs.txt` and return cited section snippets. | ✅ PASS |
| `test_assistant_inventory_limitation_guardrail` | Agent | Verifies inquiries for physical stock levels return honest dataset limitation explanations. | ✅ PASS |
| `test_sql_validator_blocks_ddl_and_dml` | Security | Verifies immediate rejection of `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `PRAGMA`. | ✅ PASS |
| `test_sql_validator_blocks_multistatements` | Security | Verifies injection attacks using semicolons (`SELECT 1; DROP TABLE...`) are blocked. | ✅ PASS |
| `test_sql_validator_blocks_system_tables` | Security | Verifies blocking of `sqlite_master`, `sqlite_sequence`, or arbitrary non-star schema tables. | ✅ PASS |
| `test_sql_validator_allows_valid_selects` | Security | Verifies legitimate analytical `SELECT` and `WITH ... SELECT` queries pass without false positives. | ✅ PASS |
| `test_retrieval_relevance_threshold` | Retrieval | Verifies relevant queries return correct policy chunks while nonsense queries return low scores. | ✅ PASS |

---

## Security Verification Summary

1. **SQL Injection Resistance:** Read-only AST/regex validator blocks DDL/DML, multi-statement injection, and unwhitelisted tables.
2. **Database Engine Sandbox:** SQLite opened with `?mode=ro` URI flag ensuring operating system-level write prevention.
3. **Secret Hygiene:** Scanned entire repository with zero committed API keys, tokens, or credentials.
