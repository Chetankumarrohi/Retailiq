# RetailIQ 10-Slide Presentation Content

---

## SLIDE 1: Title Slide
- **Title:** RetailIQ: Enterprise Demand Forecasting & Multi-Tool AI Business Assistant
- **Subtitle:** Unifying Relational Warehousing, Machine Learning Demand Forecasting, and Grounded Agentic Intelligence
- **Key Points:**
  - Production-ready full-stack retail intelligence system
  - 45 Stores, 81 Departments, 421,570 Historical Observations ($6.74B Volume)
  - FastAPI Backend + React 18 / Vite SPA + LightGBM Engine + Autonomous Multi-Tool Agent
- **Recommended Visual:** System hero banner showing the multi-tier architecture diagram.
- **Speaker Notes:** "Welcome. Today we present RetailIQ, an integrated retail analytics platform that transitions retail organizations from static reporting to predictive demand intelligence and grounded conversational assistance."

---

## SLIDE 2: Problem Statement & Industry Context
- **Title:** Operational Challenges in Modern Retail
- **Key Points:**
  - **The Supply Chain Dilemma:** Stockouts cost billions in lost revenue, while overstocking triggers destructive markdown cycles.
  - **Static Dashboards Fail:** Traditional BI dashboards only show historical summaries; they lack multi-step forward prediction capabilities.
  - **Fragmented Knowledge:** Policy guidelines (markdown rules, return windows) reside in static PDFs detached from analytical workflows.
- **Recommended Visual:** Split infographic comparing "Fragmented Traditional BI" vs "Integrated RetailIQ Architecture".
- **Speaker Notes:** "Retailers struggle with two primary challenges: accurately predicting future store-department demand and quickly synthesizing transactional data with operational policies."

---

## SLIDE 3: Dataset Architecture & Star Schema
- **Title:** Data Engineering & Relational Star Schema
- **Key Points:**
  - **Dataset Scope:** 421,570 historical records across 45 stores and 81 departments (2010–2012).
  - **Central Fact Table (`fact_sales`):** Weekly sales, markdowns (MD1-5), temperature, fuel price, CPI, unemployment.
  - **Conformed Dimensions:** `dim_store` (type, footprint size), `dim_dept` (merchandise categories), `dim_date` (4-5-4 retail calendar).
  - **Performance:** B-Tree indexed SQLite warehouse executing sub-millisecond analytical aggregations.
- **Recommended Visual:** Star Schema ERD diagram with `fact_sales` surrounded by the 3 dimension tables.
- **Speaker Notes:** "We engineered a star schema data warehouse that cleanses raw retail transactions and structures them for high-speed dimensional querying."

---

## SLIDE 4: Full-Stack System Architecture
- **Title:** 3-Tier Multi-Tool Architecture
- **Key Points:**
  - **Frontend SPA:** React 18 + Vite with Recharts data visualization and glassmorphism styling.
  - **API Gateway:** FastAPI Python application with asynchronous routing and strict Pydantic validation.
  - **Security Layer:** Read-only SQLite URI (`mode=ro`) and SQL AST validator blocking destructive DDL/DML.
  - **Autonomous Agent Layer:** Planner-Executor loop routing queries to SQL, forecasting, and TF-IDF policy tools.
- **Recommended Visual:** Architectural block diagram showing data flow from User down to DB, Model, and Knowledge Base.
- **Speaker Notes:** "Our architecture cleanly separates presentation from business logic while enforcing strict security boundaries on data access."

---

## SLIDE 5: Executive Analytics Dashboard
- **Title:** Executive Business Intelligence & KPI Discovery
- **Key Points:**
  - **Verified Lifetime Sales:** $6,737,218,987.11 ($6.74B) across 45 stores.
  - **Baseline Velocity:** Average store-department sales of $15,981.26 per week.
  - **Holiday Impact:** Holiday weeks drive a verified **+7.13% sales lift** ($17,036 vs $15,901).
  - **Top Performers:** Store 20 ($301.4M) and Department 92 ($483.9M) lead chain revenue.
- **Recommended Visual:** Screenshot of Executive Dashboard showing KPI cards, Sales Trend line, and Store Type pie chart.
- **Speaker Notes:** "The dashboard delivers real-time executive visibility with interactive store and department filters that re-query the indexed warehouse dynamically."

---

