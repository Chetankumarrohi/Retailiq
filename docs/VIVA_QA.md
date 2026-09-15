# RetailIQ Technical Viva & Examination Q&A

Comprehensive technical questions and concise, defensible answers covering data engineering, time-series modeling, FastAPI, React, SQL security, and AI agent architectures.

---

### 1. What is RetailIQ?
RetailIQ is an enterprise demand forecasting and multi-tool AI business assistant application. It combines a 45-store analytical star schema database, a 44-feature LightGBM demand forecasting model, and an autonomous Planner-Executor agent with natural language SQL querying, forecasting, and policy retrieval.

### 2. Why use FastAPI instead of Flask or Django?
FastAPI provides asynchronous execution (`asyncio`), automated OpenAPI (Swagger) documentation generation, type validation via Pydantic schemas, and sub-millisecond serialization speeds compared to synchronous frameworks.

### 3. Why use React with Vite?
React offers component-based declarative state management and ecosystem support for data visualization (Recharts). Vite leverages native ES modules and Rollup for instant Hot Module Replacement (HMR) and sub-second production bundle builds.

### 4. Why SQLite for the analytical database?
SQLite is a zero-configuration, self-contained serverless SQL engine that allows B-Tree indexing and executes sub-millisecond complex analytical queries across ~421,570 records without external database daemon dependencies.

### 5. What is a star schema?
A star schema is a dimensional data modeling pattern where a central fact table containing numerical measurements (`fact_sales`) connects directly to multiple de-normalized dimension tables (`dim_store`, `dim_dept`, `dim_date`) via foreign keys.

### 6. What is a fact table?
A fact table contains quantitative business measurements and foreign keys to dimension tables. In RetailIQ, `fact_sales` records `weekly_sales`, `markdown1-5`, `temperature`, `fuel_price`, `cpi`, and `unemployment` at the grain of `(store_id, dept_id, date_id)`.

### 7. What is a dimension table?
A dimension table contains contextual attributes that describe fact records. In RetailIQ, `dim_store` describes store physical size and type (A/B/C), `dim_dept` describes department IDs, and `dim_date` describes retail calendar weeks, quarters, and holiday tags.

### 8. Why select LightGBM over standard decision trees or Random Forest?
LightGBM uses gradient-based one-side sampling (GOSS) and Exclusive Feature Bundling (EFB) with leaf-wise tree growth, achieving higher accuracy, faster training on large tabular datasets, and natural handling of non-linear interactions across macroeconomic and calendar features.

### 9. What are lag features?
Lag features are historical values of the target variable from prior time steps ($y_{t-1}, y_{t-2}, y_{t-52}$). They allow gradient boosting models to capture auto-regressive momentum and seasonal cycles.

### 10. What are rolling window features?
Rolling features compute aggregate statistics (mean, standard deviation, minimum, maximum) over moving historical windows (e.g., 4, 8, 13 weeks) to represent moving baselines and demand volatility.

### 11. What is data leakage in time-series forecasting?
Data leakage occurs when future information ($t+k$) is inadvertently included in training feature calculations for time step $t$ (e.g., computing a global mean over the entire dataset or using future target values).

### 12. Why use time-based validation instead of k-fold random cross-validation?
Random k-fold CV shuffles future observations into training folds, causing lookahead bias. Time-based validation (forward chaining or out-of-time holdout splits) ensures the model is always trained on historical periods and tested strictly on subsequent future periods.

### 13. What is RMSE (Root Mean Squared Error)?
RMSE is the square root of the average squared differences between predicted and actual values: $\sqrt{\frac{1}{n}\sum(y_i - \hat{y}_i)^2}$. It penalizes large prediction errors quadratically.

### 14. What is MAE (Mean Absolute Error)?
MAE is the average of the absolute differences between predictions and actual targets: $\frac{1}{n}\sum |y_i - \hat{y}_i|$. It provides an intuitive, linear measure of average prediction error in dollars.

### 15. What is MAPE (Mean Absolute Percentage Error)?
MAPE measures the percentage difference relative to actual values: $\frac{100\%}{n}\sum |\frac{y_i - \hat{y}_i}{y_i}|$. It can become skewed when actual sales are near zero.

