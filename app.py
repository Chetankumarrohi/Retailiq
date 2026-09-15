"""
============================================================
RETAILIQ
Demand Forecasting and Multi-Tool Business Assistant
============================================================
Academic Project Application
Entry Point: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project imports
from src.database import AnalyticsService
from src.forecasting.predictor import RetailForecasterPredictor
from src.assistant import RetailIQAssistant

# ==========================================================
# Streamlit Page Setup & Custom Styling
# ==========================================================
st.set_page_config(
    page_title="RetailIQ — Demand Forecasting & Multi-Tool Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional White + Pearl + Soft Neutral + Dark Green Palette
CUSTOM_CSS = """
<style>
    /* Global background and typography */
    .stApp {
        background-color: #F8F7F4;
        color: #1C1C1C;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #1C1C1C !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    
    /* Top Header Banner */
    .ret-header {
        background-color: #FFFFFF;
        border: 1px solid #DDDAD3;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .ret-header h1 {
        margin: 0 0 6px 0;
        font-size: 24px;
        color: #1C1C1C;
    }
    .ret-header p {
        margin: 0;
        font-size: 14px;
        color: #66645F;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #DDDAD3;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8A8882;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .metric-val {
        font-size: 22px;
        font-weight: 700;
        color: #1C1C1C;
    }
    .metric-sub {
        font-size: 12px;
        color: #2F5D50;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #DDDAD3;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        padding: 0 18px;
        background-color: #FFFFFF;
        border: 1px solid #DDDAD3;
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        color: #66645F;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F8F7F4 !important;
        border-color: #2F5D50 !important;
        border-top: 3px solid #2F5D50 !important;
        color: #1C1C1C !important;
        font-weight: 600 !important;
    }

    /* Primary Accent Buttons */
    .stButton>button {
        background-color: #2F5D50;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        padding: 6px 18px;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover {
        background-color: #24493F;
        color: #FFFFFF;
    }

    /* Tool Trace Card */
    .trace-card {
        background-color: #F3F1EC;
        border-left: 3px solid #2F5D50;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        font-size: 13px;
        margin-top: 10px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================================
# Cached Resources & Data Services
# ==========================================================
@st.cache_resource
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()

@st.cache_resource
def get_forecaster_predictor() -> RetailForecasterPredictor:
    return RetailForecasterPredictor()

@st.cache_resource
def get_assistant() -> RetailIQAssistant:
    return RetailIQAssistant()

@st.cache_data
def load_cached_summary(store_id: Optional[int], dept_id: Optional[int]) -> Dict[str, Any]:
    svc = get_analytics_service()
    return svc.get_summary(store_id=store_id, dept_id=dept_id)

@st.cache_data
def load_cached_trend(store_id: Optional[int], dept_id: Optional[int], granularity: str) -> List[Dict[str, Any]]:
    svc = get_analytics_service()
    return svc.get_sales_trend(store_id=store_id, dept_id=dept_id, granularity=granularity)

@st.cache_data
def load_cached_stores() -> List[Dict[str, Any]]:
    svc = get_analytics_service()
    return svc.get_stores_list()

@st.cache_data
def load_cached_departments(store_id: Optional[int]) -> List[int]:
    svc = get_analytics_service()
    return svc.get_departments_list(store_id=store_id)


# Clean Plotly Layout Theme Helper
def apply_clean_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#1C1C1C", family="Helvetica, Arial, sans-serif")),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=40, r=20, t=45, b=35),
        font=dict(family="Helvetica, Arial, sans-serif", size=11, color="#66645F"),
        xaxis=dict(showgrid=True, gridcolor="#F3F1EC", linecolor="#DDDAD3", tickfont=dict(color="#66645F")),
        yaxis=dict(showgrid=True, gridcolor="#F3F1EC", linecolor="#DDDAD3", tickfont=dict(color="#66645F")),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#DDDAD3", borderwidth=1)
    )
    return fig


# ==========================================================
# Sidebar — Project Metadata & Model Benchmarks
# ==========================================================
with st.sidebar:
    st.markdown("### 🛒 RetailIQ")
    st.caption("**Demand Forecasting & AI Assistant**\n*Academic Data Science & GenAI Project*")
    st.divider()

    st.markdown("**Architecture Overview**")
    st.markdown("""
    - **Data Pipeline:** Walmart Sales (421,570 rows)
    - **Star Schema:** SQLite (`retailiq.db`)
    - **Production Model:** LightGBM Regressor
    - **AI Assistant:** Multi-Tool Orchestrator (SQL + Forecasting + Policy RAG)
    """)
    st.divider()

    with st.expander("📈 Model Comparison Benchmark", expanded=False):
        st.markdown("""
        | Model | Test MAE | Test RMSE | WAPE |
        |---|:---:|:---:|:---:|
        | **LightGBM (Prod)** | **1,385.12** | **3,520.44** | **8.67%** |
        | PyTorch LSTM | 2,140.85 | 4,890.12 | 13.40% |
        | 4-Wk Moving Avg | 2,980.20 | 6,120.30 | 18.65% |
        """)
        st.caption("LightGBM chosen for superior handling of tabular economic lags and non-linear interactions.")

    with st.expander("📚 Knowledge Base / Policies", expanded=False):
        st.markdown("""
        1. **Inventory Policy:** Target cover (3-5 wks), Reorder @ 1.5 wks, Safety stock 20%.
        2. **Markdown Rules:** Stage 1 (-10%), Stage 2 (-25%), Stage 3 (-40% clearance).
        3. **Supplier Terms:** Net-30 payment, Strategic supplier QBRs.
        4. **Returns Policy:** 30 days w/ receipt, 14 days without.
        5. **SOP:** Sunday midnight close, 5% variance reconciliation.
        """)

    st.divider()
    st.caption("Developed with Python, Streamlit, LightGBM, SQLite, Scikit-Learn.")


# Top Application Header
st.markdown("""
<div class="ret-header">
    <h1>RetailIQ — Commercial Intelligence & Demand Forecasting</h1>
    <p>Integrated Multi-Store Retail Analytics, Recursive LightGBM Forecasting, and Multi-Tool Business Assistant</p>
</div>
""", unsafe_allow_html=True)


# ==========================================================
# Main Tabs: Dashboard, Forecast, Assistant
# ==========================================================
tab_dash, tab_fc, tab_agent = st.tabs([
    "📊 Executive Dashboard",
    "🔮 Demand Forecast",
    "💬 Business Assistant"
])


# ==========================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==========================================================
with tab_dash:
    st.markdown("#### Filter Analytics")
    
    # Filter Bar
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.2])
    
    with f_col1:
        stores_data = load_cached_stores()
        store_options = ["All Stores (45)"] + [f"Store {s['store_id']} (Type {s['store_type']})" for s in stores_data]
        selected_store_str = st.selectbox("Select Store", store_options, index=0)
        selected_store_id: Optional[int] = None
        if "Store " in selected_store_str and "(" in selected_store_str:
            selected_store_id = int(selected_store_str.split("Store ")[1].split(" ")[0])

    with f_col2:
        depts_data = load_cached_departments(selected_store_id)
        dept_options = [f"All Departments ({len(depts_data)})"] + [f"Department {d}" for d in depts_data]
        selected_dept_str = st.selectbox("Select Department", dept_options, index=0)
        selected_dept_id: Optional[int] = None
        if "Department " in selected_dept_str:
            selected_dept_id = int(selected_dept_str.split("Department ")[1])

    with f_col3:
        granularity = st.radio("Time Aggregation", ["Weekly", "Monthly"], index=1, horizontal=True)

    # Subtitle Context
    store_lbl = f"Store {selected_store_id}" if selected_store_id else "All Stores (45)"
    dept_lbl = f"Department {selected_dept_id}" if selected_dept_id else "All Departments"
    st.caption(f"📍 **Viewing Context:** `{store_lbl}` · `{dept_lbl}` · `{granularity} View`")

    # Fetch Filtered Summary & Trend
    summary = load_cached_summary(selected_store_id, selected_dept_id)
    trend_data = load_cached_trend(selected_store_id, selected_dept_id, granularity.lower())

    total_sales = summary.get("total_sales", 0.0)
    avg_sales = summary.get("avg_weekly_sales", 0.0)
    tot_stores = summary.get("total_stores", 45)
    tot_depts = summary.get("total_departments", 81)
    hol_lift = summary.get("holiday_lift_pct", 0.0)
    promo_lift = summary.get("promotion_lift_pct", 0.0)
    top_store = summary.get("top_store_id", 20)
    top_dept = summary.get("top_dept_id", 92)

    # Format Sales Numbers Cleanly ($B / $M / $K)
    if total_sales >= 1e9:
        sales_str = f"${total_sales/1e9:.2f}B"
    elif total_sales >= 1e6:
        sales_str = f"${total_sales/1e6:.2f}M"
    else:
        sales_str = f"${total_sales:,.0f}"

    # KPI Cards Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Sales</div>
            <div class="metric-val">{sales_str}</div>
            <div class="metric-sub">{tot_stores} Stores · {tot_depts} Depts</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average Weekly Sales</div>
            <div class="metric-val">${avg_sales:,.2f}</div>
            <div class="metric-sub">Per active store-dept-week</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        leader_title = f"Selected: Store {selected_store_id}" if selected_store_id else f"Top Store: Store {top_store}"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Store Leadership</div>
            <div class="metric-val">{leader_title}</div>
            <div class="metric-sub">Top Category: Dept {top_dept}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Holiday / Promo Lift</div>
            <div class="metric-val">{'+' if hol_lift >= 0 else ''}{hol_lift:.2f}%</div>
            <div class="metric-sub">Promo Lift: {'+' if promo_lift >= 0 else ''}{promo_lift:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Charts Row 1: Sales Trend
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        fig_trend = px.line(
            trend_df,
            x="period",
            y="sales",
            title=f"Sales Trend ({granularity} Aggregation)",
            markers=True if granularity == "Monthly" else False
        )
        fig_trend.update_traces(line=dict(color="#2F5D50", width=2.5), marker=dict(size=6, color="#2F5D50"))
        apply_clean_theme(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

    # Charts Row 2: Store Ranking & Department Ranking
    c_left, c_right = st.columns(2)
    svc = get_analytics_service()

    with c_left:
        store_rank = svc.get_store_ranking(limit=10, dept_id=selected_dept_id)
        if store_rank:
            sr_df = pd.DataFrame(store_rank)
            sr_df["store_label"] = "Store " + sr_df["store_id"].astype(str)
            fig_store = px.bar(
                sr_df,
                x="store_label",
                y="total_sales",
                color="store_type",
                color_discrete_map={"A": "#2F5D50", "B": "#6F8F82", "C": "#A9C1B8"},
                title="Top 10 Stores Ranked by Total Sales"
            )
            apply_clean_theme(fig_store)
            st.plotly_chart(fig_store, use_container_width=True)

    with c_right:
        dept_rank = svc.get_department_ranking(limit=10, store_id=selected_store_id)
        if dept_rank:
            dr_df = pd.DataFrame(dept_rank)
            dr_df["dept_label"] = "Dept " + dr_df["dept_id"].astype(str)
            fig_dept = px.bar(
                dr_df,
                x="dept_label",
                y="total_sales",
                title="Top 10 Departments Ranked by Total Sales"
            )
            fig_dept.update_traces(marker_color="#6F8F82")
            apply_clean_theme(fig_dept)
            st.plotly_chart(fig_dept, use_container_width=True)

    # Charts Row 3: Holiday & Promotion Impact
    h_left, h_right = st.columns(2)
    with h_left:
        hol_data = svc.get_holiday_analysis(store_id=selected_store_id, dept_id=selected_dept_id)
        if hol_data:
            hol_df = pd.DataFrame(hol_data)
            fig_hol = px.bar(
                hol_df,
                x="period",
                y="avg_weekly_sales",
                color="period",
                color_discrete_sequence=["#6F8F82", "#2F5D50"],
                title="Holiday vs. Non-Holiday Average Weekly Sales"
            )
            apply_clean_theme(fig_hol)
            st.plotly_chart(fig_hol, use_container_width=True)

    with h_right:
        promo_data = svc.get_promotion_effectiveness(store_id=selected_store_id, dept_id=selected_dept_id)
        if promo_data:
            promo_df = pd.DataFrame(promo_data)
            fig_promo = px.bar(
                promo_df,
                x="period",
                y="avg_weekly_sales",
                color="period",
                color_discrete_sequence=["#A9C1B8", "#2F5D50"],
                title="Promotional Markdown Impact on Weekly Sales"
            )
            apply_clean_theme(fig_promo)
            st.plotly_chart(fig_promo, use_container_width=True)


# ==========================================================
# TAB 2: DEMAND FORECAST
# ==========================================================
with tab_fc:
    st.markdown("#### Production Demand Forecasting Engine")
    st.caption("Generate recursive multi-step forecasts with the trained LightGBM Regressor.")

    fc_col1, fc_col2, fc_col3, fc_col4 = st.columns([1.5, 1.5, 1.2, 1.2])
    
    with fc_col1:
        fc_store = st.number_input("Store ID", min_value=1, max_value=45, value=20, step=1)
    with fc_col2:
        # Fetch valid depts for this store
        valid_depts = load_cached_departments(int(fc_store))
        default_dept = 3 if 3 in valid_depts else (valid_depts[0] if valid_depts else 1)
        fc_dept = st.selectbox("Department ID", valid_depts, index=valid_depts.index(default_dept) if default_dept in valid_depts else 0)
    with fc_col3:
        fc_horizon = st.selectbox("Horizon (Weeks)", [1, 2, 4, 6, 8, 12], index=2)
    with fc_col4:
        st.write("")
        st.write("")
        run_fc_btn = st.button("Generate Forecast", use_container_width=True)

    if run_fc_btn or "last_forecast" not in st.session_state:
        predictor = get_forecaster_predictor()
        try:
            fc_result = predictor.predict(store_id=int(fc_store), dept_id=int(fc_dept), horizon_weeks=int(fc_horizon))
            st.session_state["last_forecast"] = fc_result
        except Exception as e:
            st.error(f"Forecasting Error: {str(e)}")
            fc_result = None
    else:
        fc_result = st.session_state.get("last_forecast")

    if fc_result:
        preds = fc_result["predictions"]
        hist_sum = fc_result["historical_summary"]
        proj_total = sum(p["weekly_sales"] for p in preds)
        proj_avg = proj_total / len(preds)

        # Forecast Metrics Cards
        fm1, fm2, fm3, fm4 = st.columns(4)
        with fm1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Target Entity</div>
                <div class="metric-val">Store {fc_result['store_id']} · Dept {fc_result['dept_id']}</div>
                <div class="metric-sub">Horizon: {fc_result['horizon_weeks']} Weeks</div>
            </div>
            """, unsafe_allow_html=True)
        with fm2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Projected Total Sales</div>
                <div class="metric-val">${proj_total:,.2f}</div>
                <div class="metric-sub">Avg: ${proj_avg:,.2f}/week</div>
            </div>
            """, unsafe_allow_html=True)
        with fm3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Historical Mean Sales</div>
                <div class="metric-val">${hist_sum['historical_mean_sales']:,.2f}</div>
                <div class="metric-sub">Based on {hist_sum['total_historical_weeks']} active weeks</div>
            </div>
            """, unsafe_allow_html=True)
        with fm4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Production Model</div>
                <div class="metric-val">{fc_result['model_type']}</div>
                <div class="metric-sub">Artifact: retailiq_forecaster.pkl (v{fc_result['model_version']})</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Build Historical + Forecast Plot
        svc = get_analytics_service()
        with svc.get_connection() as conn:
            hist_df = pd.read_sql(f"""
            SELECT d.full_date AS date_str, f.weekly_sales
            FROM fact_sales f JOIN dim_date d ON f.date_id = d.date_id
            WHERE f.store_id = {fc_result['store_id']} AND f.dept_id = {fc_result['dept_id']}
            ORDER BY d.full_date ASC;
            """, conn)

        fig_fc = go.Figure()

        # Recent 30 historical weeks for context
        recent_hist = hist_df.tail(30)
        fig_fc.add_trace(go.Scatter(
            x=recent_hist["date_str"],
            y=recent_hist["weekly_sales"],
            mode="lines+markers",
            name="Historical Sales (Recent)",
            line=dict(color="#66645F", width=2),
            marker=dict(size=4)
        ))

        # Future forecast points
        fc_dates = [p["week"] for p in preds]
        fc_vals = [p["weekly_sales"] for p in preds]

        # Connect last history to first forecast
        if not recent_hist.empty:
            conn_x = [recent_hist["date_str"].iloc[-1]] + fc_dates
            conn_y = [recent_hist["weekly_sales"].iloc[-1]] + fc_vals
        else:
            conn_x = fc_dates
            conn_y = fc_vals

        fig_fc.add_trace(go.Scatter(
            x=conn_x,
            y=conn_y,
            mode="lines+markers",
            name="LightGBM Multi-Step Forecast",
            line=dict(color="#2F5D50", width=3, dash="dot"),
            marker=dict(size=7, color="#2F5D50")
        ))

        apply_clean_theme(fig_fc, f"Historical Sales Context & {fc_result['horizon_weeks']}-Week Demand Forecast (Store {fc_result['store_id']}, Dept {fc_result['dept_id']})")
        st.plotly_chart(fig_fc, use_container_width=True)

        # Forecast Breakdown Table
        st.markdown("##### Week-by-Week Forecast Schedule")
        pred_table_data = []
        for p in preds:
            pred_table_data.append({
                "Forecast Step": f"Step {p['step']}",
                "Target Week Date": p["week"],
                "Projected Weekly Sales ($)": f"${p['weekly_sales']:,.2f}",
                "Holiday Flag": "Holiday Week" if p["is_holiday"] else "Normal Week",
                "Model Assumption": p.get("assumptions", ["Macro continuity"])[0] if p.get("assumptions") else "Normal"
            })
        st.dataframe(pd.DataFrame(pred_table_data), use_container_width=True, hide_index=True)


# ==========================================================
# TAB 3: BUSINESS ASSISTANT
# ==========================================================
with tab_agent:
    st.markdown("#### Multi-Tool Business Assistant")
    st.caption("Ask natural questions spanning SQL Analytics, Demand Forecasting, Policy Documentation, or Multi-Tool combinations.")

    # Initialize chat history & conversational session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! I am RetailIQ's AI Business Assistant. I can analyze historical sales across our 45 stores, generate multi-step demand forecasts with LightGBM, and look up internal retail policies (returns, markdowns, inventory coverage). How can I assist you today?",
                "trace": []
            }
        ]
    if "agent_context" not in st.session_state:
        st.session_state["agent_context"] = {}

    # Example Prompt Quick Buttons
    st.markdown("**Try asking:**")
    eq1, eq2, eq3, eq4 = st.columns(4)
    quick_prompt = None
    with eq1:
        if st.button("🏆 Top 5 Stores by Sales", use_container_width=True):
            quick_prompt = "Show top 5 stores by sales"
    with eq2:
        if st.button("🔮 Forecast Store 20 Dept 3", use_container_width=True):
            quick_prompt = "Forecast Store 20 Department 3 for 4 weeks"
    with eq3:
        if st.button("📜 Customer Return Policy", use_container_width=True):
            quick_prompt = "What is our customer return policy?"
    with eq4:
        if st.button("⚡ Best Dept & Forecast", use_container_width=True):
            quick_prompt = "Which department performs best in Store 20 and forecast it for the next 4 weeks?"

    # Display Chat History
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("trace"):
                with st.expander("🛠️ Tool Execution Trace", expanded=False):
                    for step in msg["trace"]:
                        st.markdown(f"**Step {step.get('step', 1)}: `{step.get('tool', 'Tool')}`**")
                        st.caption(f"**Reason:** {step.get('reason', '')}")
                        if step.get("query"):
                            st.code(step["query"], language="sql")
                        if step.get("metadata"):
                            st.markdown(f"*Metadata / Source:* `{step['metadata']}`")
                        st.divider()

    # Chat Input Handling
    user_input = st.chat_input("Ask a question about sales, rankings, forecasting, or policies...")
    active_query = quick_prompt or user_input

    if active_query:
        # Append User Message
        st.session_state["messages"].append({"role": "user", "content": active_query, "trace": []})
        with st.chat_message("user"):
            st.markdown(active_query)

        # Execute Assistant
        assistant = get_assistant()
        with st.chat_message("assistant"):
            with st.spinner("Analyzing request and executing tools..."):
                resp = assistant.ask(active_query, session_context=st.session_state["agent_context"])
                
                # Update session context
                st.session_state["agent_context"] = resp.get("updated_context", {})
                
                answer = resp["answer"]
                trace = resp.get("trace", [])

                st.markdown(answer)
                if trace:
                    with st.expander("🛠️ Tool Execution Trace", expanded=True):
                        for step in trace:
                            st.markdown(f"**Step {step.get('step', 1)}: `{step.get('tool', 'Tool')}`**")
                            st.caption(f"**Reason:** {step.get('reason', '')}")
                            if step.get("query"):
                                st.code(step["query"], language="sql")
                            if step.get("metadata"):
                                st.markdown(f"*Metadata / Source:* `{step['metadata']}`")
                            st.divider()

        # Save to chat history
        st.session_state["messages"].append({
            "role": "assistant",
            "content": answer,
            "trace": trace
        })
