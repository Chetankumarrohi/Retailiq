-- RetailIQ analytical SQL layer (SQLite, star schema)
-- NOTE: The Kaggle Walmart dataset has no inventory table, so "inventory cover"
-- is out of scope for this data source and is documented as a limitation.

-- 1. Sales by any dimension (store)
SELECT s.store_id, s.store_type, ROUND(SUM(f.weekly_sales),2) AS total_sales
FROM fact_sales f JOIN dim_store s ON f.store_id = s.store_id
GROUP BY s.store_id ORDER BY total_sales DESC;

-- 2. Sales by department
SELECT dept_id, ROUND(SUM(weekly_sales),2) AS total_sales
FROM fact_sales GROUP BY dept_id ORDER BY total_sales DESC;

-- 3. Period-over-period growth (year over year, by month)
WITH monthly AS (
  SELECT d.year, d.month, SUM(f.weekly_sales) AS sales
  FROM fact_sales f JOIN dim_date d ON f.date_id = d.date_id
  GROUP BY d.year, d.month
)
SELECT year, month, sales,
       LAG(sales) OVER (PARTITION BY month ORDER BY year) AS prev_year_sales,
       ROUND(100.0*(sales - LAG(sales) OVER (PARTITION BY month ORDER BY year))
             / LAG(sales) OVER (PARTITION BY month ORDER BY year), 1) AS yoy_growth_pct
FROM monthly ORDER BY month, year;

-- 4. Top-N departments per store
WITH ranked AS (
  SELECT store_id, dept_id, SUM(weekly_sales) AS sales,
         RANK() OVER (PARTITION BY store_id ORDER BY SUM(weekly_sales) DESC) AS rnk
  FROM fact_sales GROUP BY store_id, dept_id
)
SELECT * FROM ranked WHERE rnk <= 3 ORDER BY store_id, rnk;

-- 5. Running total of sales over time (whole chain)
WITH daily AS (
  SELECT date_id, SUM(weekly_sales) AS sales FROM fact_sales GROUP BY date_id
)
SELECT date_id, sales, SUM(sales) OVER (ORDER BY date_id) AS running_total
FROM daily ORDER BY date_id;

-- 6. Promotional lift: avg sales on markdown weeks vs non-markdown weeks
SELECT
  CASE WHEN (MarkDown1+MarkDown2+MarkDown3+MarkDown4+MarkDown5) > 0 THEN 'Promo' ELSE 'No Promo' END AS period,
  ROUND(AVG(weekly_sales),2) AS avg_weekly_sales, COUNT(*) AS n_weeks
FROM fact_sales GROUP BY period;

-- 7. Holiday vs non-holiday average sales (seasonality)
SELECT IsHoliday, ROUND(AVG(weekly_sales),2) AS avg_sales FROM fact_sales GROUP BY IsHoliday;
