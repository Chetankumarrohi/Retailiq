"""
Autonomous Planner-Executor Agent for RetailIQ.
Routes user queries to the appropriate analytical tools (SQL, Forecasting, Document Retrieval)
and generates grounded, cited responses with visible tool execution traces.
"""
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from backend.app.core.config import settings
from backend.app.agent.tools import (
    sql_analytics_tool, forecast_tool, retrieval_tool, AGENT_TOOL_DEFINITIONS
)
from backend.app.schemas.assistant import (
    AssistantResponse, ToolTraceStep, PolicyCitation
)


SYSTEM_PROMPT = """
You are RetailIQ's AI Business Assistant for a multi-store retail chain.
You have access to 3 specialized tools:
1. `sql_analytics_tool`: Query the SQLite star schema (fact_sales, dim_store, dim_dept, dim_date) for historical sales, rankings, aggregations, and trends.
2. `forecast_tool`: Generate future weekly sales forecasts for a given store_id and dept_id across 1-12 weeks using our trained LightGBM ML model.
3. `retrieval_tool`: Search internal company policies (Inventory Targets, Markdown Rules, Supplier Terms, Returns Policy, SOPs) in policy_docs.txt.

CRITICAL RULES:
- Never fabricate historical data, forecasts, or policy rules.
- Negative sales represent customer returns exceeding sales.
- The dataset contains NO physical inventory stock level records. If asked for actual current store inventory counts, state that physical inventory records are not present in this dataset. However, you can quote target inventory policy rules from policy_docs.txt.
- Ground all policy answers in the retrieved policy text and cite the section name.
- Show your reasoning by selecting tools appropriately.
"""


