-- RetailIQ Analytical SQL Layer (SQLite Star Schema)
-- Tested and verified against retailiq.db

-- ==========================================================
-- 1. Total Chain Sales, Average Weekly Sales, and Active Spans
-- ==========================================================
SELECT 
    COUNT(*) AS total_records,
    ROUND(SUM(weekly_sales), 2) AS total_chain_revenue,
    ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales_per_dept_store,
    MIN(date_id) AS earliest_date_id,
    MAX(date_id) AS latest_date_id
FROM fact_sales;


-- ==========================================================
-- 2. Sales by Store with Size and Store Type Details
-- ==========================================================
SELECT 
    s.store_id,
    s.store_type,
    s.store_size,
    ROUND(SUM(f.weekly_sales), 2) AS total_sales,
    ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
    COUNT(DISTINCT f.dept_id) AS active_depts
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id, s.store_type, s.store_size
ORDER BY total_sales DESC;


-- ==========================================================
-- 3. Sales by Department (All Departments)
-- ==========================================================
SELECT 
    dept_id,
    ROUND(SUM(weekly_sales), 2) AS total_dept_sales,
    ROUND(AVG(weekly_sales), 2) AS avg_weekly_sales,
    COUNT(*) AS transaction_weeks
FROM fact_sales
GROUP BY dept_id
ORDER BY total_dept_sales DESC;


-- ==========================================================
-- 4. Monthly Revenue Trend
-- ==========================================================
SELECT 
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.weekly_sales), 2) AS total_monthly_sales,
    COUNT(DISTINCT f.store_id) AS active_stores
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- ==========================================================
-- 5. Year-over-Year (YoY) Sales Comparison by Month
-- ==========================================================
WITH monthly_revenue AS (
    SELECT 
        d.year,
        d.month,
        d.month_name,
        SUM(f.weekly_sales) AS monthly_sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month, d.month_name
)
SELECT 
    curr.year,
    curr.month,
    curr.month_name,
    ROUND(curr.monthly_sales, 2) AS current_year_sales,
    ROUND(prev.monthly_sales, 2) AS prior_year_sales,
    ROUND(curr.monthly_sales - prev.monthly_sales, 2) AS yoy_absolute_growth,
    ROUND(100.0 * (curr.monthly_sales - prev.monthly_sales) / NULLIF(prev.monthly_sales, 0), 2) AS yoy_growth_pct
FROM monthly_revenue curr
LEFT JOIN monthly_revenue prev 
    ON curr.month = prev.month AND curr.year = prev.year + 1
ORDER BY curr.year, curr.month;


-- ==========================================================
-- 6. Top 10 Stores Ranked by Revenue
-- ==========================================================
SELECT 
    s.store_id,
    s.store_type,
    s.store_size,
    ROUND(SUM(f.weekly_sales), 2) AS total_revenue,
    RANK() OVER (ORDER BY SUM(f.weekly_sales) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id, s.store_type, s.store_size
ORDER BY revenue_rank ASC
LIMIT 10;


-- ==========================================================
-- 7. Top 15 Departments Ranked by Revenue
-- ==========================================================
SELECT 
    dept_id,
    ROUND(SUM(weekly_sales), 2) AS total_revenue,
    ROUND(100.0 * SUM(weekly_sales) / (SELECT SUM(weekly_sales) FROM fact_sales), 2) AS pct_of_chain_sales,
    RANK() OVER (ORDER BY SUM(weekly_sales) DESC) AS dept_rank
FROM fact_sales
GROUP BY dept_id
ORDER BY dept_rank ASC
LIMIT 15;


-- ==========================================================
-- 8. Store Type Performance (Type A vs B vs C)
-- ==========================================================
SELECT 
    s.store_type,
    COUNT(DISTINCT s.store_id) AS num_stores,
    ROUND(AVG(s.store_size), 0) AS avg_store_size_sqft,
    ROUND(SUM(f.weekly_sales), 2) AS total_sales,
    ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales_per_dept,
    ROUND(100.0 * SUM(f.weekly_sales) / (SELECT SUM(weekly_sales) FROM fact_sales), 2) AS revenue_share_pct
FROM fact_sales f
JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_type
ORDER BY total_sales DESC;


-- ==========================================================
-- 9. Holiday vs Normal Week Sales Comparison (Holiday Lift)
-- ==========================================================
SELECT 
    CASE WHEN f.is_holiday = 1 THEN 'Holiday Week' ELSE 'Non-Holiday Week' END AS week_type,
    COUNT(*) AS total_dept_weeks,
    ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
    ROUND(SUM(f.weekly_sales), 2) AS total_sales
FROM fact_sales f
GROUP BY f.is_holiday;


-- ==========================================================
-- 10. Promotional Effectiveness (Markdown Weeks vs Non-Markdown Weeks)
-- ==========================================================
SELECT 
    CASE 
        WHEN (f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5) > 0 THEN 'Promotional Markdown Active'
        ELSE 'No Promotional Markdown'
    END AS promo_status,
    COUNT(*) AS total_observations,
    ROUND(AVG(f.weekly_sales), 2) AS avg_weekly_sales,
    ROUND(SUM(f.weekly_sales), 2) AS total_sales,
    ROUND(AVG(f.markdown1 + f.markdown2 + f.markdown3 + f.markdown4 + f.markdown5), 2) AS avg_markdown_discount
FROM fact_sales f
GROUP BY promo_status;


-- ==========================================================
-- 11. Cumulative Running Sales Total Across All Weeks
-- ==========================================================
WITH weekly_totals AS (
    SELECT 
        d.date_id,
        d.full_date,
        SUM(f.weekly_sales) AS weekly_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.date_id, d.full_date
)
SELECT 
    date_id,
    full_date,
    ROUND(weekly_revenue, 2) AS weekly_revenue,
    ROUND(SUM(weekly_revenue) OVER (ORDER BY date_id), 2) AS cumulative_chain_revenue
FROM weekly_totals
ORDER BY date_id;


-- ==========================================================
-- 12. Period-over-Period (Month-over-Month) Growth
-- ==========================================================
WITH monthly_sales_series AS (
    SELECT 
        d.year,
        d.month,
        SUM(f.weekly_sales) AS current_sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month
)
SELECT 
    year,
    month,
    ROUND(current_sales, 2) AS current_monthly_sales,
    ROUND(LAG(current_sales) OVER (ORDER BY year, month), 2) AS prior_month_sales,
    ROUND(100.0 * (current_sales - LAG(current_sales) OVER (ORDER BY year, month)) 
          / NULLIF(LAG(current_sales) OVER (ORDER BY year, month), 0), 2) AS mom_growth_pct
FROM monthly_sales_series
ORDER BY year, month;


-- ==========================================================
-- 13. Customer Returns & Negative-Sales Comprehensive Audit
-- ==========================================================
SELECT 
    returns_flag,
    COUNT(*) AS record_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_sales), 3) AS pct_of_total_records,
    ROUND(SUM(weekly_sales), 2) AS total_net_value,
    ROUND(AVG(weekly_sales), 2) AS avg_value,
    ROUND(MIN(weekly_sales), 2) AS min_sales_val,
    ROUND(MAX(weekly_sales), 2) AS max_sales_val
FROM fact_sales
GROUP BY returns_flag;
