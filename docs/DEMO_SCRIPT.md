# RetailIQ 5–7 Minute Live Demonstration Script

**Target Audience:** Evaluators, Professors, Industry Judges  
**Speaker Role:** Lead AI/Data Engineer  

---

### [0:00 – 0:45] 1. The Problem
"Good morning, everyone. In modern retail operations, supply chain managers face a constant dilemma: stockouts cause lost revenue, while overstocking leads to heavy markdowns and high holding costs. Traditional BI dashboards are static—they show you what happened yesterday, but cannot predict next month or explain company inventory policies.

Today, we present **RetailIQ**: an end-to-end Demand Forecasting and Multi-Tool AI Business Assistant that unites relational analytics, machine learning demand forecasting, and grounded document retrieval into a single production application."

---

### [0:45 – 1:30] 2. System Architecture
"RetailIQ is built on a 3-tier architecture:
- On the frontend: a high-performance **React 18 and Vite SPA** with dark-mode glassmorphism and Recharts visualizations.
- On the backend: a modular **FastAPI** application with asynchronous API routing, schema validation via Pydantic, and strict SQL security guardrails.
- In the data layer: an analytical **SQLite Star Schema** database with 421,570 fact records, a trained **LightGBM 44-feature demand forecaster**, and a **TF-IDF policy retrieval engine**."

---

### [1:30 – 2:30] 3. Executive Dashboard
*(Action: Navigate to http://localhost:5173)*  
"Here is the RetailIQ Executive Dashboard. Across our 45 stores and 81 departments, we see a verified cumulative sales volume of **$6.74 Billion**, with an average weekly store-department sales baseline of **$15,981**.

Notice our dynamic filtering:
- If I filter down to **Store 20**—our top revenue generator at **$301.4 Million**—the entire sales trend re-aggregates instantaneously via indexed database queries.
- We also quantify operational drivers: **Holiday weeks generate a +7.13% sales lift** ($17,036 vs $15,901 average), while promotional markdown weeks deliver a **+1.92% lift**."

---

### [2:30 – 3:30] 4. Demand Forecast Explorer
*(Action: Click 'Forecast' on the sidebar, select Store 1, Department 1, Horizon 4 weeks, and click 'Generate Forecast')*  
"Now, let's step into the **Demand Forecast Explorer**. Unlike basic time-series models, RetailIQ builds an exact **44-feature pipeline** on the fly—generating 52-week annual lags, 4-week rolling momentum, and promotional features.

When I run a 4-week forecast for Store 1, Department 1:
- The chart cleanly displays our **historical baseline sales of $22,513** alongside our forward projected curve.
- Notice the pink vertical marker: **'Forecast Starts'**.
- For Week 4 (ending November 23), our model automatically identifies the Thanksgiving holiday week and projects an elevated demand of **$28,275.14**, allowing store managers to preemptively schedule replenishment."

---

### [3:30 – 5:00] 5. Autonomous Multi-Tool Business Assistant
*(Action: Click 'AI Assistant' on the sidebar)*  
"The centerpiece of RetailIQ is our **Autonomous Business Assistant**. Rather than acting as a generic chatbot, it functions as a Planner-Executor agent with 3 specialized tools:

1. **SQL Analytics Tool:** Let's ask: *'Which store has the highest total sales?'*  
*(Click or type question)*  
The agent autonomously identifies a database inquiry, writes a secure `SELECT` query, executes it against `fact_sales`, and returns Store 20 with formatted tabular proof. On the right, the **'How RetailIQ Answered'** panel shows the full execution trace.

2. **ML Forecasting Tool:** Let's ask: *'Forecast Store 1 Department 1 for 4 weeks.'*  
*(Click question)*  
The agent routes to the production LightGBM model, performs recursive feature rolling, and outputs the projected demand table directly in conversation.

3. **Grounded Policy Retrieval:** Let's ask: *'What is the returns policy?'*  
*(Click question)*  
The agent queries our internal policy vector index, returns the 30-day receipt window rule, and provides a verified citation to `policy_docs.txt Section 4`."

---

### [5:00 – 5:45] 6. Model Evaluation & Insights
*(Action: Click 'Data Insights' on the sidebar)*  
"Under **Data Insights**, we expose our model engineering rigor:
- Our champion LightGBM model achieved a **Weighted Mean Absolute Error (WMAE) of $1,250.03** on our out-of-time holdout test set, significantly outperforming linear and deep learning LSTM baselines.
- The feature importance chart demonstrates that department category, annual seasonality (week of year), and 52-week prior-year lag dominate demand patterns."

---

### [5:45 – 6:30] 7. Limitations & Conclusion
"Finally, we maintain complete transparency:
- The dataset lacks physical warehouse inventory stock tables, so our assistant explains policy cover targets rather than hallucinating physical unit counts.
- All SQL queries are sandboxed in read-only URI mode with AST token validation.

RetailIQ proves how modern data science and agentic AI can transform raw transactional data into actionable operational intelligence. Thank you, and we look forward to your questions."
