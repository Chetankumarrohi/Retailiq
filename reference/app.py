"""
RetailIQ App - run with:  streamlit run app.py
Needs: pip install streamlit plotly anthropic
Needs ANTHROPIC_API_KEY set in environment for the chat tab.
"""
import streamlit as st, sqlite3, pandas as pd, plotly.express as px
from agent import ask_agent, forecast_tool

st.set_page_config(page_title="RetailIQ", layout="wide")
con = sqlite3.connect("retailiq.db")

tab1, tab2, tab3 = st.tabs(["Executive Dashboard", "Forecast Explorer", "Business Assistant"])

with tab1:
    st.header("Executive Dashboard")
    by_store = pd.read_sql("""SELECT s.store_id, s.store_type, SUM(f.weekly_sales) sales
                               FROM fact_sales f JOIN dim_store s ON f.store_id=s.store_id
                               GROUP BY s.store_id ORDER BY sales DESC""", con)
    by_dept = pd.read_sql("SELECT dept_id, SUM(weekly_sales) sales FROM fact_sales GROUP BY dept_id ORDER BY sales DESC LIMIT 15", con)
    trend = pd.read_sql("""SELECT d.year||'-'||printf('%02d',d.month) ym, SUM(f.weekly_sales) sales
                            FROM fact_sales f JOIN dim_date d ON f.date_id=d.date_id GROUP BY ym ORDER BY ym""", con)
    promo = pd.read_sql("""SELECT CASE WHEN (MarkDown1+MarkDown2+MarkDown3+MarkDown4+MarkDown5)>0
                            THEN 'Promo' ELSE 'No Promo' END period, AVG(weekly_sales) avg_sales
                            FROM fact_sales GROUP BY period""", con)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"${by_store['sales'].sum():,.0f}")
    c2.metric("Stores", len(by_store))
    c3.metric("Avg Weekly Sales / Store-Dept", f"${trend['sales'].mean()/len(by_store):,.0f}")

    st.plotly_chart(px.line(trend, x="ym", y="sales", title="Revenue Trend (Monthly)"), use_container_width=True)
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(by_store, x="store_id", y="sales", color="store_type", title="Store Ranking"), use_container_width=True)
    col2.plotly_chart(px.bar(by_dept, x="dept_id", y="sales", title="Top 15 Departments"), use_container_width=True)
    st.plotly_chart(px.bar(promo, x="period", y="avg_sales", title="Promotional Effectiveness"), use_container_width=True)

    st.subheader("Drill-through: product (dept) detail")
    dept_pick = st.selectbox("Choose department", sorted(pd.read_sql("SELECT DISTINCT dept_id FROM fact_sales", con)["dept_id"]))
    detail = pd.read_sql(f"""SELECT d.year, d.month, SUM(f.weekly_sales) sales FROM fact_sales f
                              JOIN dim_date d ON f.date_id=d.date_id WHERE dept_id={dept_pick}
                              GROUP BY d.year, d.month ORDER BY d.year, d.month""", con)
    st.plotly_chart(px.line(detail, x="month", y="sales", color="year", title=f"Dept {dept_pick} monthly sales by year"), use_container_width=True)

with tab2:
    st.header("Forecast Explorer")
    store_pick = st.number_input("Store ID", 1, 45, 1)
    dept_pick2 = st.number_input("Dept ID", 1, 99, 1)
    horizon = st.slider("Horizon (weeks)", 1, 12, 4)
    if st.button("Run forecast"):
        result = forecast_tool(int(store_pick), int(dept_pick2), int(horizon))
        st.success(result)

with tab3:
    st.header("Business Assistant (Agent)")
    st.caption("Ask about sales, forecasts, or policy. Reasoning trace is shown below the answer.")
    q = st.text_input("Your question")
    if st.button("Ask") and q:
        with st.spinner("Thinking..."):
            answer, trace = ask_agent(q)
        st.markdown("### Answer")
        st.write(answer)
        st.markdown("### Reasoning trace (tool selection)")
        for step in trace:
            st.json(step)