## SLIDE 6: Machine Learning Feature Engineering
- **Title:** 44-Feature Production Forecasting Pipeline
- **Key Points:**
  - **Autoregressive Lags (7):** Captures short-term momentum (1, 2, 4, 8, 13 weeks) and 52-week annual seasonality.
  - **Rolling Statistics (14):** 4, 8, and 13-week moving means, standard deviations, and min/max boundaries.
  - **Calendar & Promotion (15):** Week of year, holiday flags, MarkDown1-5 activities, and total markdown volume.
  - **Macroeconomic & Entity (8):** CPI, fuel prices, unemployment rate, store type embeddings, and store size.
- **Recommended Visual:** Feature Importance horizontal bar chart highlighting `dept_id`, `week_of_year`, and `lag_52`.
- **Speaker Notes:** "We developed an exact 44-feature engineering pipeline that transforms raw time-series data into predictive signals for machine learning."

---

## SLIDE 7: Forecasting Model Evaluation & Benchmarks
- **Title:** Rigorous Forward Time-Series Validation
- **Key Points:**
  - **Validation Design:** Forward-chaining time-series split (Holdout starting 2012-07-27) preventing lookahead bias.
  - **Champion Model:** LightGBM GBDT Regressor (400 trees, learning rate 0.04, num_leaves=63).
  - **Holdout Evaluation:** **Weighted MAE (WMAE) of $1,250.03**, RMSE of $2,496.47, and MAE of $1,213.40.
  - **Benchmark Superiority:** Outperformed linear models and deep sequence LSTM architectures.
- **Recommended Visual:** Forecast Explorer curve showing historical baseline and multi-step projected curve.
- **Speaker Notes:** "Our model evaluation uses time-based holdouts rather than random cross-validation, guaranteeing realistic production performance."

---

## SLIDE 8: Multi-Tool Autonomous Business Assistant
- **Title:** Agentic AI with Grounded Tool Execution
- **Key Points:**
  - **Tool 1 — SQL Analytics:** Autonomously composes and executes safe `SELECT` queries against the star schema.
  - **Tool 2 — ML Forecaster:** Triggers recursive multi-step LightGBM predictions for any store-department segment.
  - **Tool 3 — Policy Retrieval:** Conducts TF-IDF cosine similarity search against internal company documentation.
  - **Visible Execution Trace:** Full transparency in 'How RetailIQ Answered' panel with zero hidden hallucination.
- **Recommended Visual:** Assistant interface screenshot showing chat bubble, execution trace badge, and policy citation card.
- **Speaker Notes:** "RetailIQ's AI Assistant functions as an autonomous reasoning agent, dynamically choosing tools to deliver grounded, cited responses."

---

## SLIDE 9: Security, Guardrails & Production Readiness
- **Title:** Production Hardening & Security Guardrails
- **Key Points:**
  - **Zero-Trust SQL Sandboxing:** Dual-layer protection (application token whitelist + SQLite C-engine read-only connection).
  - **Injection Resistance:** Blocks multi-statement attacks, DDL commands (`DROP`, `ALTER`), and confidential file access.
  - **Factuality Guardrails:** Honest disclaimers when asked for unrecorded physical warehouse stock counts.
  - **Automated Test Suite:** 20 automated Pytest test cases validating 100% of endpoints and security rules.
- **Recommended Visual:** Security workflow diagram illustrating the dual-layer validation checkpoint.
- **Speaker Notes:** "We prioritized reliability and security: the assistant is strictly sandboxed to read-only analytics and validated tools."

---

## SLIDE 10: Conclusion, Limitations & Future Scope
- **Title:** Project Summary & Future Scope
- **Key Points:**
  - **Summary:** RetailIQ delivers a full-stack, submission-ready demand intelligence and conversational assistant platform.
  - **Known Limitations:** Transactional financial grain without physical warehouse stock counts; synthetic policy docs.
  - **Future Roadmap:**
    - Hierarchical reconciliation across store networks.
    - Probabilistic quantile demand forecasting ($P_{10}, P_{50}, P_{90}$).
    - Enterprise cloud deployment on Snowflake and Kubernetes.
- **Recommended Visual:** Summary scorecard table with checkmarks across all Phase 1, Phase 2, and Phase 3 deliverables.
- **Speaker Notes:** "In conclusion, RetailIQ provides a robust blueprint for enterprise retail intelligence. Thank you for your time."
