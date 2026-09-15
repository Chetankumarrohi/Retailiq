# RetailIQ 5–7 Minute Live Demonstration Script

**Target Audience:** Evaluators, Professors, Industry Judges  
**Speaker Role:** Lead AI/Data Engineer  

---

### [0:00 – 0:45] 1. The Problem
"Good morning, everyone. In modern retail operations, supply chain managers face a constant dilemma: stockouts cause lost revenue, while overstocking leads to heavy markdowns and high holding costs. Traditional BI dashboards are static—they show you what happened yesterday, but cannot predict next month or explain company inventory policies.

Today, we present **RetailIQ**: an end-to-end Demand Forecasting and Multi-Tool AI Business Assistant that unites relational analytics, machine learning demand forecasting, and grounded document retrieval into a single, clean academic application."

---

### [0:45 – 1:30] 2. System Architecture
"RetailIQ is built on a clean, modular Python architecture:
- **Streamlit Web Application (`app.py`):** Interactive, reactive UI with an executive pearl/white theme and three dedicated operational tabs.
- **Relational Data Layer:** An analytical **SQLite Star Schema** database (`retailiq.db`) tracking 421,570 fact records across 45 stores and 81 departments.
- **Machine Learning Engine:** A trained **LightGBM 44-feature demand forecaster** providing recursive multi-step weekly sales projections.
- **Grounded AI Assistant:** A multi-tool orchestrator combining SQL analytics, forecasting inference, and **TF-IDF policy retrieval (RAG)**."

---

### [1:30 – 2:30] 3. Executive Dashboard
*(Action: Open http://localhost:8501 and view the Executive Dashboard tab)*  
"Here is the RetailIQ Executive Dashboard. Across our 45 stores and 81 departments, we see a verified cumulative sales volume of **$6.74 Billion**, with an average weekly store-department sales baseline of **$15,981**.

Notice our dynamic filtering:
- If I filter down to **Store 20**—our top revenue generator at **$301.4 Million**—the entire sales trend, store breakdown, and department rankings re-aggregate instantaneously via parameterized SQLite queries.
- We also quantify operational drivers: **Holiday weeks generate a +7.13% sales lift** ($17,036 vs $15,901 average), while promotional markdown weeks deliver a **+1.92% lift**.
- Toggling between Weekly and Monthly aggregation adapts the trend granularity while preserving total sales consistency."

---

### [2:30 – 3:30] 4. Demand Forecast Tab
*(Action: Click 'Demand Forecast' tab, select Store 20, Department 3, Horizon 4 weeks, and click 'Generate Forecast')*  
"Now, let's step into the **Demand Forecast** tab. Unlike basic time-series models, RetailIQ builds an exact **44-feature pipeline** on the fly—generating 52-week annual lags, 4-week rolling momentum, and promotional features.

When I run a 4-week forecast for Store 20, Department 3:
- The chart cleanly displays our **historical sales context alongside our forward projected curve**.
- The week-by-week table provides exact dollar projections and holiday week indicators.
- Non-negative constraints prevent erroneous negative forecasts."

---

### [3:30 – 5:00] 5. Multi-Tool Business Assistant
*(Action: Click 'Business Assistant' tab)*  
"The centerpiece of RetailIQ is our **Multi-Tool Business Assistant**. Rather than acting as a generic chatbot, it functions as an autonomous tool orchestrator with 3 specialized capabilities:

1. **SQL Analytics Tool:** Let's ask: *'Which store has the highest total sales?'*  
The assistant identifies a database inquiry, writes a secure `SELECT` query, executes it against `fact_sales`, and returns Store 20 with tabular proof and an expandable tool trace.

2. **Demand Forecast Tool:** Let's ask: *'Forecast Store 20 Department 3 for 4 weeks.'*  
The assistant routes to the production LightGBM model, performs recursive feature rolling, and outputs the projected demand table directly in conversation.

3. **Grounded Policy Retrieval (RAG):** Let's ask: *'What is our return policy?'*  
The assistant searches our internal policy index, returns the 30-day receipt window rule, and provides a verified citation to `policy_docs.txt Section 4`.

4. **Multi-Tool Composition:** Let's ask: *'Which department performs best in Store 20 and forecast it for the next 4 weeks?'*  
The assistant first runs SQL analytics to find the top department (Dept 92), then automatically triggers the forecast tool for that department, uniting both results into one cohesive response."

---

### [5:00 – 5:45] 6. Model Evaluation & Benchmarks
"Under our offline research benchmarks:
- Our champion **LightGBM model achieved a Test MAE of $1,385.12 and WAPE of 8.67%**, significantly outperforming baseline moving averages and LSTM sequence models.
- Tabular GBDTs dominate time-series forecasting in retail by handling complex non-linear promotional markdowns, calendar cycles, and regional economic variables."

---

### [5:45 – 6:30] 7. Limitations & Conclusion
"Finally, we maintain complete academic transparency:
- The dataset tracks weekly aggregate department sales rather than individual SKU units; our assistant explains policy cover targets rather than hallucinating physical unit counts.
- All SQL queries are sandboxed in read-only mode with token security validation.

RetailIQ proves how modern data science and agentic AI can transform raw transactional data into actionable commercial intelligence. Thank you, and we look forward to your questions."
