"""
Multi-Tool Business Assistant Engine for RetailIQ Streamlit Application.
Orchestrates SQL Analytics, Demand Forecasting, and Policy Retrieval tools with
multi-tool composition, conversational context tracking, and security guardrails.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from src.database.analytics import AnalyticsService
from src.forecasting.predictor import RetailForecasterPredictor
from src.assistant.retrieval import PolicyRetriever


class RetailIQAssistant:
    """Orchestrator for RetailIQ multi-tool AI assistant."""

    def __init__(self):
        self.analytics_service = AnalyticsService()
        self.predictor = RetailForecasterPredictor()
        self.retriever = PolicyRetriever.get_instance()

    # ==========================================================
    # Tool 1: SQL Analytics Tool
    # ==========================================================
    def sql_tool(self, sql: str) -> Dict[str, Any]:
        """Executes a safe read-only SQL query against retailiq.db."""
        return self.analytics_service.execute_safe_query(sql, max_rows=25)

    # ==========================================================
    # Tool 2: Demand Forecast Tool
    # ==========================================================
    def forecast_tool(self, store_id: int, dept_id: int, horizon_weeks: int = 4) -> Dict[str, Any]:
        """Generates future sales predictions using the trained LightGBM model."""
        try:
            horizon_weeks = min(max(int(horizon_weeks), 1), 12)
            res = self.predictor.predict(store_id=int(store_id), dept_id=int(dept_id), horizon_weeks=horizon_weeks)
            return {"success": True, "data": res}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================
    # Tool 3: Policy Retrieval Tool
    # ==========================================================
    def retrieval_tool(self, query: str) -> Dict[str, Any]:
        """Searches internal policy documentation (policy_docs.txt)."""
        try:
            results = self.retriever.search(query, top_k=2)
            if results:
                return {"success": True, "found": True, "citations": results}
            return {"success": True, "found": False, "citations": []}
        except Exception as e:
            return {"success": False, "error": str(e), "citations": []}

    # ==========================================================
    # Master Processing & Tool Routing
    # ==========================================================
    def ask(self, question: str, session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main query handler: analyzes intent, extracts entities, executes tools,
        and formats an academic, grounded response with a concise tool trace.
        """
        q = question.strip()
        q_lower = q.lower()
        context = session_context or {}

        trace: List[Dict[str, Any]] = []
        tools_used: List[str] = []

        # ------------------------------------------------------
        # 1. Guardrail: Out of Scope Questions
        # ------------------------------------------------------
        out_of_scope_patterns = [
            r"\b(who is the prime minister|who is president|cricket match|football score|who won the)\b",
            r"\b(write (a|python) code for|calculator|poem|story|recipe|weather in paris|capital of)\b",
            r"\b(movie|song|actor|actress|celebrity|joke|translate|horoscope)\b"
        ]
        if any(re.search(pat, q_lower) for pat in out_of_scope_patterns) and not any(k in q_lower for k in ["store", "sales", "retail", "forecast", "policy", "markdown", "dept"]):
            return {
                "answer": "This question is outside RetailIQ's scope. I can assist with retail sales analysis, store/department performance rankings, demand forecasting, promotions, holidays, and internal retail policies.",
                "tools_used": [],
                "trace": [
                    {
                        "step": 1,
                        "tool": "Scope Guardrail",
                        "reason": "Evaluated question against domain boundary.",
                        "metadata": "Out-of-scope query rejected."
                    }
                ],
                "updated_context": context
            }

        # ------------------------------------------------------
        # 2. Guardrail: Physical Inventory Limitation
        # ------------------------------------------------------
        if re.search(r"\b(how many units|current stock|physical inventory|units on hand|inventory count|warehouse balance)\b", q_lower) and not re.search(r"\b(policy|target|rule|standard|reorder)\b", q_lower):
            trace.append({
                "step": 1,
                "tool": "Data Limitation Guardrail",
                "reason": "Request for physical stock level records not present in transactions dataset.",
                "metadata": "Grounded disclaimer provided."
            })
            return {
                "answer": "Physical inventory stock records (individual unit counts and shelf balances) are not tracked in this Walmart transaction dataset. Current store-level physical units cannot be computed. However, target inventory cover guidelines (3 weeks for Type A stores, 4 weeks for Type B, 5 weeks for Type C) can be reviewed in our internal **Inventory Policy**.",
                "tools_used": ["Data Limitation Guardrail"],
                "trace": trace,
                "updated_context": context
            }

        # ------------------------------------------------------
        # 3. Multi-Tool: Department Ranking + Forecast
        # Example: "Which department performs best in Store 20 and forecast it for the next 4 weeks?"
        # ------------------------------------------------------
        if ("best" in q_lower or "top" in q_lower or "highest" in q_lower) and ("dept" in q_lower or "department" in q_lower) and ("forecast" in q_lower or "predict" in q_lower):
            store_id = self._extract_store_id(q_lower, context) or 20
            horizon = self._extract_horizon(q_lower) or 4

            # Step 1: SQL to find best department in store
            sql = f"""
            SELECT dept_id, ROUND(SUM(weekly_sales), 2) AS total_sales
            FROM fact_sales WHERE store_id = {store_id}
            GROUP BY dept_id ORDER BY total_sales DESC LIMIT 1;
            """
            tools_used.append("SQL Analytics Tool")
            trace.append({
                "step": 1,
                "tool": "SQL Analytics Tool",
                "reason": f"Identifying top-performing department in Store {store_id}.",
                "query": sql.strip(),
                "metadata": f"Store {store_id} dept ranking"
            })
            sql_res = self.sql_tool(sql)
            top_dept_id = 92  # default fallback
            if sql_res.get("success") and sql_res.get("data"):
                top_dept_id = int(sql_res["data"][0]["dept_id"])
                dept_sales = float(sql_res["data"][0]["total_sales"])
            else:
                dept_sales = 0.0

            # Step 2: Forecast Tool
            tools_used.append("Demand Forecast Tool")
            trace.append({
                "step": 2,
                "tool": "Demand Forecast Tool",
                "reason": f"Generating {horizon}-week demand forecast for identified top category (Dept {top_dept_id}) in Store {store_id}.",
                "metadata": f"Store {store_id}, Dept {top_dept_id}, Horizon {horizon}w"
            })
            fc_res = self.forecast_tool(store_id, top_dept_id, horizon)

            context["last_store_id"] = store_id
            context["last_dept_id"] = top_dept_id

            if fc_res.get("success"):
                fc_data = fc_res["data"]
                preds = fc_data["predictions"]
                pred_lines = [f"- **{p['week']} (Step {p['step']}):** ${p['weekly_sales']:,.2f} {'*(Holiday)*' if p['is_holiday'] else ''}" for p in preds]
                proj_total = sum(p["weekly_sales"] for p in preds)

                answer = (
                    f"### Multi-Tool Analysis: Store {store_id} Best Department Forecast\n\n"
                    f"1. **Analytical Finding (SQL):** In **Store {store_id}**, the top-performing category is **Department {top_dept_id}** with **${dept_sales:,.2f}** in cumulative sales.\n"
                    f"2. **Demand Forecast (LightGBM):** Generated a **{horizon}-week** forward-looking forecast for **Store {store_id}, Department {top_dept_id}**:\n\n"
                    + "\n".join(pred_lines) + "\n\n"
                    f"- **Projected {horizon}-Week Total:** **${proj_total:,.2f}**\n"
                    f"- **Historical Average:** **${fc_data['historical_summary']['historical_mean_sales']:,.2f}**/week\n"
                    f"- **Last Known Sales:** **${fc_data['historical_summary']['last_known_sales']:,.2f}**"
                )
            else:
                answer = f"Found top Department {top_dept_id} in Store {store_id}, but forecasting failed: {fc_res.get('error')}"

            return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 4. Multi-Tool: Top Store + Policy Retrieval
        # Example: "Which store has the highest sales and what is our reorder policy?"
        # ------------------------------------------------------
        if ("highest sales" in q_lower or "top store" in q_lower or "best store" in q_lower) and ("reorder" in q_lower or "policy" in q_lower or "inventory" in q_lower or "cover" in q_lower):
            # Step 1: SQL for top store
            sql = "SELECT s.store_id, s.store_type, ROUND(SUM(f.weekly_sales), 2) AS total_sales FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id GROUP BY s.store_id ORDER BY total_sales DESC LIMIT 1;"
            tools_used.append("SQL Analytics Tool")
            trace.append({
                "step": 1,
                "tool": "SQL Analytics Tool",
                "reason": "Finding store with highest cumulative sales.",
                "query": sql,
                "metadata": "Store ranking query"
            })
            sql_res = self.sql_tool(sql)
            top_store_info = "Store 20"
            if sql_res.get("success") and sql_res.get("data"):
                r = sql_res["data"][0]
                top_store_info = f"**Store {r['store_id']}** (Type {r['store_type']}) with **${float(r['total_sales']):,.2f}** in total sales"

            # Step 2: Policy Retrieval for inventory/reorder
            tools_used.append("Policy Retrieval Tool")
            trace.append({
                "step": 2,
                "tool": "Policy Retrieval Tool",
                "reason": "Retrieving inventory and reorder policy from policy_docs.txt.",
                "metadata": "Source: policy_docs.txt (Section 1: Inventory Policy)"
            })
            ret_res = self.retrieval_tool("inventory reorder policy target cover")
            policy_text = ""
            if ret_res.get("citations"):
                policy_text = ret_res["citations"][0]["text"]

            answer = (
                f"### Combined Analysis: Top Store & Inventory Reorder Policy\n\n"
                f"1. **Top Performing Store (SQL Analytics):**\n"
                f"   - {top_store_info}.\n\n"
                f"2. **Reorder & Inventory Policy (Internal Documentation):**\n"
                f"   ```\n{policy_text}\n   ```\n\n"
                f"*Source: policy_docs.txt (Section 1: INVENTORY POLICY)*"
            )
            return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 5. Multi-Tool: Store Comparison & Forecast Recommendation
        # Example: "Compare Store 10 and Store 20 and tell me which one I should forecast."
        # ------------------------------------------------------
        if ("compare" in q_lower) and ("store" in q_lower) and ("forecast" in q_lower or "should" in q_lower):
            store_nums = [int(m) for m in re.findall(r"\bstore\s*(\d+)\b", q_lower)]
            s1 = store_nums[0] if len(store_nums) > 0 else 10
            s2 = store_nums[1] if len(store_nums) > 1 else 20

            sql = f"""
            SELECT s.store_id, s.store_type, s.store_size,
                   ROUND(SUM(f.weekly_sales), 2) AS total_sales,
                   ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales
            FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id
            WHERE s.store_id IN ({s1}, {s2})
            GROUP BY s.store_id;
            """
            tools_used.append("SQL Analytics Tool")
            trace.append({
                "step": 1,
                "tool": "SQL Analytics Tool",
                "reason": f"Comparing sales and size metrics between Store {s1} and Store {s2}.",
                "query": sql.strip(),
                "metadata": f"Stores {s1} vs {s2}"
            })
            res = self.sql_tool(sql)
            table_md = res.get("formatted_markdown", "")

            # Recommendation logic based on volume
            data = res.get("data", [])
            higher_store = s2
            if len(data) == 2:
                higher_store = data[0]["store_id"] if data[0]["total_sales"] > data[1]["total_sales"] else data[1]["store_id"]

            answer = (
                f"### Comparative Performance: Store {s1} vs Store {s2}\n\n"
                f"**Metrics Comparison:**\n\n{table_md}\n\n"
                f"**Forecasting Recommendation:**\n"
                f"- **Store {higher_store}** generates the higher sales volume, making accurate forward demand forecasting critical for inventory replenishment.\n"
                f"- To forecast Store {higher_store}, you can ask: *'Forecast Store {higher_store} Department 1 for 4 weeks'*."
            )
            context["last_store_id"] = higher_store
            return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 5.5 Direct Raw SQL Input
        # ------------------------------------------------------
        if re.match(r"^\s*(select|drop|delete|insert|update|create|alter|truncate|pragma)\b", q_lower):
            tools_used.append("SQL Analytics Tool")
            trace.append({
                "step": 1,
                "tool": "SQL Analytics Tool",
                "reason": "Direct SQL query execution with security sandbox validation.",
                "query": q,
                "metadata": "Raw SQL input"
            })
            res = self.sql_tool(q)
            if not res.get("success"):
                return {
                    "answer": f"🔒 **Security Violation / SQL Error:**\n\n`{res.get('error')}`\n\n*RetailIQ permits only read-only SELECT queries on the analytical star schema.*",
                    "tools_used": tools_used,
                    "trace": trace,
                    "updated_context": context
                }
            return {
                "answer": f"### Direct SQL Query Results\n\n{res.get('formatted_markdown')}",
                "tools_used": tools_used,
                "trace": trace,
                "updated_context": context
            }

        # ------------------------------------------------------
        # 6. Standalone Forecast Intent
        # Examples: "Forecast Store 20 Department 3 for 4 weeks", "predict sales for store 20 dept 3", "what will sales look like for department 3 in store 20?"
        # ------------------------------------------------------
        if re.search(r"\b(forecast|predict|prediction|project sales|future demand|what will sales look like|sales look like|expected sales)\b", q_lower):
            store_id = self._extract_store_id(q_lower, context) or 1
            dept_id = self._extract_dept_id(q_lower, context) or 1
            horizon = self._extract_horizon(q_lower) or 4

            tools_used.append("Demand Forecast Tool")
            trace.append({
                "step": 1,
                "tool": "Demand Forecast Tool",
                "reason": f"Generating multi-step demand predictions for Store {store_id}, Department {dept_id} over {horizon} weeks.",
                "metadata": f"Store: {store_id}, Dept: {dept_id}, Horizon: {horizon}w, Model: LightGBM"
            })

            fc_res = self.forecast_tool(store_id, dept_id, horizon)
            context["last_store_id"] = store_id
            context["last_dept_id"] = dept_id

            if not fc_res.get("success"):
                return {
                    "answer": f"⚠️ Unable to generate forecast for Store {store_id}, Department {dept_id}: {fc_res.get('error')}. Please ensure this store-department combination exists.",
                    "tools_used": tools_used,
                    "trace": trace,
                    "updated_context": context
                }

            fc_data = fc_res["data"]
            preds = fc_data["predictions"]
            lines = [f"| Week {p['step']} | {p['week']} | ${p['weekly_sales']:,.2f} | {'Yes' if p['is_holiday'] else 'No'} |" for p in preds]
            table = "| Step | Target Week | Forecasted Sales | Holiday Week |\n|---|---|---|:---:|\n" + "\n".join(lines)
            total_proj = sum(p["weekly_sales"] for p in preds)
            avg_proj = total_proj / len(preds)

            answer = (
                f"### Demand Forecast: Store {store_id}, Department {dept_id}\n\n"
                f"- **Model:** LightGBM Regressor (Multi-Step Lag/Rolling Recursive Features)\n"
                f"- **Forecast Horizon:** {horizon} weeks\n"
                f"- **Projected Total Sales:** **${total_proj:,.2f}** (Avg: **${avg_proj:,.2f}**/week)\n"
                f"- **Historical Baseline:** Mean = **${fc_data['historical_summary']['historical_mean_sales']:,.2f}**/week | Last Known = **${fc_data['historical_summary']['last_known_sales']:,.2f}**\n\n"
                f"{table}"
            )
            return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 6.5 Promotional & Holiday Analytical Questions (Priority over Policy)
        # ------------------------------------------------------
        if re.search(r"\b(perform better|did markdown|markdown impact|markdown weeks|promo weeks|holiday weeks compare|normal weeks)\b", q_lower):
            sql, reason, summary_template = self._build_analytical_sql(q_lower, context)
            tools_used.append("SQL Analytics Tool")
            trace.append({
                "step": 1,
                "tool": "SQL Analytics Tool",
                "reason": reason,
                "query": sql,
                "metadata": "Promotional / Holiday comparative SQL analysis"
            })
            sql_res = self.sql_tool(sql)
            data = sql_res.get("data", [])
            md_table = sql_res.get("formatted_markdown", "")
            narrative = self._generate_sql_narrative(q_lower, data, summary_template)
            answer = f"### Sales Analytics Findings\n\n{narrative}\n\n**Data Summary:**\n\n{md_table}"
            return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 7. Standalone Policy Retrieval / RAG Intent
        # ------------------------------------------------------
        policy_keywords = [
            "policy", "sop", "return", "refund", "receipt", "markdown", "discount",
            "clearance", "supplier", "payment terms", "reorder", "safety stock",
            "discrepanc", "variance", "procedure", "shrinkage", "lead time", "cover"
        ]
        if any(k in q_lower for k in policy_keywords):
            tools_used.append("Policy Retrieval Tool")
            trace.append({
                "step": 1,
                "tool": "Policy Retrieval Tool",
                "reason": "Searching internal standard operating procedures and policies in policy_docs.txt.",
                "metadata": f"Query: '{question}'"
            })

            ret_res = self.retrieval_tool(question)
            if ret_res.get("found"):
                chunks = ret_res["citations"]
                primary = chunks[0]
                sec_name = primary["section"]
                sec_text = primary["text"]
                score = primary.get("score", 1.0)

                answer = (
                    f"### Policy Documentation: {sec_name}\n\n"
                    f"**Internal Policy Document Content:**\n\n"
                    f"```\n{sec_text}\n```\n\n"
                    f"- **Source:** `data/knowledge_base/policy_docs.txt`\n"
                    f"- **Section:** `{sec_name}`\n"
                    f"- **Relevance Score:** `{score:.2f}`\n\n"
                    f"*(Note: Internal policies are synthetic guidelines provided for operational RetailIQ demonstration).* "
                )
                return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

        # ------------------------------------------------------
        # 8. SQL Analytics Intent (Historical Analysis)
        # ------------------------------------------------------
        sql, reason, summary_template = self._build_analytical_sql(q_lower, context)
        tools_used.append("SQL Analytics Tool")
        trace.append({
            "step": 1,
            "tool": "SQL Analytics Tool",
            "reason": reason,
            "query": sql,
            "metadata": "Star schema execution (fact_sales, dim_store, dim_dept, dim_date)"
        })

        sql_res = self.sql_tool(sql)
        if not sql_res.get("success"):
            return {
                "answer": f"SQL Execution Error: {sql_res.get('error')}",
                "tools_used": tools_used,
                "trace": trace,
                "updated_context": context
            }

        data = sql_res.get("data", [])
        md_table = sql_res.get("formatted_markdown", "")

        # Generate narrative
        narrative = self._generate_sql_narrative(q_lower, data, summary_template)

        # Context updates
        if data and "store_id" in data[0]:
            context["last_store_id"] = int(data[0]["store_id"])
        if data and "dept_id" in data[0]:
            context["last_dept_id"] = int(data[0]["dept_id"])

        answer = f"### Sales Analytics Findings\n\n{narrative}\n\n**Data Summary:**\n\n{md_table}"
        return {"answer": answer, "tools_used": tools_used, "trace": trace, "updated_context": context}

    # ==========================================================
    # Entity Extraction Helpers
    # ==========================================================
    def _extract_store_id(self, q_lower: str, context: Dict[str, Any]) -> Optional[int]:
        m = re.search(r"\bstore\s*(\d+)\b", q_lower)
        if m:
            return int(m.group(1))
        # Context follow-up
        if "its" in q_lower or "that store" in q_lower or "this store" in q_lower:
            return context.get("last_store_id")
        return None

    def _extract_dept_id(self, q_lower: str, context: Dict[str, Any]) -> Optional[int]:
        m = re.search(r"\b(?:dept|department)\s*(\d+)\b", q_lower)
        if m:
            return int(m.group(1))
        if "its" in q_lower or "that dept" in q_lower:
            return context.get("last_dept_id")
        return None

    def _extract_horizon(self, q_lower: str) -> Optional[int]:
        m = re.search(r"\b(\d+)\s*(?:weeks|week|wk|wks)\b", q_lower)
        if m:
            return min(max(int(m.group(1)), 1), 12)
        if "next month" in q_lower or "1 month" in q_lower:
            return 4
        if "2 months" in q_lower:
            return 8
        if "3 months" in q_lower or "quarter" in q_lower:
            return 12
        return None

    # ==========================================================
    # Intelligent SQL Query Builder for Diverse Natural Questions
    # ==========================================================
    def _build_analytical_sql(self, q_lower: str, context: Dict[str, Any]) -> Tuple[str, str, str]:
        """Constructs an accurate parameterized or filtered SQL query for analytical questions."""
        # Top Stores / Best Performing Stores / Highest Sales Store
        has_store = bool(re.search(r"\b(store|stores)\b", q_lower))
        has_top = bool(re.search(r"\b(top|best|highest|leading|most sales|rank|ranking|largest)\b", q_lower))
        has_dept = bool(re.search(r"\b(dept|department|departments|category)\b", q_lower))

        if (has_store and has_top) and not has_dept:
            limit_m = re.search(r"\b(?:top|best|first)\s*(\d+)\b", q_lower)
            lim = int(limit_m.group(1)) if limit_m else 5
            lim = min(max(lim, 1), 45)
            return (
                f"SELECT s.store_id, s.store_type, s.store_size, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                f"GROUP BY s.store_id ORDER BY total_sales DESC LIMIT {lim};",
                f"Querying top {lim} stores ranked by total sales.",
                "top_stores"
            )

        # Worst / Lowest Performing Stores
        if re.search(r"\b(worst|lowest|bottom|underperforming)\b.*\b(store|stores)\b", q_lower):
            limit_m = re.search(r"\b(?:bottom|worst|lowest)\s*(\d+)\b", q_lower)
            lim = int(limit_m.group(1)) if limit_m else 5
            return (
                f"SELECT s.store_id, s.store_type, s.store_size, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                f"GROUP BY s.store_id ORDER BY total_sales ASC LIMIT {lim};",
                f"Querying bottom {lim} stores by total sales.",
                "worst_stores"
            )

        # Compare Store X and Store Y
        if "compare" in q_lower and "store" in q_lower:
            store_nums = [int(m) for m in re.findall(r"\bstore\s*(\d+)\b", q_lower)]
            if len(store_nums) >= 2:
                s_list = ",".join(str(s) for s in store_nums[:5])
                return (
                    f"SELECT s.store_id, s.store_type, s.store_size, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                    f"FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                    f"WHERE s.store_id IN ({s_list}) GROUP BY s.store_id ORDER BY total_sales DESC;",
                    f"Comparing sales across stores: {s_list}.",
                    "compare_stores"
                )

        # How much did Store X sell?
        store_id_match = re.search(r"\bstore\s*(\d+)\b", q_lower)
        if store_id_match and ("how much" in q_lower or "sales for" in q_lower or "total" in q_lower or "performance" in q_lower):
            s_id = int(store_id_match.group(1))
            return (
                f"SELECT s.store_id, s.store_type, s.store_size, COUNT(DISTINCT f.dept_id) AS active_depts, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                f"WHERE s.store_id = {s_id} GROUP BY s.store_id;",
                f"Retrieving cumulative sales and metrics for Store {s_id}.",
                "single_store"
            )

        # Top Departments in Store X
        if ("top" in q_lower or "best" in q_lower) and ("dept" in q_lower or "department" in q_lower) and store_id_match:
            s_id = int(store_id_match.group(1))
            return (
                f"SELECT dept_id, ROUND(SUM(weekly_sales), 2) AS total_sales, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales WHERE store_id = {s_id} GROUP BY dept_id ORDER BY total_sales DESC LIMIT 5;",
                f"Querying top departments for Store {s_id}.",
                "top_depts_in_store"
            )

        # Top Departments Overall
        if re.search(r"\b(top|best|highest|leading)\b.*\b(dept|department|departments)\b", q_lower) or "department ranking" in q_lower:
            return (
                "SELECT dept_id, ROUND(SUM(weekly_sales), 2) AS total_sales, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
                "FROM fact_sales GROUP BY dept_id ORDER BY total_sales DESC LIMIT 10;",
                "Querying top 10 departments across all stores.",
                "top_depts_global"
            )

        # Compare Department X across stores
        dept_match = re.search(r"\b(?:dept|department)\s*(\d+)\b", q_lower)
        if dept_match and ("across" in q_lower or "compare" in q_lower or "stores" in q_lower):
            d_id = int(dept_match.group(1))
            return (
                f"SELECT s.store_id, s.store_type, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                f"WHERE f.dept_id = {d_id} GROUP BY s.store_id ORDER BY total_sales DESC LIMIT 10;",
                f"Comparing Department {d_id} performance across stores.",
                "dept_across_stores"
            )

        # Sales for Department X
        if dept_match and ("sales" in q_lower or "how much" in q_lower or "total" in q_lower):
            d_id = int(dept_match.group(1))
            return (
                f"SELECT dept_id, COUNT(DISTINCT store_id) AS active_stores, ROUND(SUM(weekly_sales), 2) AS total_sales, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
                f"FROM fact_sales WHERE dept_id = {d_id} GROUP BY dept_id;",
                f"Calculating total sales for Department {d_id}.",
                "single_dept"
            )

        # Sales in a specific year (2010, 2011, 2012)
        year_match = re.search(r"\b(2010|2011|2012)\b", q_lower)
        if year_match:
            yr = int(year_match.group(1))
            return (
                f"SELECT d.year, d.month, d.month_name, ROUND(SUM(f.weekly_sales), 2) AS monthly_sales "
                f"FROM fact_sales f JOIN dim_date d ON f.date_id = d.date_id "
                f"WHERE d.year = {yr} GROUP BY d.year, d.month, d.month_name ORDER BY d.month ASC;",
                f"Aggregating monthly sales performance for calendar year {yr}.",
                "year_sales"
            )

        # Best performing month
        if "best month" in q_lower or "highest month" in q_lower or "top month" in q_lower:
            return (
                "SELECT d.year || '-' || printf('%02d', d.month) AS year_month, d.month_name, d.year, ROUND(SUM(f.weekly_sales), 2) AS total_sales "
                "FROM fact_sales f JOIN dim_date d ON f.date_id = d.date_id "
                "GROUP BY year_month, d.month_name, d.year ORDER BY total_sales DESC LIMIT 5;",
                "Querying top performing calendar months historically.",
                "top_months"
            )

        # Holiday vs Normal weeks
        if "holiday" in q_lower:
            return (
                "SELECT CASE WHEN is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS period, "
                "COUNT(*) AS observation_count, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales, ROUND(SUM(weekly_sales), 2) AS total_sales "
                "FROM fact_sales GROUP BY is_holiday;",
                "Evaluating holiday vs non-holiday sales performance.",
                "holiday"
            )

        # Promotional markdown impact
        if "promo" in q_lower or "markdown" in q_lower:
            return (
                "SELECT CASE WHEN (markdown1+markdown2+markdown3+markdown4+markdown5) > 0 THEN 'Promo Markdown' ELSE 'No Markdown' END AS period, "
                "COUNT(*) AS observation_count, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales, ROUND(SUM(weekly_sales), 2) AS total_sales "
                "FROM fact_sales GROUP BY period;",
                "Analyzing promotional markdown impact on sales volume.",
                "promo"
            )

        # Store Types (A, B, C)
        if "store type" in q_lower or "type a" in q_lower or "type b" in q_lower or "type c" in q_lower:
            return (
                "SELECT s.store_type, COUNT(DISTINCT s.store_id) AS num_stores, ROUND(SUM(f.weekly_sales), 2) AS total_sales, ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales "
                "FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id "
                "GROUP BY s.store_type ORDER BY total_sales DESC;",
                "Aggregating sales by Store Format/Type (A, B, C).",
                "store_types"
            )

        # Default: Global summary
        return (
            "SELECT COUNT(DISTINCT store_id) AS total_stores, COUNT(DISTINCT dept_id) AS total_departments, "
            "ROUND(SUM(weekly_sales), 2) AS total_sales, ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales "
            "FROM fact_sales;",
            "Calculating global chain sales summary.",
            "global_summary"
        )

    def _generate_sql_narrative(self, q_lower: str, data: List[Dict[str, Any]], template_type: str) -> str:
        """Generates clear, informative narrative text summarizing SQL results."""
        if not data:
            return "No historical data matched the specified criteria."

        row0 = data[0]

        if template_type == "top_stores":
            return f"**Store {row0['store_id']}** ranks #1 across the entire retail network with **${row0['total_sales']:,.2f}** in cumulative sales (averaging **${row0['avg_weekly_sales']:,.2f}**/week)."

        if template_type == "worst_stores":
            return f"**Store {row0['store_id']}** (Type {row0.get('store_type', '')}) has the lowest recorded sales at **${row0['total_sales']:,.2f}**."

        if template_type == "single_store":
            return f"**Store {row0['store_id']}** (Type {row0.get('store_type', '')}, Size: {row0.get('store_size', 0):,} sq ft) generated **${row0['total_sales']:,.2f}** across {row0.get('active_depts', 'all')} departments with an average weekly sales rate of **${row0['avg_weekly_sales']:,.2f}**."

        if template_type == "top_depts_in_store":
            return f"Within the requested store, **Department {row0['dept_id']}** leads category sales with **${row0['total_sales']:,.2f}**."

        if template_type == "top_depts_global":
            return f"Across the entire retail chain, **Department {row0['dept_id']}** is the highest-grossing department with **${row0['total_sales']:,.2f}** in total historical sales."

        if template_type == "single_dept":
            return f"**Department {row0['dept_id']}** is active across {row0.get('active_stores', 45)} stores, generating a cumulative **${row0['total_sales']:,.2f}** in total sales."

        if template_type == "holiday":
            hol_row = next((r for r in data if "Holiday" in str(r.get("period", "")) and "Non" not in str(r.get("period", ""))), None)
            non_row = next((r for r in data if "Non-Holiday" in str(r.get("period", ""))), None)
            if hol_row and non_row:
                lift = ((hol_row["avg_weekly_sales"] - non_row["avg_weekly_sales"]) / non_row["avg_weekly_sales"]) * 100.0
                return f"Holiday weeks generated an average of **${hol_row['avg_weekly_sales']:,.2f}** per store-department week compared to **${non_row['avg_weekly_sales']:,.2f}** on regular weeks, representing a **+{lift:.2f}% holiday lift**."

        if template_type == "promo":
            promo_row = next((r for r in data if "Promo" in str(r.get("period", ""))), None)
            non_row = next((r for r in data if "No" in str(r.get("period", ""))), None)
            if promo_row and non_row:
                lift = ((promo_row["avg_weekly_sales"] - non_row["avg_weekly_sales"]) / non_row["avg_weekly_sales"]) * 100.0
                return f"Weeks with active promotional markdowns averaged **${promo_row['avg_weekly_sales']:,.2f}** versus **${non_row['avg_weekly_sales']:,.2f}** without markdowns, providing a **+{lift:.2f}% promotional lift**."

        if template_type == "store_types":
            return f"**Type {row0['store_type']}** supercenters lead overall chain volume, contributing **${row0['total_sales']:,.2f}** across {row0['num_stores']} stores."

        if template_type == "global_summary":
            return f"The analytical database tracks **{row0['total_stores']} stores** and **{row0['total_departments']} departments**, totaling **${row0['total_sales']:,.2f}** in total sales and **${row0['avg_weekly_sales']:,.2f}** average weekly sales."

        return "Analytical query executed successfully against the SQLite star schema."
