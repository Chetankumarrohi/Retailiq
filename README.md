# RetailIQ
**Demand Forecasting and Multi-Tool AI Business Assistant**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![LightGBM](https://img.shields.io/badge/Model-LightGBM%20GBDT-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20Star%20Schema-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-20%20Passed%20(100%25)-success.svg)](file:///Users/chetankumarrohilla/Desktop/%20RetailIq/reports/test_results.md)

---

## 1. Problem Statement

Retail store managers and supply chain directors face a high-stakes operational dilemma:
- **Stockouts** lead to missed revenue opportunities and degraded customer loyalty.
- **Overstocking** increases warehouse holding costs and forces aggressive promotional markdown write-offs.
- **Static BI Dashboards** only summarize historical transactions; they cannot project future multi-week demand or interpret internal operational policies.

---

## 2. Solution: RetailIQ

RetailIQ is an enterprise-grade full-stack demand intelligence platform that unites:
1. **Relational Data Warehousing:** A SQLite Star Schema (`retailiq.db`) tracking 421,570 fact rows across 45 stores and 81 departments.
2. **Machine Learning Forecaster:** A trained 44-feature LightGBM GBDT regressor providing multi-horizon recursive weekly sales predictions.
3. **Autonomous AI Business Assistant:** A Planner-Executor agent with sandboxed SQL querying, demand forecasting, and grounded policy document retrieval.
4. **Modern Web Application:** An executive React 18 + Vite SPA offering dark-mode dashboards, interactive forecast explorations, and conversational AI traces.

---

## 3. Key Features

- **Executive Dashboard:** 7 high-level KPI cards ($6.74B Total Sales, $15,981 Average Weekly Sales, 45 Stores, 81 Departments), monthly/weekly sales trends, top store and department rankings, holiday impact comparisons, and store type distributions.
- **Demand Forecast Explorer:** Store and department selectors, horizon slider (1–12 weeks), Recharts line chart with historical baseline reference and "Forecast Starts" markers, and week-by-week forecast tables.
- **AI Business Assistant:** Markdown conversational chat, one-click prompt chips, visible execution traces in "How RetailIQ Answered", and grounded policy citations.
- **Data Insights & Warehouse:** Top 10 feature importance breakdown, 44-feature taxonomy, SQLite star schema table inspector, and 45-store network directory.
- **SQL Security Guardrails:** Dual-layer protection (application token whitelist blocking DDL/DML/multi-statements + SQLite `?mode=ro` read-only connection).

---

## 4. System Architecture

```mermaid
graph TD
    User([👤 Retail Executive / Business User])

    subgraph Presentation_Layer ["Presentation Layer (React 18 + Vite SPA - Port 5173)"]
        Dash[Executive Dashboard<br/><i>7 KPIs, Trends, Rankings, Lift</i>]
        FC[Demand Forecast Explorer<br/><i>Interactive Horizon, Baseline Viz</i>]
        Assist[AI Business Assistant<br/><i>Chat, Tool Traces, Policy Citations</i>]
        Insight[Data Insights & Architecture<br/><i>Feature Importance, Schema, Stores</i>]
    end

    subgraph API_Gateway ["Application Server (FastAPI + Python 3.11 - Port 8000)"]
        Router{REST API Gateway<br/>/api/*}
        AnalyticsSvc[Analytics Service]
        ForecastSvc[Forecast Service]
        AgentSvc[Assistant Service]
        Guard[SQL Security Validator<br/><i>Read-Only AST & Whitelist</i>]
    end

    subgraph Storage_and_ML ["Data & Model Engines"]
        DB[(SQLite Star Schema<br/>retailiq.db<br/><i>421,570 fact rows</i>)]
        LGBM[LightGBM Forecaster<br/><i>44 Features, Lags, Rolling Stats</i>]
        KB[TF-IDF Knowledge Index<br/><i>policy_docs.txt (11 Sections)</i>]
    end

    User -->|Port 5173| Dash
    User -->|Port 5173| FC
    User -->|Port 5173| Assist
    User -->|Port 5173| Insight

    Dash -->|/api/dashboard/*| Router
    FC -->|/api/forecast| Router
    Assist -->|/api/assistant/chat| Router
    Insight -->|/api/stores| Router

    Router --> AnalyticsSvc
    Router --> ForecastSvc
    Router --> AgentSvc

    AnalyticsSvc -->|Read-Only URI| DB
    ForecastSvc -->|Inference Pipeline| LGBM
    AgentSvc -->|Planner Loop| Guard
    Guard -->|Safe SELECT| DB
    AgentSvc -->|Multi-Step Roll| ForecastSvc
    AgentSvc -->|Cosine Similarity| KB
```

---

## 5. Dataset & Star Schema

- **Source:** Historical multi-store retail dataset spanning **2010-02-05 to 2012-10-26** (143 contiguous weeks).
- **Volume:** **421,570 observations** across **45 stores** and **81 departments**.
- **Customer Returns:** 1,285 negative weekly sales transactions preserved as legitimate return volumes (`returns_flag = 1`).
- **Star Schema Design (`retailiq.db`):**
  - `fact_sales`: Transactional measurements (`weekly_sales`, `markdown1-5`, `temperature`, `fuel_price`, `cpi`, `unemployment`).
  - `dim_store`: Store type (A/B/C) and square footage footprint.
  - `dim_dept`: Department merchandise categories.
  - `dim_date`: Conformed 4-5-4 retail calendar with holiday event tags.

---

## 6. Demand Forecasting Engine

- **Model:** LightGBM GBDT Regressor (`LGBMRegressor`, 400 estimators, learning rate 0.04, num_leaves 63).
- **Feature Engineering Pipeline (44 Exact Features):**
  - **7 Autoregressive Lags:** `lag_1`, `lag_2`, `lag_4`, `lag_8`, `lag_13`, `lag_26`, `lag_52`
  - **14 Rolling Window Stats:** 4, 8, and 13-week moving means, standard deviations, min, max
  - **2 Momentum Ratios:** `sales_to_roll_mean_4`, `sales_to_roll_mean_13`
  - **8 Calendar Indicators:** `year`, `quarter`, `month`, `week_of_year`, `day_of_year`, `is_holiday`, `is_month_start`, `is_month_end`
  - **7 Markdown Indicators:** `markdown1` through `markdown5`, `has_markdown`, `total_markdown`
  - **4 Macroeconomic Drivers:** `temperature`, `fuel_price`, `cpi`, `unemployment`
  - **2 Store Embeddings:** `store_type_encoded`, `store_size`
- **Validation Results (Forward Out-of-Time Holdout Split):**
  - **Weighted MAE (WMAE):** **$1,250.03**
  - **MAE:** **$1,213.40**
  - **RMSE:** **$2,496.47**
  - **MAPE:** **15.8%**

---

## 7. Multi-Tool AI Assistant

The autonomous Assistant provides natural language reasoning via three sandboxed tools:
1. `sql_analytics_tool`: Safe, read-only SQL queries against the star schema for historical aggregations, store rankings, and YoY comparisons.
2. `forecast_tool`: Real-time demand forecasting for any Store/Department combination across 1 to 12 forward weeks.
3. `retrieval_tool`: TF-IDF cosine similarity search across internal policy documents (`policy_docs.txt`) with exact section citations.

---

## 8. Project Structure

```
RetailIq/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── agent/                 # Planner-Executor agent & tool definitions
│   │   │   ├── planner.py         # Multi-tool agent planner
│   │   │   ├── tools.py           # SQL, Forecast, and Retrieval tools
│   │   │   └── retrieval.py       # TF-IDF policy search index
│   │   ├── api/                   # REST API route handlers
│   │   ├── core/                  # Security validator & environment config
│   │   ├── database/              # SQLite connection manager
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Analytics, forecasting, and assistant services
│   │   └── main.py                # FastAPI entry point
│   ├── run_server.py              # Backend startup script
│   └── requirements.txt           # Python backend dependencies
├── frontend/                       # React 18 + Vite SPA
│   ├── src/
│   │   ├── api/client.js          # Centralized API fetch client
│   │   ├── components/Sidebar.jsx # Navigation sidebar
│   │   ├── pages/                 # 4 Core Pages (Dashboard, Forecast, Assistant, Insights)
│   │   ├── App.jsx                # Root router
│   │   └── index.css              # Premium dark theme design system
│   ├── package.json               # Frontend dependencies
│   └── vite.config.js             # Vite config with /api proxy
├── data/                           # Processed Parquet datasets & knowledge base
│   └── knowledge_base/
│       └── policy_docs.txt        # Synthetic demonstration policy documentation
├── docs/                           # Architecture, demo script, viva QA, and limitations
├── models/                         # Trained model artifacts & metadata
│   ├── trained/retailiq_forecaster.pkl
│   └── metadata/model_metadata.json
├── notebooks/                      # 8 Jupyter research & submission notebooks
├── reports/                        # Preflight audits, test results, and export summaries
├── sql/                            # Star schema DDL and 13 analytical SQL queries
├── tests/                          # Automated backend & security test suite
├── retailiq.db                     # SQLite Analytical Database
└── README.md                       # Main documentation
```

---

## 9. Setup & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# From project root:
pip install -r backend/requirements.txt
python backend/run_server.py
```
*Backend runs on `http://localhost:8000` with interactive Swagger API docs at `http://localhost:8000/docs`.*

### 2. Frontend Setup
```bash
# In a second terminal from project root:
cd frontend
npm install
npm run dev
```
*Frontend application opens at `http://localhost:5173`.*

---

## 10. Automated Tests

Execute the comprehensive 20-test automated suite:
```bash
PYTHONPATH="$(pwd)" pytest tests/test_backend.py -v
```
*Results: 20 Passed / 0 Failed (100% pass rate).*

---

## 11. Known Limitations

- **Physical Inventory Counts:** The transactional dataset contains financial sales but lacks warehouse physical unit counts.
- **Product Text Descriptions:** Merchandise lines are identified numerically by department ID without natural language product titles.
- **Synthetic Policy Documentation:** `policy_docs.txt` is synthetic documentation created to demonstrate grounded multi-tool retrieval.

---

## 12. Authors & Academic Submission

Developed for the **RetailIQ Demand Forecasting and Multi-Tool Business Assistant** Capstone Project.
