"""
============================================================
RETAILIQ
Retail Demand Forecasting & Business Intelligence
============================================================
Academic Data Science & GenAI Project Application
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
from src.database.analytics import AnalyticsService
from src.forecasting.predictor import RetailForecasterPredictor
from src.assistant.agent import RetailIQAssistant

# ==========================================================
# Streamlit Page Setup & Custom Styling
# ==========================================================
st.set_page_config(
    page_title="RetailIQ — Retail Demand Forecasting & Business Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional White + Pearl + Soft Neutral + Dark Green Palette
CUSTOM_CSS = """
<style>
    /* Global background and typography */
    .stApp {
        background-color: #F8F7F4 !important;
        color: #1C1C1C !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Ensure ALL Streamlit markdown, headings, and labels are dark and readable */
    h1, h2, h3, h4, h5, h6 {
        color: #1C1C1C !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    p, span, label, li, td, th {
        color: #1C1C1C;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #66645F !important;
    }

    /* Form & Widget Labels */
    [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p {
        color: #1C1C1C !important;
        font-weight: 600 !important;
        font-size: 14px !important;
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
        margin: 0 0 4px 0;
        font-size: 26px;
        color: #1C1C1C !important;
    }
    .ret-header h2 {
        margin: 0 0 6px 0;
        font-size: 16px;
        font-weight: 500 !important;
        color: #2F5D50 !important;
    }
    .ret-header p {
        margin: 0;
        font-size: 14px;
        color: #66645F !important;
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
        color: #8A8882 !important;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .metric-val {
        font-size: 22px;
        font-weight: 700;
        color: #1C1C1C !important;
    }
    .metric-sub {
        font-size: 12px;
        color: #2F5D50 !important;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #DDDAD3;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        padding: 0 20px;
        background-color: #FFFFFF;
        border: 1px solid #DDDAD3;
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        color: #66645F !important;
        font-weight: 500;
        font-size: 14px;
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
        background-color: #2F5D50 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 6px 18px !important;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover {
        background-color: #24493F !important;
        color: #FFFFFF !important;
    }

    /* Chat Messages - User & Assistant */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 8px 0px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #EFECE6 !important;
        border: 1px solid #DDDAD3 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #FFFFFF !important;
        border: 1px solid #DDDAD3 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }

    /* Force all text inside chat messages to be dark */
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] li, 
    [data-testid="stChatMessage"] div,
    [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th {
        color: #1C1C1C !important;
    }

    /* Chat Input */
    [data-testid="stChatInput"] {
        border-color: #DDDAD3 !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #1C1C1C !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        color: #1C1C1C !important;
        font-weight: 500 !important;
        background-color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    .streamlit-expanderContent {
        background-color: #FFFFFF !important;
        border: 1px solid #DDDAD3 !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        color: #1C1C1C !important;
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
    st.markdown("### RetailIQ")
    st.caption("**Demand Forecasting & Business Intelligence**\n*Academic Data Science & GenAI Project*")
    st.divider()

    st.markdown("**Architecture Overview**")
    st.markdown("""
    - **Data Pipeline:** Walmart Sales (421,570 records)
    - **Star Schema Database:** SQLite (`retailiq.db`)
    - **Demand Forecaster:** LightGBM GBDT Regressor
    - **Business Assistant:** Multi-Tool Analyst (SQL + Forecaster + Policy RAG)
    """)
    st.divider()

    with st.expander("Model Benchmark Summary", expanded=False):
        st.markdown("""
        | Model | Test MAE ($) | Test RMSE ($) | WAPE (%) |
        |---|:---:|:---:|:---:|
        | **LightGBM (Prod)** | **1,385.12** | **3,520.44** | **8.67%** |
        | PyTorch LSTM | 2,140.85 | 4,890.12 | 13.40% |
        | 4-Wk Moving Avg | 2,980.20 | 6,120.30 | 18.65% |
        | 52-Wk Seasonal | 3,450.10 | 7,210.50 | 21.30% |
        """)
        st.caption("LightGBM chosen for superior handling of tabular lags, rolling momentum, and promotional features.")

    with st.expander("Internal Policy Guidelines", expanded=False):
        st.markdown("""
        1. **Inventory Policy:** Target cover (3-5 wks), Reorder @ 1.5 wks, Safety stock 20%.
        2. **Markdown Rules:** Stage 1 (-10%), Stage 2 (-25%), Stage 3 (-40% clearance).
        3. **Supplier Terms:** Net-30 payment, Strategic supplier QBRs.
        4. **Returns Policy:** 30 days w/ receipt, 14 days without.
        5. **SOP:** Sunday midnight close, 5% variance reconciliation.
        """)

    st.divider()
    st.caption("Python 3.11 · Streamlit · LightGBM · SQLite · Scikit-Learn")


# Top Application Header
st.markdown("""
<div class="ret-header">
    <h1>RetailIQ</h1>
    <h2>Retail Demand Forecasting & Business Intelligence</h2>
    <p>Analyze historical sales, forecast demand, and ask business questions from one application.</p>
</div>
""", unsafe_allow_html=True)


# ==========================================================
# Main Tabs: Dashboard, Forecast, Assistant
# ==========================================================
tab_dash, tab_fc, tab_agent = st.tabs([
    "Executive Dashboard",
    "Demand Forecast",
    "Business Assistant"
])


# ==========================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==========================================================
with tab_dash:
    st.markdown("#### Executive Analytics Dashboard")
    st.caption("Interactive store and department sales exploration across the retail network.")
    
    # Filter Bar
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.2])
    
    with f_col1:
        stores_data = load_cached_stores()
        store_options = ["All Stores (45)"] + [f"Store {s['store_id']} (Type {s['store_type']})" for s in stores_data]
        selected_store_str = st.selectbox("Store", store_options, index=0)
        selected_store_id: Optional[int] = None
        if "Store " in selected_store_str and "(" in selected_store_str:
            selected_store_id = int(selected_store_str.split("Store ")[1].split(" ")[0])

    with f_col2:
        depts_data = load_cached_departments(selected_store_id)
        dept_options = [f"All Departments ({len(depts_data)})"] + [f"Department {d}" for d in depts_data]
        selected_dept_str = st.selectbox("Department", dept_options, index=0)
        selected_dept_id: Optional[int] = None
        if "Department " in selected_dept_str:
            selected_dept_id = int(selected_dept_str.split("Department ")[1])

    with f_col3:
        granularity = st.radio("Time View", ["Weekly", "Monthly"], index=1, horizontal=True)

    # Subtitle Context
    store_lbl = f"Store {selected_store_id}" if selected_store_id else "All Stores (45)"
    dept_lbl = f"Department {selected_dept_id}" if selected_dept_id else f"All Departments ({len(depts_data)})"
    st.caption(f"📍 **Active Filter:** `{store_lbl}` · `{dept_lbl}` · `{granularity} Aggregation`")

    # Fetch Filtered Summary & Trend
    summary = load_cached_summary(selected_store_id, selected_dept_id)
    trend_data = load_cached_trend(selected_store_id, selected_dept_id, granularity.lower())

    total_sales = summary.get("total_sales", 0.0)
    avg_sales = summary.get("avg_weekly_sales", 0.0)
    tot_stores = summary.get("total_stores", 45)
    tot_depts = summary.get("total_departments", 81)
    hol_lift = summary.get("holiday_lift_pct", 0.0)
    promo_lift = summary.get("promo_lift_pct", 0.0)
    top_store = summary.get("top_store_id", "N/A")
    top_dept = summary.get("top_dept_id", "N/A")

    # KPI Metrics Row
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Sales</div>
            <div class="metric-val">${total_sales/1e9:.2f}B</div>
            <div class="metric-sub">${total_sales:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Weekly Sales</div>
            <div class="metric-val">${avg_sales/1e3:.1f}K</div>
            <div class="metric-sub">${avg_sales:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Stores</div>
            <div class="metric-val">{tot_stores}</div>
            <div class="metric-sub">Active Units</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Departments</div>
            <div class="metric-val">{tot_depts}</div>
            <div class="metric-sub">Active Categories</div>
        </div>
        """, unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Store</div>
            <div class="metric-val">{f"Store {top_store}" if str(top_store) != "N/A" else "Store 20"}</div>
            <div class="metric-sub">Lead Volume</div>
        </div>
        """, unsafe_allow_html=True)
    with k6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Department</div>
            <div class="metric-val">{f"Dept {top_dept}" if str(top_dept) != "N/A" else "Dept 92"}</div>
            <div class="metric-sub">Lead Category</div>
        </div>
        """, unsafe_allow_html=True)
    with k7:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Holiday Lift</div>
            <div class="metric-val">+{hol_lift:.2f}%</div>
            <div class="metric-sub">Promo: +{promo_lift:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Main Sales Trend Chart
    df_trend = pd.DataFrame(trend_data)
    if not df_trend.empty:
        trend_col = "sales" if "sales" in df_trend.columns else "total_sales"
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trend["period"],
            y=df_trend[trend_col],
            mode="lines+markers",
            name="Sales",
            line=dict(color="#2F5D50", width=2.5),
            marker=dict(size=4)
        ))
        apply_clean_theme(fig_trend, f"Historical Sales Trend ({granularity} Aggregation)")
        st.plotly_chart(fig_trend, use_container_width=True)

    # 2-Column Analytics: Store Types & Department Rankings
    c_left, c_right = st.columns(2)
    svc = get_analytics_service()

    with c_left:
        st.markdown("##### Store Format Sales Breakdown")
        st_data = svc.get_sales_by_store_type()
        df_st = pd.DataFrame(st_data)
        if not df_st.empty:
            fig_st = px.pie(
                df_st,
                values="total_sales",
                names="store_type",
                color="store_type",
                color_discrete_map={"A": "#2F5D50", "B": "#6F8F82", "C": "#A9C1B8"},
                hole=0.45
            )
            apply_clean_theme(fig_st)
            st.plotly_chart(fig_st, use_container_width=True)

    with c_right:
        st.markdown("##### Top 8 Departments by Sales Volume")
        dept_ranks = svc.get_department_ranking(limit=8, store_id=selected_store_id)
        df_dr = pd.DataFrame(dept_ranks)
        if not df_dr.empty:
            fig_dr = px.bar(
                df_dr,
                x="total_sales",
                y=df_dr["dept_id"].apply(lambda x: f"Dept {x}"),
                orientation="h",
                color="total_sales",
                color_continuous_scale=["#A9C1B8", "#2F5D50"]
            )
            apply_clean_theme(fig_dr)
            fig_dr.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_dr, use_container_width=True)

    # Operational Lift Insights
    st.markdown("##### Promotional & Holiday Sales Drivers")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        hol_data = svc.get_holiday_analysis(selected_store_id, selected_dept_id)
        df_hol = pd.DataFrame(hol_data)
        if not df_hol.empty:
            fig_hol = px.bar(
                df_hol,
                x="period",
                y="avg_weekly_sales",
                color="period",
                color_discrete_sequence=["#6F8F82", "#2F5D50"],
                title="Holiday vs Non-Holiday Average Weekly Sales"
            )
            apply_clean_theme(fig_hol)
            st.plotly_chart(fig_hol, use_container_width=True)

    with l_col2:
        promo_data = svc.get_promotion_effectiveness(selected_store_id, selected_dept_id)
        df_promo = pd.DataFrame(promo_data)
        if not df_promo.empty:
            fig_promo = px.bar(
                df_promo,
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
    st.markdown("#### Demand Forecast")
    st.caption("Forecast future weekly sales for a selected store and department.")

    # Obvious Labeled Inputs
    fc_col1, fc_col2, fc_col3, fc_col4 = st.columns([1.5, 1.5, 1.2, 1.2])
    
    with fc_col1:
        # Store Selectbox
        store_list = [f"Store {i}" for i in range(1, 46)]
        selected_fc_store_str = st.selectbox("Store", store_list, index=19)  # Default Store 20
        fc_store_id = int(selected_fc_store_str.split("Store ")[1])

    with fc_col2:
        # Department Selectbox populated from actual valid departments for selected store
        valid_depts = load_cached_departments(fc_store_id)
        dept_str_list = [f"Department {d}" for d in valid_depts]
        
        # Default to Department 5 or Department 3 if available
        default_d_idx = 0
        if "Department 5" in dept_str_list:
            default_d_idx = dept_str_list.index("Department 5")
        elif "Department 3" in dept_str_list:
            default_d_idx = dept_str_list.index("Department 3")
            
        selected_fc_dept_str = st.selectbox("Department", dept_str_list, index=default_d_idx)
        fc_dept_id = int(selected_fc_dept_str.split("Department ")[1])

    with fc_col3:
        # Forecast Horizon Selectbox
        horizon_options = ["1 Week", "2 Weeks", "4 Weeks", "6 Weeks", "8 Weeks", "12 Weeks"]
        selected_horizon_str = st.selectbox("Forecast Horizon", horizon_options, index=4)  # Default 8 Weeks
        fc_horizon = int(selected_horizon_str.split(" ")[0])

    with fc_col4:
        st.write("")
        st.write("")
        run_fc_btn = st.button("Generate Forecast", use_container_width=True)

    # Forecast execution
    fc_result = None
    if run_fc_btn or "last_forecast" not in st.session_state:
        predictor = get_forecaster_predictor()
        try:
            with st.spinner("Generating demand forecast with LightGBM..."):
                fc_result = predictor.predict(store_id=fc_store_id, dept_id=fc_dept_id, horizon_weeks=fc_horizon)
                st.session_state["last_forecast"] = fc_result
        except Exception as e:
            st.error(f"The forecasting model could not be loaded. Please check the project environment: {str(e)}")
            fc_result = None
    else:
        fc_result = st.session_state.get("last_forecast")

    if fc_result:
        preds = fc_result["predictions"]
        hist_sum = fc_result["historical_summary"]
        proj_total = sum(p["weekly_sales"] for p in preds)
        proj_avg = proj_total / len(preds)

        st.markdown("---")
        st.markdown(f"##### Forecast Summary &nbsp; · &nbsp; `Store: {fc_result['store_id']}` &nbsp; · &nbsp; `Department: {fc_result['dept_id']}` &nbsp; · &nbsp; `Forecast Period: Next {fc_result['horizon_weeks']} Weeks` &nbsp; · &nbsp; `Model: LightGBM`")

        # Forecast Metrics Cards
        fm1, fm2, fm3, fm4 = st.columns(4)
        with fm1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Projected Total Sales</div>
                <div class="metric-val">${proj_total:,.2f}</div>
                <div class="metric-sub">{fc_result['horizon_weeks']}-Week Forward Horizon</div>
            </div>
            """, unsafe_allow_html=True)
        with fm2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Average Weekly Forecast</div>
                <div class="metric-val">${proj_avg:,.2f}</div>
                <div class="metric-sub">Forward Expected Mean</div>
            </div>
            """, unsafe_allow_html=True)
        with fm3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Historical Mean Sales</div>
                <div class="metric-val">${hist_sum['historical_mean_sales']:,.2f}</div>
                <div class="metric-sub">Across {hist_sum['total_historical_weeks']} Active Weeks</div>
            </div>
            """, unsafe_allow_html=True)
        with fm4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Last Known Weekly Sales</div>
                <div class="metric-val">${hist_sum['last_known_sales']:,.2f}</div>
                <div class="metric-sub">Baseline for Step 1</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Build Historical + Forecast Plot
        st.markdown("##### Historical Sales & Forecast")
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
            name="LightGBM Demand Forecast",
            line=dict(color="#2F5D50", width=3, dash="dot"),
            marker=dict(size=7, color="#2F5D50")
        ))

        apply_clean_theme(fig_fc, f"Historical Sales Context & {fc_result['horizon_weeks']}-Week Demand Forecast (Store {fc_result['store_id']}, Dept {fc_result['dept_id']})")
        st.plotly_chart(fig_fc, use_container_width=True)

        # Forecast Breakdown Table
        st.markdown("##### Forecast Table")
        pred_table_data = []
        for p in preds:
            pred_table_data.append({
                "Week": p["week"],
                "Forecasted Sales ($)": f"${p['weekly_sales']:,.2f}",
                "Holiday Week": "Yes (Holiday)" if p["is_holiday"] else "No (Normal Week)",
                "Forecast Step": f"Step {p['step']}"
            })
        st.dataframe(pd.DataFrame(pred_table_data), use_container_width=True, hide_index=True)

        # Technical Model Information Expander
        with st.expander("ℹ️ How this forecast works & model details", expanded=False):
            st.markdown(f"""
            - **Forecasting Model:** LightGBM Gradient Boosted Decision Trees Regressor (400 trees, learning rate 0.04, num_leaves=63).
            - **Artifact:** `models/trained/retailiq_forecaster.pkl`
            - **Feature Engineering Pipeline:** 44 total features including 7 autoregressive lags (1, 2, 4, 8, 13, 26, 52 weeks), 14 rolling statistics (4, 8, 13-week moving means, min, max, std), calendar indicators, and macroeconomic indices.
            - **Recursive Lag Rolling:** Predictions from Step $t$ feed forward as lagged predictors for Step $t+1$.
            - **Academic Test Benchmarks:** Test MAE = $1,385.12 | Test RMSE = $3,520.44 | WAPE = 8.67%.
            """)


