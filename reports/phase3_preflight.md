# RetailIQ Phase 3 Preflight Audit Report

**Audit Date:** 2026-09-15  
**Auditor:** RetailIQ Quality & Reliability System  
**Objective:** Complete pre-hardening verification of backend, frontend, database, ML forecaster, autonomous agent, and security systems.

---

## 1. Verified Database Metrics (`retailiq.db`)

Direct calculation against the SQLite star schema database yielded exact values:

| Metric | Verified Value | Verification Query / Method | Status |
| :--- | :--- | :--- | :--- |
| **Total Observations (Rows)** | `421,570` | `SELECT COUNT(*) FROM fact_sales` | ✅ PASS |
| **Total Sales** | `$6,737,218,987.11` (~$6.74B) | `SELECT SUM(weekly_sales) FROM fact_sales` | ✅ PASS |
| **Average Weekly Sales** | `$15,981.26` | `SELECT AVG(weekly_sales) FROM fact_sales` | ✅ PASS |
| **Distinct Stores** | `45` | `SELECT COUNT(DISTINCT store_id) FROM fact_sales` | ✅ PASS |
| **Distinct Departments** | `81` | `SELECT COUNT(DISTINCT dept_id) FROM fact_sales` | ✅ PASS |
| **Date Range** | `2010-02-05` to `2012-10-26` | 143 contiguous weekly observations | ✅ PASS |
| **Top Store** | **Store 20** (`$301,397,792.46`) | Group by `store_id`, ordered by sum | ✅ PASS |
| **Top Department** | **Department 92** (`$483,943,341.87`) | Group by `dept_id`, ordered by sum | ✅ PASS |
| **Normal Week Avg Sales** | `$15,901.45` | 391,909 observations (`is_holiday = 0`) | ✅ PASS |
| **Holiday Week Avg Sales** | `$17,035.82` | 29,661 observations (`is_holiday = 1`) | ✅ PASS |
| **Holiday Sales Lift** | `+7.13%` | `(17035.82 - 15901.45) / 15901.45` | ✅ PASS |
| **Non-Promo Avg Sales** | `$15,871.52` | 270,138 observations | ✅ PASS |
| **Promo Avg Sales** | `$16,177.02` | 151,432 observations (MarkDown1-5 active) | ✅ PASS |
| **Promo Sales Lift** | `+1.92%` | `(16177.02 - 15871.52) / 15871.52` | ✅ PASS |

### Store Type Breakdown
- **Type A (Supercenters, >150k sqft):** 22 stores | `$4,331,014,722.75` total sales (64.3%) | Avg: `$20,099.57`
- **Type B (Standard Format, 100k–150k sqft):** 17 stores | `$2,000,700,736.82` total sales (29.7%) | Avg: `$12,237.08`
- **Type C (Small Format, <100k sqft):** 6 stores | `$405,503,527.54` total sales (6.0%) | Avg: `$9,519.53`

---

## 2. Model & Forecasting Verification

- **Artifact Path:** `models/trained/retailiq_forecaster.pkl`
- **Metadata Path:** `models/metadata/model_metadata.json`
- **Model Type:** LightGBM GBDT Regressor (`LGBMRegressor`)
- **Number of Input Features:** Exactly **44 features**
  - **7 Lag Steps:** `lag_1`, `lag_2`, `lag_4`, `lag_8`, `lag_13`, `lag_26`, `lag_52`
  - **14 Rolling Statistics:** 4, 8, and 13-week rolling mean, std, min, max
  - **2 Momentum Ratios:** `sales_to_roll_mean_4`, `sales_to_roll_mean_13`
  - **8 Calendar/Temporal Features:** `year`, `quarter`, `month`, `week_of_year`, `day_of_year`, `is_holiday`, `is_month_start`, `is_month_end`
  - **7 Markdown Features:** `markdown1` through `markdown5`, `has_markdown`, `total_markdown`
  - **4 Macroeconomic Features:** `temperature`, `fuel_price`, `cpi`, `unemployment`
  - **2 Entity Embeddings:** `store_type_encoded`, `store_size`
- **Evaluation Metrics on Holdout Test Set:**
  - **RMSE:** `$2,496.47`
  - **MAE:** `$1,213.40`
  - **WMAE (Weighted MAE):** `$1,250.03`
  - **MAPE:** `15.8%`

---

## 3. Security & Safety Audit

| Layer | Component | Test Scenario | Expected Behavior | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SQL Sandboxing** | `SQLSecurityValidator` | DDL / DML (`DROP`, `INSERT`, `UPDATE`, `DELETE`) | Immediate rejection | ✅ VERIFIED |
| **SQL Sandboxing** | `SQLSecurityValidator` | Multi-statement injection (`SELECT 1; DROP TABLE fact_sales;`) | Rejection on `;` | ✅ VERIFIED |
| **SQL Sandboxing** | `SQLSecurityValidator` | System tables (`sqlite_master`, `sqlite_sequence`) | Rejection on non-whitelisted tables | ✅ VERIFIED |
| **Engine Write-Block** | `get_db_connection` | Read-only SQLite URI (`mode=ro`) | OS/C-level write block | ✅ VERIFIED |
| **Secrets & Keys** | Secret Scanner | Git history & source tree scan for `sk-...` / API keys | Zero committed secrets | ✅ VERIFIED |
| **Path Portability** | Path Scanner | Hard-coded absolute developer paths | Zero hard-coded paths (`pathlib.Path` used) | ✅ VERIFIED |

---

## 4. Application Status

- **FastAPI Backend:** Verified running on `http://localhost:8000` with automated OpenAPI schemas at `/docs`.
- **React + Vite Frontend:** Verified running on `http://localhost:5173` with proxy configuration to FastAPI.
- **Knowledge Base:** Verified `data/knowledge_base/policy_docs.txt` chunked into 11 sections with TF-IDF indexing.
