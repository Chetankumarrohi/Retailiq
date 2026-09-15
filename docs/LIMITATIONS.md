# RetailIQ Limitations & Assumptions Document

In accordance with rigorous academic and engineering standards, this document details the architectural boundaries, dataset limitations, and operational assumptions of RetailIQ.

---

## 1. Dataset Boundaries & Granularity

1. **Absence of Physical Inventory Counts:**
   - The supplied Walmart historical retail dataset contains weekly aggregate financial transactions (`Weekly_Sales`), promotional markdowns, and macroeconomic indicators. It does **not** contain unit-level stock-keeping units (SKUs), warehouse stock on hand, or replenishment order queues.
   - Consequently, store-level inventory cover (weeks of supply) cannot be empirically computed from transaction rows. RetailIQ provides target inventory rules from policy documentation while explicitly disclaiming physical counts when asked.

2. **Absence of Natural Language Product Catalogs:**
   - Merchandise is categorized numerically by `dept_id` (1 through 99). The original dataset does not provide item titles, brand names, or text descriptions.

3. **Customer Returns Semantics:**
   - Negative values in `Weekly_Sales` reflect store-department weeks where customer refund and return dollar volumes exceeded gross sales. These are valid retail transactions rather than data corruptions and are preserved in training and analytics.

---

## 2. Forecasting Engine Assumptions

1. **Exogenous Feature Availability:**
   - Future demand forecasting relies on recursive lag generation. For future macroeconomic indicators (CPI, Unemployment, Temperature, Fuel Price), the predictor references scheduled feature entries where available, or defaults to the latest known historical level (macroeconomic continuity assumption).

2. **Recursive Error Accumulation:**
   - In multi-step recursive forecasting (e.g. 12 weeks out), model predictions from Step $t$ are fed back as `lag_1` inputs for Step $t+1$. While regularized through rolling statistics, recursive forecasting carries greater uncertainty at extended horizons compared to immediate 1-to-4-week projections.

---

## 3. Knowledge Base & Agent Environment

1. **Synthetic Policy Documentation:**
   - Internal policies in `policy_docs.txt` (Inventory Coverage, Markdown Cadence, Supplier Payment Terms, Returns Policy, Store Safety SOPs) are synthetic demonstration documents created to test grounded multi-tool retrieval. They do not represent Walmart corporate policy.

2. **Demonstration Database Scale:**
   - The SQLite star schema database (`retailiq.db`) is optimized with B-Tree indexes for single-node college and hackathon demonstration workloads (~421,570 rows). For enterprise multi-region deployments with millions of concurrent transactions, migration to PostgreSQL or Snowflake with connection pooling is recommended.
