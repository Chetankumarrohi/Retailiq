-- RetailIQ Star Schema DDL (SQLite)
-- Schema represents the analytical data warehouse queried by SQL analytics and Phase 2 AI tools.

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_dept;
DROP TABLE IF EXISTS dim_date;

-- Dimension 1: Store Master
CREATE TABLE dim_store (
    store_id INTEGER PRIMARY KEY,
    store_type TEXT NOT NULL,
    store_size INTEGER NOT NULL,
    first_active_week TEXT,
    last_active_week TEXT
);

-- Dimension 2: Department Master
CREATE TABLE dim_dept (
    dept_id INTEGER PRIMARY KEY
);

-- Dimension 3: Date / Calendar Dimension
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,   -- YYYYMMDD integer format, e.g., 20100205
    full_date TEXT NOT NULL,       -- YYYY-MM-DD
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_holiday_week INTEGER NOT NULL
);

-- Fact Table: Weekly Sales Transactions with Economic & Promotional Indicators
CREATE TABLE fact_sales (
    sales_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    dept_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    weekly_sales REAL NOT NULL,
    returns_flag INTEGER NOT NULL DEFAULT 0,
    is_holiday INTEGER NOT NULL DEFAULT 0,
    temperature REAL,
    fuel_price REAL,
    cpi REAL,
    unemployment REAL,
    markdown1 REAL DEFAULT 0.0,
    markdown2 REAL DEFAULT 0.0,
    markdown3 REAL DEFAULT 0.0,
    markdown4 REAL DEFAULT 0.0,
    markdown5 REAL DEFAULT 0.0,
    FOREIGN KEY (store_id) REFERENCES dim_store(store_id),
    FOREIGN KEY (dept_id) REFERENCES dim_dept(dept_id),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- Performance Indexes
CREATE INDEX idx_fact_store ON fact_sales(store_id);
CREATE INDEX idx_fact_dept ON fact_sales(dept_id);
CREATE INDEX idx_fact_date ON fact_sales(date_id);
CREATE INDEX idx_fact_store_dept ON fact_sales(store_id, dept_id);
CREATE INDEX idx_fact_returns ON fact_sales(returns_flag);
