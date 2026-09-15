# RetailIQ: Reference Implementation Review & Technical Audit

## 1. Executive Summary

This document provides a rigorous architectural and technical review of the supplied reference implementation files for the **RetailIQ** demand forecasting platform and multi-tool business assistant.

The reference implementation demonstrates basic functionality across data loading, SQLite database creation, tree and sequence forecasting, and a Streamlit-based UI with Claude tool calling. However, it contains several critical statistical, data handling, and architectural issues that must be redesigned for a production-grade enterprise system.

---

## 2. Detailed Review of Supplied Reference Files

### 2.1 `app.py` (Streamlit Frontend Reference)
- **Role:** Monolithic user interface with three tabs: *Executive Dashboard*, *Forecast Explorer*, and *Business Assistant*.
- **Strengths:** 
  - Clear user journey with three high-value business views.
  - Good visualization choices (Plotly time-series, bar rankings, promo comparisons).
- **Weaknesses & Technical Debt:**
  - **Tightly Coupled Architecture:** Executes raw SQL queries directly inside UI rendering code, connects to SQLite synchronously on every rerun, and imports agent/forecasting code directly in the view layer.
  - **No API Layer:** Lacks an independent REST backend (FastAPI) to serve frontend clients.
- **Decision:**
  - **Conceptual Reuse:** Retain the three-tab concept (*Executive Dashboard*, *Forecast Explorer*, *Business Assistant*) and KPIs for the future frontend.
  - **Phase 1 Action:** Do **not** build the frontend or FastAPI endpoints now. Abstract SQL queries into structured database service functions and document the REST API contracts for Phase 2.

---

### 2.2 `build_db.py` (Database Builder Reference)
- **Role:** Reads CSVs, applies cleaning, creates a SQLite star schema (`fact_sales`, `dim_store`, `dim_dept`, `dim_date`).
- **Strengths:**
  - Establishes a standard star schema suitable for analytical SQL queries.
  - Generates integer `date_id` (YYYYMMDD) for efficient indexing.
- **Critical Flaws & Incorrect Assumptions:**
  - **Data Destruction / Clipping:** Line 18 executes `train["Weekly_Sales_Clean"] = train["Weekly_Sales"].clip(lower=0)` and writes this clipped value as `weekly_sales`. This improperly erases legitimate net customer return transactions.
  - **Lack of Robust Error Handling & Logging:** Hardcoded file paths and silent forward-fills without validation.
- **Decision:**
  - **Phase 1 Action:** Complete redesign in `src/data/cleaner.py` and `src/database/build_database.py`. Preserve true negative sales as net returns, create `returns_flag = (weekly_sales < 0)`, and construct a fully indexed SQLite database with DDL definitions in `sql/schema.sql`.

---

### 2.3 `train_sequence_model.py` (Sequence Model Reference)
- **Role:** PyTorch LSTM implementation predicting next-week sales from a 12-week lookback window, testing a department category feature.
- **Strengths:**
  - Formulates sequence forecasting cleanly (12 historical steps -> 1 future step).
- **Critical Flaws & Incorrect Assumptions:**
  - **Invalid Time-Series Validation:** Uses a global 80/20 array split across mixed store-department pairs (`split = int(len(X) * 0.8)`). Because sequences are concatenated across pairs, later date sequences from early pairs are in the train set while early date sequences from later pairs are in the test set, creating chronological data leakage.
  - **Fabricated Category Proxy:** Creates `dept_category` by dividing `dept_id` into 5 arbitrary numerical bins and claims it acts as a stand-in for product description text.
- **Decision:**
  - **Phase 1 Action:** Refactor in `src/forecasting/train_sequence.py`. Implement strict date-cutoff splitting ensuring all validation sequences occur strictly after the training cutoff date. Explicitly document that the Walmart dataset contains no product text, avoiding any false claims of text-derived category NLP features.

---

### 2.4 `agent.py` (AI Assistant & Tool Execution Reference)
- **Role:** Planner-executor assistant using Claude's tool-use API to invoke `sql_tool`, `forecast_tool`, and `retrieval_tool`.
- **Strengths:**
  - Clean separation into three domain tools (SQL, Forecasting, Document Retrieval).
  - Explicit system prompt preventing fabricated inventory cover calculations when inventory tables are absent.
