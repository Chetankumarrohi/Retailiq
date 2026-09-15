# RetailIQ
**Demand Forecasting and Multi-Tool AI Business Assistant**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LightGBM](https://img.shields.io/badge/Model-LightGBM%20GBDT-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20Star%20Schema-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

---

## 1. Project Overview & Problem Statement

Retail executives and department managers constantly face the classic inventory dilemma:
- **Under-forecasting / Stockouts:** Lead to lost sales and dissatisfied customers.
- **Over-forecasting / Excess Inventory:** Tie up working capital and force aggressive clearance markdowns.
- **Static Dashboards:** Traditional BI dashboards only show historical data; they cannot simulate future sales or answer operational policy questions.

**RetailIQ** solves this by unifying:
1. **Relational Analytics:** SQLite Star Schema (`retailiq.db`) tracking 421,570 fact rows across 45 stores and 81 departments.
2. **Machine Learning Forecaster:** A trained 44-feature LightGBM GBDT regressor for recursive multi-step weekly sales predictions.
3. **Multi-Tool AI Business Assistant:** An intelligent agent combining SQL Analytics, Demand Forecasting, and Policy Document Retrieval (RAG via TF-IDF).
4. **Streamlit Application:** A single, clean, student-friendly web application with zero complex build steps.

---

## 2. System Architecture

```
                      ┌───────────────────────────────────────────────┐
                      │             Streamlit Web App                 │
                      │               (app.py)                        │
                      └───────┬──────────────┬──────────────┬─────────┘
                              │              │              │
             ┌────────────────┘              │              └────────────────┐
             ▼                               ▼                               ▼
  📊 Executive Dashboard           🔮 Demand Forecast              💬 Business Assistant
  - Filter-aware metrics           - Multi-week horizon (1-12w)    - Natural language queries
  - Monthly/Weekly trends          - Historical context plot       - SQL Analytics Tool
  - Store & Dept rankings          - Week-by-week schedule         - Demand Forecast Tool
  - Holiday & Promo lift           - Non-negative constraint       - Policy Retrieval (RAG)
             │                               │                               │
             ▼                               ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│     SQLite Database     │     │  LightGBM Forecaster    │     │   Knowledge Base RAG    │
│      (retailiq.db)      │     │(retailiq_forecaster.pkl)│     │    (policy_docs.txt)    │
│  - fact_sales           │     │  - 44 lag/rolling feats │     │  - TF-IDF Vectorizer    │
│  - dim_store            │     │  - Recursive inference  │     │  - Cosine Similarity    │
│  - dim_dept, dim_date   │     │  - Macro & Promo flags  │     │  - Grounded citations   │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

---

## 3. End-to-End Data Pipeline

### Step 1: Preprocessing & Data Cleaning (`src/data/`)
- **Raw Datasets:** `stores.csv` (45 stores), `features.csv` (temperature, fuel price, CPI, unemployment, markdowns 1-5), `train.csv` (421,570 weekly sales records).
- **Date Alignment:** Standardized transaction dates from 2010-02-05 to 2012-10-26 (143 contiguous weeks).
- **Missing Value Handling:** Unrecorded promotional markdowns imputed to `0.0` (as markdowns only began late 2011).
- **Negative Sales / Customer Returns:** 1,285 negative weekly sales records flagged as legitimate customer returns (`returns_flag = 1`), preserving net sales integrity.
- **Output:** Clean integrated dataset saved at `data/processed/integrated_sales.parquet`.

### Step 2: Star Schema Relational Database (`src/database/`)
- Relational SQLite database built at `retailiq.db` with indexed foreign keys:
  - `fact_sales`: 421,570 transaction rows.
  - `dim_store`: Store type (A, B, C), physical size (sq ft), active date span.
  - `dim_dept`: 81 unique department identifiers.
  - `dim_date`: Year, quarter, month, ISO week of year, holiday flags.

### Step 3: Feature Engineering (`src/features/`)
Generates 44 predictive features:
- **Lags:** 1-week, 2-week, 4-week, 8-week, 12-week, 52-week historical sales.
- **Rolling Statistics:** 4-week, 8-week, 13-week, 26-week rolling mean, min, max, std.
- **Calendar Signals:** ISO week of year, month, quarter, month start/end flags.
- **Macroeconomic & Promo:** Fuel price, CPI, unemployment, temperature, total markdowns.

---

## 4. Machine Learning & Model Benchmark

We evaluated multiple forecasting paradigms using 3-fold forward-chaining time-series cross-validation:

| Model Architecture | Test MAE ($) | Test RMSE ($) | WAPE (%) | R² Score |
|---|:---:|:---:|:---:|:---:|
| **LightGBM Regressor (Production)** | **1,385.12** | **3,520.44** | **8.67%** | **0.972** |
| PyTorch LSTM (Sequence Model) | 2,140.85 | 4,890.12 | 13.40% | 0.941 |
| 4-Week Moving Average (Baseline) | 2,980.20 | 6,120.30 | 18.65% | 0.884 |
| 52-Week Seasonal Naive (Baseline) | 3,450.10 | 7,210.50 | 21.30% | 0.840 |

### Why LightGBM was Selected:
1. **Tabular & Exogenous Superiority:** LightGBM excels at non-linear interactions between promotional markdowns, store types, economic indicators, and historical lags.
2. **Speed & Efficiency:** Instant inference for multi-step recursive forecasting inside interactive applications without GPU dependencies.
3. **Saved Artifact:** Production model serialized at `models/trained/retailiq_forecaster.pkl`.

> **Note on Evaluation Metrics:** Because retail sales contain customer returns ($ \le 0 $), standard percentage metrics like MAPE can divide by near-zero values. We report **MAE**, **RMSE**, and **WAPE** (Weighted Absolute Percentage Error) as the robust, mathematically sound benchmarks.

---

## 5. Multi-Tool Business Assistant

The assistant operates as a sandboxed agent with 3 distinct tools:

1. **SQL Analytics Tool:** Executes parameterized, read-only analytical queries on the SQLite star schema. Protected with strict security guardrails blocking DDL/DML, multi-statements, and metadata tables.
2. **Demand Forecast Tool:** Calls `retailiq_forecaster.pkl` to project 1–12 week forward-looking sales for any valid store and department.
3. **Policy Retrieval Tool (RAG):** Performs TF-IDF cosine-similarity search over internal standard operating procedures (`data/knowledge_base/policy_docs.txt`), retrieving relevant clauses with citations.

### Multi-Tool Orchestration Examples:
- **Query:** *"Which department performs best in Store 20 and forecast it for the next 4 weeks?"*
  - **Step 1 (SQL):** Identifies top department in Store 20 (Department 92).
  - **Step 2 (Forecast):** Generates 4-week LightGBM forecast for Store 20, Dept 92.
  - **Combined Result:** Delivers unified analytical summary with historical context and projections.
- **Query:** *"Which store has the highest sales and what is our reorder policy?"*
  - **Step 1 (SQL):** Finds Store 20 leads chain sales.
  - **Step 2 (RAG):** Retrieves Inventory Policy (Section 1) citing reorder thresholds (1.5 weeks).

### Guardrails & Limitations:
- **Physical Inventory Counts:** Physical shelf stock counts are not part of transaction datasets; the assistant clearly disclaims this limitation and quotes target policy rules.
- **Scope Guardrail:** Unrelated questions (celebrities, politics, code generation) are politely rejected with clear domain guidance.

---

## 6. How to Run the Application

### Prerequisites
- Python 3.10 or 3.11 installed on your system.

### Quick Setup

#### 1. Clone & Navigate to Repository
```bash
git clone https://github.com/Chetankumarrohi/Retailiq.git
cd Retailiq
```

#### 2. Create and Activate Virtual Environment
**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (Command Prompt / PowerShell):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Launch Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 7. Project Structure

```
RetailIq/
├── app.py                     # Main Streamlit application entry point
├── requirements.txt           # Clean dependencies list
├── retailiq.db                # SQLite Star Schema database (421,570 fact rows)
│
├── src/                       # Core Python modules
│   ├── data/                  # Data loading and preprocessing pipelines
│   │   ├── loader.py
│   │   └── cleaner.py
│   ├── database/              # SQLite builder and filter-aware analytics
│   │   ├── build_database.py
│   │   └── analytics.py
│   ├── features/              # Lag and rolling feature engineering
│   │   └── forecasting_features.py
│   ├── forecasting/           # Training routines, evaluation, and predictor
│   │   ├── baseline.py
│   │   ├── train_tree.py
│   │   ├── train_sequence.py
│   │   ├── evaluate.py
│   │   └── predictor.py
│   └── assistant/             # AI Multi-tool assistant & policy RAG
│       ├── retrieval.py
│       └── agent.py
│
├── data/
│   ├── raw/                   # stores.csv, features.csv, train.csv
│   ├── processed/             # integrated_sales.parquet
│   └── knowledge_base/        # policy_docs.txt
│
├── models/trained/            # Serialized LightGBM forecaster artifact
├── notebooks/                 # 8 sequential academic Jupyter notebooks
└── tests/                     # Unit and integration test suite
```
