# RetailIQ: Phase 1 Summary & Technical Foundation Report

## 1. Executive Overview

This report provides the formal technical summary for **Phase 1 (Data + Database + Forecasting)** of **RetailIQ: Demand Forecasting and Multi-Tool Business Assistant**.

All deliverables for Phase 1 are fully implemented, verified, and packaged into production-ready modular Python artifacts, an analytical SQLite star schema database (`retailiq.db`), forward-validated ML/DL forecasting models, and interactive Jupyter notebooks.

---

## 2. Technical Audit & Architecture Review

### 2.1 Repository Structure
```
RetailIQ/
│
├── data/
│   ├── raw/
│   │   ├── train.csv (421,570 rows)
│   │   ├── test.csv (115,064 rows)
│   │   ├── stores.csv (45 rows)
│   │   ├── features.csv.zip / features.csv (8,190 rows)
│   │   └── sampleSubmission.csv
│   ├── processed/
│   │   ├── integrated_sales.parquet
│   │   ├── clean_features.parquet
│   │   └── data_audit_summary.json
│   └── knowledge_base/
│       └── policy_docs.txt (Synthetic internal business policy)
│
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_database.ipynb
│   ├── 05_feature_engineering.ipynb
│   ├── 06_tree_forecasting.ipynb
│   ├── 07_sequence_forecasting.ipynb
│   └── 08_model_comparison.ipynb
│
├── src/
│   ├── data/
│   │   ├── loader.py
│   │   ├── cleaner.py
│   │   └── pipeline.py
│   ├── database/
│   │   └── build_database.py
│   ├── features/
│   │   └── forecasting_features.py
│   └── forecasting/
│       ├── baseline.py
│       ├── train_tree.py
│       ├── train_sequence.py
│       ├── evaluate.py
│       └── predictor.py
│
├── models/
│   ├── trained/
│   │   └── retailiq_forecaster.pkl
│   └── metadata/
│       └── model_metadata.json
│
├── sql/
│   ├── schema.sql
│   └── analytics_queries.sql
│
├── reports/
│   ├── figures/ (01 to 06 presentation charts)
│   ├── metrics/
│   │   ├── forecast_cv_results.csv
│   │   └── model_comparison.csv
│   ├── reference_review.md
│   └── phase1_summary.md
│
├── docs/
│   └── phase2_api_contract.md
│
├── scripts/
│   ├── run_phase1.py
│   └── build_notebooks.py
│
├── backend/README.md
├── frontend/README.md
├── retailiq.db
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 3. Data Audit, Semantics & Decisions

| Dimension / Metric | Finding / Decision |
| :--- | :--- |
| **Dataset Files Found** | `train.csv`, `test.csv`, `stores.csv`, `features.csv.zip`, `sampleSubmission.csv` |
| **Dataset Dimensions** | `train`: 421,570 $\times$ 5 \| `test`: 115,064 $\times$ 4 \| `features`: 8,190 $\times$ 12 \| `stores`: 45 $\times$ 3 |
| **Historical Date Range** | **2010-02-05 to 2012-10-26** (143 weekly observations) |
| **Test Date Range** | **2012-11-02 to 2013-07-26** (39 weekly observations) |
| **Stores & Departments** | **45 unique stores**, **81 unique departments** |
| **Target Availability** | `Weekly_Sales` is fully available in `train.csv` (Mean: \$15,981.26, Median: \$7,612.03) |
| **Customer Returns (Negative Sales)** | Exactly **1,285 records (0.305%)** are negative (min: -\$4,988.94). Net return volume exceeding sales. Preserved without zero-clipping; flagged via `returns_flag = 1`. |
| **Promotional Markdowns** | `MarkDown1`–`MarkDown5` contain NaNs when no promotional discount was scheduled. Imputed with **$0.00$** and tracked via `has_markdown = 1/0`. |
| **Economic Indicators** | Missing `CPI` and `Unemployment` in feature horizon rows forward-filled per store. |
| **Product Text Limitation** | Walmart dataset does not contain product descriptions or item titles. Documented that text NLP features cannot be derived without an external catalog. |

---

## 4. Database Star Schema (`retailiq.db`)

The SQLite analytical warehouse follows a dimensional star schema:
- **`fact_sales` (421,570 rows):** `sales_id`, `store_id`, `dept_id`, `date_id`, `weekly_sales`, `returns_flag`, `is_holiday`, `temperature`, `fuel_price`, `cpi`, `unemployment`, `markdown1`–`markdown5`.
- **`dim_store` (45 rows):** `store_id`, `store_type`, `store_size`, `first_active_week`, `last_active_week`.
- **`dim_dept` (81 rows):** `dept_id`.
- **`dim_date` (182 rows):** `date_id` (YYYYMMDD), `full_date`, `year`, `quarter`, `month`, `month_name`, `week_of_year`, `is_holiday_week`.
- **Indexes:** Created on `fact_sales(store_id)`, `fact_sales(dept_id)`, `fact_sales(date_id)`, and `fact_sales(returns_flag)`.
- **SQL Analytics Suite:** 13 verified analytical queries in `sql/analytics_queries.sql` supporting store rankings, department contribution, YoY monthly growth, holiday lifts, running totals, and returns audits.

---

## 5. Feature Engineering (Leakage-Safe)

All features are engineered strictly on historical data using `shift(1)` prior to rolling calculations:
- **Calendar:** `year`, `quarter`, `month`, `week_of_year`, `day_of_year`, `is_holiday`, `is_month_start`, `is_month_end`.
- **Store Attributes:** `store_id`, `dept_id`, `store_type_encoded`, `store_size`.
- **Economic & Promo:** `temperature`, `fuel_price`, `cpi`, `unemployment`, `markdown1`..`5`, `has_markdown`, `total_markdown`.
- **Lags:** `lag_1`, `lag_2`, `lag_4`, `lag_8`, `lag_13`, `lag_26`, `lag_52` per store-department series.
- **Rolling Statistics:** `roll_mean_4`, `roll_std_4`, `roll_min_4`, `roll_max_4`, `roll_mean_8`, `roll_std_8`, `roll_mean_13`, `roll_std_13`, `sales_to_roll_mean_4`, `sales_to_roll_mean_13`.

---

## 6. Model Evaluation & Benchmark Comparison

Validation was conducted using **3-Fold Expanding-Window Forward-Chaining Time-Series CV** and a **20-Week Final Chronological Holdout (2012-06-01 to 2012-10-26)**:

| Model | Holdout RMSE | Holdout MAE | Holdout MAPE | Holdout WMAE (Holiday 5x) | Rationale & Performance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **LightGBM Regressor (Production)** | **$2,096.39** | **$1,081.88** | 138.81% | **$1,113.74** | **WINNER:** Superior handling of tabular retail covariates, fast inference (<1ms), lowest RMSE/WMAE. |
| **Sklearn HistGradientBoosting** | $2,610.87 | $1,264.45 | 218.49% | $1,307.87 | Competitive GBDT baseline. |
| **PyTorch LSTM (Sequence)** | $3,163.72 | $1,462.07 | 250.58% | $1,534.78 | 12-week lookback deep sequence network with date-safe splitting. |
| **Moving Average (4-Week)** | $3,456.32 | $1,567.53 | 47.59% | $1,627.09 | Statistical rolling mean benchmark. |
| **Naive (Lag-1)** | $3,476.17 | $1,540.86 | 32.31% | $1,629.04 | Persistence baseline. |
| **Seasonal Naive (52-Week)** | $3,589.61 | $1,717.45 | 485.70% | $1,732.00 | Prior-year same-week baseline. |

### Why LightGBM Won:
1. **Multivariate Power:** Combines historical lag dynamics, rolling volatility, store characteristics, promotional discounts, and calendar cycles in non-linear decision trees.
2. **Superior Accuracy:** Delivers a **33.7% reduction in RMSE** compared to deep LSTM networks and a **39.7% reduction** compared to naive baselines.
3. **Low Latency Inference:** Sub-millisecond execution per prediction step makes it ideal for real-time multi-step API serving.

---

## 7. Production Predictor Engine (`src/forecasting/predictor.py`)

- **Standalone Execution:** Runs fully outside Jupyter notebooks.
- **Recursive Multi-Step Forecasting:** Dynamically generates recursive lag and rolling features for horizons up to 52 weeks.
- **Macroeconomic Continuity Strategy:** Uses known feature schedules where available and falls back on latest-known store economic parameters, explicitly returning transparent assumption tags.
- **Structured Python/JSON Schema:** Outputs clean dictionaries ready for FastAPI REST endpoints.

---

## 8. Phase 2 Readiness Confirmation

Phase 1 provides all foundational artifacts for Phase 2:
- Database: `retailiq.db` with indexed star schema and `RetailAnalyticsService`.
- Model: `models/trained/retailiq_forecaster.pkl` with `RetailForecasterPredictor`.
- Policy Knowledge Base: `data/knowledge_base/policy_docs.txt`.
- Contracts: Complete REST API and AI Tool JSON schemas defined in `docs/phase2_api_contract.md`.