- **Weaknesses:**
  - `forecast_tool` returns unformatted plain text strings rather than structured data structures required by modern API consumers.
  - `retrieval_tool` relies on naive word set intersection without semantic ranking or chunk boundary management.
- **Decision:**
  - **Phase 1 Action:** Build a production-grade structured `predictor.py` that outputs JSON-serializable structured dictionaries. Preserve `policy_docs.txt` in `data/knowledge_base/` and formally document the Phase 2 agent tool contract in `docs/phase2_api_contract.md`.
  - **Phase 2 Action:** Implement the complete LLM agent, FastAPI endpoints, and semantic retriever.

---

### 2.5 `queries.sql` (Analytical SQL Queries)
- **Role:** Analytical queries testing aggregations, window functions, YoY growth, running totals, and promotional lifts.
- **Strengths:**
  - Modern SQL using Common Table Expressions (CTEs) and Window Functions (`LAG`, `RANK`, `SUM() OVER`).
- **Phase 1 Action:**
  - Expand into `sql/analytics_queries.sql` covering all 13 core analytical scenarios with formal testing against `retailiq.db`.

---

### 2.6 `policy_docs.txt` (Knowledge Base)
- **Role:** Internal documentation for inventory policy, markdown rules, supplier terms, returns policy, and SOPs.
- **Assessment:**
  - High quality synthetic demonstration policy document.
  - Formally accounts for negative weekly sales (Section 4: customer returns exceeding sales).
- **Phase 1 Action:**
  - Preserved in `data/knowledge_base/policy_docs.txt` and documented for Phase 2 retrieval integration.

---

## 3. Architecture Comparison Matrix

| Component | Supplied Reference Implementation | RetailIQ Phase 1 Target | RetailIQ Phase 2 Target |
| :--- | :--- | :--- | :--- |
| **Data Cleaning** | In-script, destructive negative clipping | Modular `src/data/cleaner.py`, preserves true sales, flags returns | Incremental batch ingestion pipeline |
| **Database** | Ad-hoc SQLite script | Star schema DDL in `sql/schema.sql`, indexed `retailiq.db` | Production SQLite / PostgreSQL with SQLAlchemy |
| **Feature Engineering** | Ad-hoc inside training script | Modular `src/features/forecasting_features.py` with zero leakage | Real-time feature store / caching |
| **Validation Strategy** | Global 80/20 index split (leakage prone) | Forward-chaining expanding window CV + strict date-based holdout | Automated backtesting & drift monitoring |
| **Predictor Output** | Plain text string | Structured Python dict / JSON-ready schema in `predictor.py` | FastAPI endpoint `/api/forecast` |
| **UI & API** | Monolithic Streamlit app | Independent business logic and API contracts | React/Vite UI + FastAPI backend |

---

## 4. Phase 1 vs Phase 2 Scope Demarcation

### Phase 1 Scope (Current):
1. Raw data audit and pipeline creation (`loader.py`, `cleaner.py`, `pipeline.py`).
2. SQLite star schema database generation (`retailiq.db`) with SQL test suite.
3. Leakage-safe feature engineering (lags, rolling stats, promotional/calendar features).
4. Baselines (Naive, Moving Avg, Seasonal) + LightGBM + PyTorch LSTM training and forward-chaining evaluation.
5. Production inference predictor (`src/forecasting/predictor.py`) with multi-step recursive forecasting.
6. Presentation-quality Jupyter notebooks (`01_data_understanding.ipynb` to `08_model_comparison.ipynb`).
7. Formal Phase 2 API contract (`docs/phase2_api_contract.md`).

### Phase 2 Scope (Future):
1. FastAPI backend services and REST endpoints.
2. React + Vite dashboard frontend (Executive Dashboard, Forecast Explorer, Assistant).
3. LangChain / Claude / OpenAI AI Assistant planner with tool execution (`sql_tool`, `forecast_tool`, `retrieval_tool`).
