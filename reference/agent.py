"""
RetailIQ Agent - planner-executor with 3 tools:
  1. sql_tool      - runs a SQL query the LLM writes against the star schema
  2. forecast_tool - calls the trained LightGBM model for a store/dept/horizon
  3. retrieval_tool - keyword search over policy_docs.txt, returns cited section

Requires: pip install anthropic
Set your key first:  setx ANTHROPIC_API_KEY "sk-..."   (Windows, then reopen terminal)
"""
import sqlite3, re, joblib, pandas as pd, numpy as np, os, json

DB = "retailiq.db"
SCHEMA_DESC = """
Star schema tables in retailiq.db (SQLite):
- fact_sales(store_id, dept_id, date_id, weekly_sales, Returns_Flag, IsHoliday,
             Temperature, Fuel_Price, CPI, Unemployment, MarkDown1..MarkDown5)
- dim_store(store_id, store_type, store_size, first_active_week, last_active_week)
- dim_dept(dept_id)
- dim_date(date_id, year, month, week_of_year, is_holiday_week)
date_id is an integer YYYYMMDD, e.g. 20120127. Join fact_sales.date_id = dim_date.date_id.
No inventory table exists in this dataset - say so if asked about stock/inventory cover.
"""

# ---- Tool 1: SQL ----
def sql_tool(query: str) -> str:
    """Runs a read-only SQL query against the star schema and returns rows as text."""
    if not re.match(r"^\s*SELECT", query, re.IGNORECASE):
        return "Error: only SELECT queries are allowed."
    con = sqlite3.connect(DB)
    try:
        df = pd.read_sql(query, con)
        return df.head(50).to_string(index=False)
    except Exception as e:
        return f"SQL error: {e}"
    finally:
        con.close()

# ---- Tool 2: Forecast ----
_model_bundle = None
def _load_model():
    global _model_bundle
    if _model_bundle is None:
        _model_bundle = joblib.load("forecast_model.pkl")
    return _model_bundle

def forecast_tool(store_id: int, dept_id: int, horizon_weeks: int = 4) -> str:
    """Forecasts weekly sales for a store-dept for the next N weeks using the trained model."""
    bundle = _load_model()
    model, feature_cols = bundle["model"], bundle["features"]
    hist = pd.read_parquet("model_features.parquet")
    series = hist[(hist.store_id == store_id) & (hist.dept_id == dept_id)].sort_values("date")
    if series.empty:
        return f"No history found for store {store_id}, dept {dept_id}."
    last_row = series.iloc[-1:].copy()
    preds = []
    recent_sales = list(series["weekly_sales"].tail(52))
    for h in range(horizon_weeks):
        row = last_row.copy()
        for lag in [1, 2, 4, 8, 52]:
            row[f"lag_{lag}"] = recent_sales[-lag] if len(recent_sales) >= lag else recent_sales[0]
        for win in [4, 8, 12]:
            row[f"roll_mean_{win}"] = np.mean(recent_sales[-win:])
            row[f"roll_std_{win}"] = np.std(recent_sales[-win:])
        pred = max(0, model.predict(row[feature_cols])[0])
        preds.append(round(pred, 1))
        recent_sales.append(pred)
    return f"Store {store_id}, Dept {dept_id} forecast for next {horizon_weeks} week(s): {preds}"

# ---- Tool 3: Retrieval ----
def retrieval_tool(question: str) -> str:
    """Keyword search over internal policy documentation, returns the matching section with a citation."""
    text = open("policy_docs.txt").read()
    sections = re.split(r"\n(?=\d\.\s[A-Z])", text)
    q_words = set(re.findall(r"\w+", question.lower()))
    best, best_score = None, 0
    for sec in sections:
        sec_words = set(re.findall(r"\w+", sec.lower()))
        score = len(q_words & sec_words)
        if score > best_score:
            best, best_score = sec, score
    if not best:
        return "No matching policy section found."
    title = best.strip().split("\n")[0]
    return f"[Source: policy_docs.txt - '{title}']\n{best.strip()}"

TOOLS = [
    {"name": "sql_tool", "description": "Run a SQL SELECT against the star schema for sales/analytics questions.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "forecast_tool", "description": "Forecast future weekly sales for a specific store and department.",
     "input_schema": {"type": "object", "properties": {
         "store_id": {"type": "integer"}, "dept_id": {"type": "integer"},
         "horizon_weeks": {"type": "integer"}}, "required": ["store_id", "dept_id"]}},
    {"name": "retrieval_tool", "description": "Answer policy/SOP/inventory-rule/markdown-rule/returns/supplier questions from internal docs.",
     "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
]

def run_tool(name, inp):
    if name == "sql_tool": return sql_tool(inp["query"])
    if name == "forecast_tool": return forecast_tool(inp["store_id"], inp["dept_id"], inp.get("horizon_weeks", 4))
    if name == "retrieval_tool": return retrieval_tool(inp["question"])
    return "Unknown tool"

def ask_agent(user_question: str, max_steps: int = 4):
    """Planner-executor loop using Claude's tool-use API. Returns (answer, reasoning_trace)."""
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
    system = f"You are RetailIQ's business assistant. {SCHEMA_DESC}\nUse the tools to answer. Show your reasoning. Cite the source document when the answer involves policy."
    messages = [{"role": "user", "content": user_question}]
    trace = []
    for _ in range(max_steps):
        resp = client.messages.create(model="claude-sonnet-4-5", max_tokens=1024,
                                       system=system, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        tool_calls = [b for b in resp.content if b.type == "tool_use"]
        if not tool_calls:
            final_text = "".join(b.text for b in resp.content if b.type == "text")
            return final_text, trace
        tool_results = []
        for tc in tool_calls:
            result = run_tool(tc.name, tc.input)
            trace.append({"tool": tc.name, "input": tc.input, "result": result})
            tool_results.append({"type": "tool_result", "tool_use_id": tc.id, "content": result})
        messages.append({"role": "user", "content": tool_results})
    return "Reached step limit without a final answer.", trace

if __name__ == "__main__":
    # Local test of the tools without needing the API key
    print(sql_tool("SELECT store_id, SUM(weekly_sales) s FROM fact_sales GROUP BY store_id ORDER BY s DESC LIMIT 3"))
    print()
    print(forecast_tool(1, 1, horizon_weeks=3))
    print()
    print(retrieval_tool("what is the markdown rule for slow moving stock"))