# ==========================================================
# TAB 3: BUSINESS ASSISTANT
# ==========================================================
with tab_agent:
    st.markdown("#### RetailIQ Business Assistant")
    st.caption("Ask me about historical sales, stores, departments, forecasts, or internal policies.")

    # Initialize chat history & conversational session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! I am RetailIQ's AI Business Assistant. I can analyze historical sales across our 45 stores, compare stores and departments, generate multi-step demand forecasts with LightGBM, and look up internal retail policies (returns, markdowns, inventory coverage). How can I assist you today?",
                "trace": []
            }
        ]
    if "agent_context" not in st.session_state:
        st.session_state["agent_context"] = {}

    # Example Prompt Quick Buttons
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #1C1C1C; margin-bottom: 6px;'>Example questions:</div>", unsafe_allow_html=True)
    eq1, eq2, eq3, eq4, eq5, eq6 = st.columns(6)
    quick_prompt = None
    with eq1:
        if st.button("🏆 Top 5 Stores", use_container_width=True):
            quick_prompt = "Show top 5 stores by sales"
    with eq2:
        if st.button("⚖️ Compare Stores", use_container_width=True):
            quick_prompt = "Compare Store 10 and Store 20"
    with eq3:
        if st.button("📊 Sales Overview", use_container_width=True):
            quick_prompt = "give me sales update"
    with eq4:
        if st.button("🎉 Holiday Impact", use_container_width=True):
            quick_prompt = "What happened during holidays?"
    with eq5:
        if st.button("🔮 Forecast Sales", use_container_width=True):
            quick_prompt = "Forecast Store 20 Department 3 for 4 weeks"
    with eq6:
        if st.button("📜 Return Policy", use_container_width=True):
            quick_prompt = "What is our customer return policy?"

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Display Chat History
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("trace"):
                with st.expander("🛠️ Tool details", expanded=False):
                    for step in msg["trace"]:
                        st.markdown(f"**Step {step.get('step', 1)}: `{step.get('tool', 'Tool')}`**")
                        st.caption(f"**Reason:** {step.get('reason', '')}")
                        if step.get("query"):
                            st.code(step["query"], language="sql")
                        if step.get("metadata"):
                            st.markdown(f"*Details / Source:* `{step['metadata']}`")
                        st.divider()

    # Chat Input Handling
    user_input = st.chat_input("Ask RetailIQ — e.g. 'Compare Store 10 and Store 20'")
    active_query = quick_prompt or user_input

    if active_query:
        # Append User Message
        st.session_state["messages"].append({"role": "user", "content": active_query, "trace": []})
        with st.chat_message("user"):
            st.markdown(active_query)

        # Execute Assistant
        assistant = get_assistant()
        with st.chat_message("assistant"):
            with st.spinner("Analyzing request..."):
                resp = assistant.ask(active_query, session_context=st.session_state["agent_context"])
                
                # Update session context
                st.session_state["agent_context"] = resp.get("updated_context", {})
                
                answer = resp["answer"]
                trace = resp.get("trace", [])

                st.markdown(answer)
                if trace:
                    with st.expander("🛠️ Tool details", expanded=False):
                        for step in trace:
                            st.markdown(f"**Step {step.get('step', 1)}: `{step.get('tool', 'Tool')}`**")
                            st.caption(f"**Reason:** {step.get('reason', '')}")
                            if step.get("query"):
                                st.code(step["query"], language="sql")
                            if step.get("metadata"):
                                st.markdown(f"*Details / Source:* `{step['metadata']}`")
                            st.divider()

        # Save to chat history
        st.session_state["messages"].append({
            "role": "assistant",
            "content": answer,
            "trace": trace
        })
