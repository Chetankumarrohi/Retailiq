"""
RetailIQ - Data pipeline + Star Schema builder
Reads raw Kaggle Walmart files -> cleans -> builds star schema in SQLite.
"""
import pandas as pd, numpy as np, sqlite3, os

DATA = "data"
DB = "retailiq.db"

train = pd.read_csv(f"{DATA}/train.csv", parse_dates=["Date"])
test = pd.read_csv(f"{DATA}/test.csv", parse_dates=["Date"])
features = pd.read_csv(f"{DATA}/features.csv", parse_dates=["Date"])
stores = pd.read_csv(f"{DATA}/stores.csv")

# ---- Cleaning ----
# 1. Negative Weekly_Sales = returns -> keep but flag, and create a returns-adjusted column
train["Returns_Flag"] = train["Weekly_Sales"] < 0
train["Weekly_Sales_Clean"] = train["Weekly_Sales"].clip(lower=0)

# 2. Missing markdowns -> no promo running -> 0
md_cols = [c for c in features.columns if c.startswith("MarkDown")]
features[md_cols] = features[md_cols].fillna(0)
features["CPI"] = features["CPI"].ffill()
features["Unemployment"] = features["Unemployment"].ffill()

# 3. IsHoliday exists in both train and features; trust features' version, drop train's before merge
train = train.drop(columns=["IsHoliday"], errors="ignore")

# 4. Detect store open/close mid-period: store-week rows that don't exist = closed that week (no fabrication, just note range)
store_active_range = train.groupby("Store")["Date"].agg(["min", "max"]).rename(columns={"min": "first_active_week", "max": "last_active_week"})

# ---- Dimension tables ----
dim_store = stores.merge(store_active_range, left_on="Store", right_index=True, how="left")
dim_store.columns = ["store_id", "store_type", "store_size", "first_active_week", "last_active_week"]

dim_dept = pd.DataFrame({"dept_id": sorted(train["Dept"].unique())})

all_dates = pd.concat([train["Date"], test["Date"], features["Date"]]).drop_duplicates().sort_values()
dim_date = pd.DataFrame({"date": all_dates})
dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["is_holiday_week"] = dim_date["date"].isin(features.loc[features["IsHoliday"]==True, "Date"])

# ---- Fact table ----
fact = train.merge(features, on=["Store", "Date"], how="left")
fact["date_id"] = fact["Date"].dt.strftime("%Y%m%d").astype(int)
fact = fact.rename(columns={"Store": "store_id", "Dept": "dept_id"})
fact_cols = ["store_id", "dept_id", "date_id", "Weekly_Sales_Clean", "Returns_Flag", "IsHoliday",
             "Temperature", "Fuel_Price", "CPI", "Unemployment"] + md_cols
fact_sales = fact[fact_cols].rename(columns={"Weekly_Sales_Clean": "weekly_sales"})

# ---- Write to SQLite ----
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
dim_store.to_sql("dim_store", con, index=False)
dim_dept.to_sql("dim_dept", con, index=False)
dim_date.drop(columns=["date"]).to_sql("dim_date", con, index=False)
fact_sales.to_sql("fact_sales", con, index=False)

con.execute("CREATE INDEX idx_fact_store ON fact_sales(store_id)")
con.execute("CREATE INDEX idx_fact_dept ON fact_sales(dept_id)")
con.execute("CREATE INDEX idx_fact_date ON fact_sales(date_id)")
con.commit()

print("Rows written -> fact_sales:", len(fact_sales), "dim_store:", len(dim_store),
      "dim_dept:", len(dim_dept), "dim_date:", len(dim_date))
con.close()