### 16. What is WMAE (Weighted Mean Absolute Error)?
WMAE weights holiday weeks higher (typically weight=5 vs weight=1 for normal weeks) to emphasize forecast accuracy during critical high-volume promotional periods: $\frac{\sum w_i |y_i - \hat{y}_i|}{\sum w_i}$.

### 17. Why use baseline models?
Baseline models (such as predicting the historical median or previous year same-week sales $y_{t-52}$) establish a benchmark to prove that complex ML models add genuine predictive lift over trivial heuristics.

### 18. What is an LSTM and how does it compare with LightGBM on tabular retail data?
An LSTM (Long Short-Term Memory) is a recurrent neural network designed for sequential data. While effective for continuous signals, tree-based GBDT models like LightGBM consistently outperform LSTMs on tabular retail data due to tabular inductive biases, heterogenous feature scales, and categorical embeddings.

### 19. What is RAG (Retrieval-Augmented Generation)?
RAG dynamically fetches relevant external document passages from a knowledge base to ground language model responses with verifiable citations rather than relying solely on parametric memory.

### 20. What is TF-IDF (Term Frequency-Inverse Document Frequency)?
TF-IDF evaluates how important a word is to a document within a collection. Term frequency measures word occurrence within a chunk, while inverse document frequency downweights universally common words across the corpus.

### 21. What is tool calling in AI agents?
Tool calling allows an LLM or planner to recognize user intent, construct structured arguments (JSON), and trigger external software routines (SQL queries, ML forecasters, vector searches) to generate factual outputs.

### 22. How does the RetailIQ planner select tools?
The planner uses intent classification (or LLM tool-calling when API keys are supplied) to map questions to `sql_analytics_tool` for historical aggregations, `forecast_tool` for future demand predictions, or `retrieval_tool` for company policy searches.

### 23. How is the SQL analytics tool secured against injection and data loss?
Security is enforced at two independent layers:
1. **Application Layer:** An AST/regex validator enforces single `SELECT` or `WITH ... SELECT` statements, blocks forbidden DDL/DML keywords (`DROP`, `INSERT`, `DELETE`, `PRAGMA`), blocks semicolons, and enforces an approved table whitelist (`fact_sales`, `dim_store`, `dim_dept`, `dim_date`).
2. **Database Engine Layer:** SQLite connections are opened with read-only URI mode (`?mode=ro`), causing the SQLite C-engine to reject write operations at the OS level.

### 24. What happens if no external AI API key is configured?
RetailIQ features a built-in deterministic rule-based planner that classifies intents, executes SQL/forecast/retrieval tools, and formats Markdown responses with 100% reliability and zero external latency or cost.

### 25. Why are policy answers cited?
Citing the source document (`policy_docs.txt`) and exact section header prevents hallucination and allows business users to verify the grounded policy rule.

### 26. What are RetailIQ's known limitations?
1. The dataset contains financial sales transactions but lacks physical warehouse unit-level stock inventory counts.
2. Merchandise is indexed by department ID without natural language product titles.
3. Exogenous future macroeconomic indicators rely on scheduled inputs or continuity assumptions.

### 27. Why can't the assistant report exact inventory stock levels?
Because the underlying historical Walmart competition dataset records weekly financial sales figures rather than physical warehouse stock receipts or perpetual inventory logs.

### 28. How do negative sales occur in the dataset?
Negative `weekly_sales` values represent customer return and refund volumes that exceeded gross sales in a specific store-department during that week.

### 29. How would you scale RetailIQ in an enterprise production environment?
1. Migrate the data warehouse from SQLite to PostgreSQL, Snowflake, or BigQuery.
2. Deploy the FastAPI backend inside Kubernetes clusters behind an API Gateway with horizontal pod autoscaling.
3. Cache frequent analytical queries with Redis.
4. Schedule automated weekly batch re-training of LightGBM models via Airflow or Kubeflow.

### 30. What future improvements would you implement next?
1. Incorporate hierarchical reconciliation (e.g. MinT / Top-Down) across chain-store-dept hierarchies.
2. Add probabilistic quantile regression models (e.g. LightGBM pinball loss for $P_{10}, P_{50}, P_{90}$ demand intervals).
3. Integrate real-time webhook ingestion for live point-of-sale streams.