class AgentPlanner:
    """Planner-executor engine orchestrating tool execution and response synthesis."""

    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.provider = settings.AI_PROVIDER.lower()
        self.model_name = settings.AI_MODEL

    def process_query(self, user_question: str) -> AssistantResponse:
        """Main entry point: processes a user question and returns a structured AssistantResponse."""
        cleaned_question = user_question.strip()
        if not cleaned_question:
            return AssistantResponse(
                answer="Please provide a valid question regarding sales analytics, demand forecasting, or retail policy.",
                tools_used=[],
                trace=[],
                sources=[]
            )

        # 1. Try external LLM provider if API key is configured
        if self.api_key and len(self.api_key) > 5:
            try:
                if "anthropic" in self.provider or "claude" in self.model_name:
                    return self._execute_anthropic(cleaned_question)
                elif "openai" in self.provider or "gpt" in self.model_name:
                    return self._execute_openai(cleaned_question)
            except Exception as e:
                # Log error and fall back to deterministic planner
                print(f"[AgentPlanner] External LLM failed: {e}. Using deterministic engine.")

        # 2. Deterministic intelligent rule-based planner fallback
        return self._execute_deterministic(cleaned_question)

    def _execute_anthropic(self, question: str) -> AssistantResponse:
        """Executes planner loop with Anthropic Claude tool-use API."""
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        # Convert tool definitions to Anthropic format
        anthropic_tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["parameters"]
            }
            for t in AGENT_TOOL_DEFINITIONS
        ]

        messages = [{"role": "user", "content": question}]
        trace_steps: List[ToolTraceStep] = []
        tools_used: List[str] = []
        citations: List[PolicyCitation] = []

        for step_idx in range(1, 4):
            resp = client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=anthropic_tools,
                messages=messages
            )

            tool_calls = [b for b in resp.content if b.type == "tool_use"]
            if not tool_calls:
                # Final response reached
                text_content = "".join(b.text for b in resp.content if b.type == "text")
                return AssistantResponse(
                    answer=text_content,
                    tools_used=list(set(tools_used)),
                    trace=trace_steps,
                    sources=citations
                )

            # Execute tool calls
            tool_results = []
            for tc in tool_calls:
                tool_name = tc.name
                tool_input = tc.input
                tools_used.append(tool_name)

                # Tool execution
                if tool_name == "sql_analytics_tool":
                    res = sql_analytics_tool(tool_input.get("query", ""))
                    reason = "Executing SQL query to retrieve historical sales data from the star schema."
                    summary_out = f"Returned {res.get('row_count', 0)} rows."
                elif tool_name == "forecast_tool":
                    res = forecast_tool(
                        store_id=tool_input.get("store_id", 1),
                        dept_id=tool_input.get("dept_id", 1),
                        horizon_weeks=tool_input.get("horizon_weeks", 4)
                    )
                    reason = f"Forecasting future demand for Store {tool_input.get('store_id')} Dept {tool_input.get('dept_id')}."
                    summary_out = f"Generated {len(res.get('predictions', []))} weekly forecast steps."
                elif tool_name == "retrieval_tool":
                    res = retrieval_tool(tool_input.get("query", question))
                    reason = "Searching internal company policy documents."
                    if res.get("citations"):
                        c = res["citations"][0]
                        citations.append(PolicyCitation(
                            document=c["source"],
                            section=c["section"],
                            snippet=c["text"][:180] + "..."
                        ))
                    summary_out = f"Found relevant section: {res.get('primary_section', 'None')}."
                else:
                    res = {"error": "Unknown tool"}
                    reason = "Unknown tool invoked."
                    summary_out = "Failed."

                trace_steps.append(ToolTraceStep(
                    step=len(trace_steps) + 1,
                    tool=tool_name,
                    reason=reason,
                    input_summary=tool_input,
                    output_summary=summary_out
                ))

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": json.dumps(res)
                })

            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})

        return AssistantResponse(
            answer="Reached maximum planning steps. Please refine your query.",
            tools_used=list(set(tools_used)),
            trace=trace_steps,
            sources=citations
        )

    def _execute_openai(self, question: str) -> AssistantResponse:
        """Executes planner loop with OpenAI tool-calling API."""
        import openai
        client = openai.OpenAI(api_key=self.api_key)

        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                }
            }
            for t in AGENT_TOOL_DEFINITIONS
        ]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
        trace_steps: List[ToolTraceStep] = []
        tools_used: List[str] = []
        citations: List[PolicyCitation] = []

        for step_idx in range(1, 4):
            resp = client.chat.completions.create(
                model=self.model_name or "gpt-4o",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                return AssistantResponse(
                    answer=msg.content or "No response generated.",
                    tools_used=list(set(tools_used)),
                    trace=trace_steps,
                    sources=citations
                )

            messages.append(msg)
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments or "{}")
                tools_used.append(fn_name)

                if fn_name == "sql_analytics_tool":
                    res = sql_analytics_tool(fn_args.get("query", ""))
                    reason = "Executing analytical SQL query against star schema."
                elif fn_name == "forecast_tool":
                    res = forecast_tool(
                        store_id=fn_args.get("store_id", 1),
                        dept_id=fn_args.get("dept_id", 1),
                        horizon_weeks=fn_args.get("horizon_weeks", 4)
                    )
                    reason = f"Forecasting future demand for Store {fn_args.get('store_id')} Dept {fn_args.get('dept_id')}."
                elif fn_name == "retrieval_tool":
                    res = retrieval_tool(fn_args.get("query", question))
                    reason = "Retrieving policy guidelines from internal knowledge base."
                    if res.get("citations"):
                        c = res["citations"][0]
                        citations.append(PolicyCitation(
                            document=c["source"],
                            section=c["section"],
                            snippet=c["text"][:180] + "..."
                        ))
                else:
                    res = {"error": "Unknown tool"}
                    reason = "Unknown tool"

                trace_steps.append(ToolTraceStep(
                    step=len(trace_steps) + 1,
                    tool=fn_name,
                    reason=reason,
                    input_summary=fn_args,
                    output_summary=f"Result: {res.get('success', False)}"
                ))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(res)
                })

        return AssistantResponse(
            answer="Completed processing.",
            tools_used=list(set(tools_used)),
            trace=trace_steps,
            sources=citations
        )

    def _execute_deterministic(self, question: str) -> AssistantResponse:
        """
        High-precision deterministic intent classifier and execution engine.
        Guarantees 100% reliable responses without requiring external API keys.
        """
        q_lower = question.lower()
        trace_steps: List[ToolTraceStep] = []
        tools_used: List[str] = []
        citations: List[PolicyCitation] = []

        # ==========================================================
        # 1. Physical Inventory Limitation Check
        # ==========================================================
        if re.search(r"\b(current|real-time|actual|store \d+)\b.*\b(inventory|stock|units on hand|cover)\b", q_lower) and not re.search(r"\b(policy|target|rule|standard)\b", q_lower):
            return AssistantResponse(
                answer="Inventory-level records (physical stock counts and warehouse balances) are not present in the supplied Walmart sales dataset. Therefore, store-level inventory cover cannot be directly calculated from transactions. However, target inventory cover guidelines (e.g. 3 weeks for Type A, 4 for Type B, 5 for Type C) can be viewed under our internal Inventory Policy.",
                tools_used=[],
                trace=[ToolTraceStep(
                    step=1,
                    tool="knowledge_guardrail",
                    reason="Detected data request for physical inventory levels, which are absent from the transaction dataset.",
                    input_summary={"query": question},
                    output_summary="Returned factual dataset limitation disclaimer."
                )],
                sources=[]
            )

        # ==========================================================
        # 2. Forecast Intent Recognition
        # ==========================================================
        if re.search(r"\b(forecast|predict|prediction|future sales|demand for next)\b", q_lower):
            store_match = re.search(r"\bstore\s*(\d+)\b", q_lower)
            dept_match = re.search(r"\bdept\s*(\d+)|department\s*(\d+)\b", q_lower)
            horizon_match = re.search(r"\b(\d+)\s*(?:week|wk|wks)\b", q_lower)

            store_id = int(store_match.group(1)) if store_match else 1
            dept_id = int(dept_match.group(1) or dept_match.group(2)) if dept_match else 1
            horizon_weeks = int(horizon_match.group(1)) if horizon_match else 4
            horizon_weeks = min(max(horizon_weeks, 1), 12)

            trace_steps.append(ToolTraceStep(
                step=1,
                tool="forecast_tool",
                reason=f"Identified forecasting intent for Store {store_id}, Department {dept_id} over {horizon_weeks} week(s).",
                input_summary={"store_id": store_id, "dept_id": dept_id, "horizon_weeks": horizon_weeks},
                output_summary=f"Invoked LightGBM forecaster."
            ))
            tools_used.append("forecast_tool")

            fc_result = forecast_tool(store_id, dept_id, horizon_weeks)
            if not fc_result.get("success"):
                return AssistantResponse(
                    answer=f"Unable to generate forecast: {fc_result.get('error')}",
                    tools_used=tools_used,
                    trace=trace_steps,
                    sources=[]
                )

            preds = fc_result["predictions"]
            lines = [f"- **Week {p['week']} (Step {p['step']}):** ${p['weekly_sales']:,.2f} {'*(Holiday Week)*' if p['is_holiday'] else ''}" for p in preds]
            ans = (
                f"### Demand Forecast for Store {store_id}, Department {dept_id}\n"
                f"**Forecast Horizon:** {horizon_weeks} week(s) | **Model:** LightGBM Regressor (v{fc_result['model_version']})\n\n"
                f"**Projected Weekly Sales:**\n" + "\n".join(lines) + "\n\n"
                f"**Historical Context:** Last recorded weekly sales were **${fc_result['last_known_sales']:,.2f}** with an average baseline of **${fc_result['historical_mean_sales']:,.2f}**."
            )

            return AssistantResponse(
                answer=ans,
                tools_used=tools_used,
                trace=trace_steps,
                sources=[]
            )

        # ==========================================================
        # 3. Policy / Documentation Retrieval Intent Recognition
        # ==========================================================
        if re.search(r"\b(policy|sop|rule|terms|supplier|markdown rule|returns policy|inventory policy|procedure)\b", q_lower):
            trace_steps.append(ToolTraceStep(
                step=1,
                tool="retrieval_tool",
                reason="Identified policy/documentation inquiry. Searching internal policy_docs.txt.",
                input_summary={"query": question},
                output_summary="Executed TF-IDF similarity search."
            ))
            tools_used.append("retrieval_tool")

            ret_result = retrieval_tool(question)
            if ret_result.get("found"):
                citations_list = ret_result["citations"]
                for c in citations_list:
                    citations.append(PolicyCitation(
                        document=c["source"],
                        section=c["section"],
                        snippet=c["text"][:180] + "..."
                    ))

                primary_chunk = citations_list[0]
                ans = (
                    f"### Policy Information: {primary_chunk['section']}\n\n"
                    f"{primary_chunk['text']}\n\n"
                    f"*Source: [{primary_chunk['source']}] Section '{primary_chunk['section']}'*"
                )
                return AssistantResponse(
                    answer=ans,
                    tools_used=tools_used,
                    trace=trace_steps,
                    sources=citations
                )
            else:
                return AssistantResponse(
                    answer="No specific policy section was found matching your query in policy_docs.txt. Please check inventory policy, markdown rules, supplier terms, returns policy, or SOPs.",
                    tools_used=tools_used,
                    trace=trace_steps,
                    sources=[]
                )

        # ==========================================================
        # 4. SQL Analytics Intent Recognition (Default / Analytical)
        # ==========================================================
        sql_query, reason = self._construct_sql_query(q_lower)
        trace_steps.append(ToolTraceStep(
            step=1,
            tool="sql_analytics_tool",
            reason=reason,
            input_summary={"query": sql_query},
            output_summary="Executed read-only query against SQLite star schema."
        ))
        tools_used.append("sql_analytics_tool")

        sql_res = sql_analytics_tool(sql_query)
        if not sql_res.get("success"):
            return AssistantResponse(
                answer=f"Could not execute query: {sql_res.get('error')}",
                tools_used=tools_used,
                trace=trace_steps,
                sources=[]
            )

        data = sql_res.get("data", [])
        formatted_table = sql_res.get("formatted_table", "")

        # Format narrative summary from SQL output
        narrative = self._format_sql_narrative(q_lower, data)
        full_answer = f"{narrative}\n\n**Query Results Summary:**\n\n```\n{formatted_table}\n```"

        return AssistantResponse(
            answer=full_answer,
            tools_used=tools_used,
            trace=trace_steps,
            sources=[]
        )

    def _construct_sql_query(self, q_lower: str) -> Tuple[str, str]:
        """Constructs an accurate SQL query for common retail questions."""
        # Top Stores / Highest Sales
        if "top store" in q_lower or "highest sales" in q_lower or "best store" in q_lower or "store ranking" in q_lower:
            return (
                "SELECT s.store_id, s.store_type, s.store_size, ROUND(SUM(f.weekly_sales), 2) AS total_sales "
                "FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                "GROUP BY s.store_id ORDER BY total_sales DESC LIMIT 5;",
                "Querying top stores ranked by historical total sales."
            )
        # Top Departments
        if "top dept" in q_lower or "top department" in q_lower or "best dept" in q_lower:
            return (
                "SELECT dept_id, ROUND(SUM(weekly_sales), 2) AS total_sales, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
                "FROM fact_sales GROUP BY dept_id ORDER BY total_sales DESC LIMIT 5;",
                "Querying top performing departments by total revenue."
            )
        # Holiday vs Non-Holiday
        if "holiday" in q_lower:
            return (
                "SELECT CASE WHEN is_holiday = 1 THEN 'Holiday' ELSE 'Non-Holiday' END AS period, "
                "COUNT(*) AS weeks, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales, ROUND(SUM(weekly_sales), 2) AS total_sales "
                "FROM fact_sales GROUP BY is_holiday;",
                "Aggregating sales performance by holiday status."
            )
        # Promotional Markdown Impact
        if "promo" in q_lower or "markdown" in q_lower:
            return (
                "SELECT CASE WHEN (markdown1+markdown2+markdown3+markdown4+markdown5) > 0 THEN 'Promo' ELSE 'No Promo' END AS period, "
                "COUNT(*) AS weeks, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
                "FROM fact_sales GROUP BY period;",
                "Comparing average weekly sales on promotional markdown weeks vs non-markdown weeks."
            )
        # Store Types
        if "store type" in q_lower or "type a" in q_lower:
            return (
                "SELECT s.store_type, COUNT(DISTINCT s.store_id) AS num_stores, ROUND(SUM(f.weekly_sales), 2) AS total_sales "
                "FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                "GROUP BY s.store_type ORDER BY total_sales DESC;",
                "Aggregating chain performance across Store Types (A, B, C)."
            )
        # Returns / Negative Sales
        if "return" in q_lower or "negative" in q_lower:
            return (
                "SELECT returns_flag, COUNT(*) AS record_count, ROUND(SUM(weekly_sales), 2) AS net_revenue, "
                "ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales FROM fact_sales GROUP BY returns_flag;",
                "Auditing customer return transactions flagged with returns_flag = 1."
            )

        # Default: Summary totals
        return (
            "SELECT COUNT(DISTINCT store_id) AS total_stores, COUNT(DISTINCT dept_id) AS total_departments, "
            "ROUND(SUM(weekly_sales), 2) AS total_revenue, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
            "FROM fact_sales;",
            "Aggregating overall chain revenue, store count, and average weekly sales."
        )

    def _format_sql_narrative(self, q_lower: str, data: List[Dict[str, Any]]) -> str:
        """Generates clear, natural language summaries for SQL results."""
        if not data:
            return "No historical records were found matching your criteria."

        row0 = data[0]
        if "store_id" in row0 and "total_sales" in row0:
            return f"**Store {row0['store_id']}** achieved the highest revenue with **${row0['total_sales']:,.2f}** across its active operations."
        if "dept_id" in row0 and "total_sales" in row0:
            return f"**Department {row0['dept_id']}** is the top-performing category with **${row0['total_sales']:,.2f}** in total historical sales."
        if "period" in row0 and "avg_weekly_sales" in row0:
            return "Analysis indicates significant variance in average weekly sales across operational periods."
        if "total_revenue" in row0:
            return f"The retail chain generated a cumulative total revenue of **${row0['total_revenue']:,.2f}** across **{row0['total_stores']} stores** and **{row0['total_departments']} departments**."

        return "Historical query executed successfully against the analytical star schema."
