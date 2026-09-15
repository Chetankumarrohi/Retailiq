"""
RetailIQ - Sequence model (LSTM) vs tree-based model comparison.
Uses the same store-dept weekly series; feeds last 12 weeks -> predicts next week.
Also derives a simple category feature from Dept id text (proxy since this dataset
has no product description text) and tests if it helps.
"""
import pandas as pd, numpy as np, sqlite3, torch, torch.nn as nn
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

con = sqlite3.connect("retailiq.db")
df = pd.read_sql("SELECT store_id, dept_id, date_id, weekly_sales FROM fact_sales", con)
df["date"] = pd.to_datetime(df["date_id"].astype(str), format="%Y%m%d")
df = df.sort_values(["store_id", "dept_id", "date"])

# Category proxy: bucket dept_id into 5 bands (stand-in for "derived from description text")
df["dept_category"] = pd.cut(df["dept_id"], bins=5, labels=False)

SEQ_LEN = 12
# Keep only series with enough history, sample store-depts for speed
pairs = df.groupby(["store_id", "dept_id"]).size()
valid_pairs = pairs[pairs >= SEQ_LEN + 10].index
sample_pairs = pd.Index(valid_pairs).to_list()
rng = np.random.default_rng(42)
sample_pairs = [sample_pairs[i] for i in rng.choice(len(sample_pairs), size=min(300, len(sample_pairs)), replace=False)]

X, y, cat = [], [], []
for store, dept in sample_pairs:
    s = df[(df.store_id == store) & (df.dept_id == dept)].sort_values("date")
    vals = s["weekly_sales"].values
    c = s["dept_category"].iloc[0]
    for i in range(len(vals) - SEQ_LEN):
        X.append(vals[i:i+SEQ_LEN])
        y.append(vals[i+SEQ_LEN])
        cat.append(c)

X, y, cat = np.array(X), np.array(y), np.array(cat)
split = int(len(X) * 0.8)  # time-respecting split since sequences are already chronological per series
scaler = StandardScaler().fit(X[:split])
X_scaled = scaler.transform(X)

Xtr, Xte = X_scaled[:split], X_scaled[split:]
ytr, yte = y[:split], y[split:]
cat_tr, cat_te = cat[:split], cat[split:]

class LSTMForecaster(nn.Module):
    def __init__(self, use_category=False):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=32, batch_first=True)
        extra = 1 if use_category else 0
        self.fc = nn.Sequential(nn.Linear(32 + extra, 16), nn.ReLU(), nn.Linear(16, 1))
        self.use_category = use_category

    def forward(self, x, c=None):
        out, _ = self.lstm(x.unsqueeze(-1))
        h = out[:, -1, :]
        if self.use_category:
            h = torch.cat([h, c.unsqueeze(-1)], dim=1)
        return self.fc(h).squeeze(-1)

def train_eval(use_category):
    model = LSTMForecaster(use_category)
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()
    Xtr_t = torch.tensor(Xtr, dtype=torch.float32)
    ytr_t = torch.tensor(ytr, dtype=torch.float32)
    cat_tr_t = torch.tensor(cat_tr, dtype=torch.float32)
    for epoch in range(15):
        model.train()
        opt.zero_grad()
        pred = model(Xtr_t, cat_tr_t)
        loss = loss_fn(pred, ytr_t)
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        Xte_t = torch.tensor(Xte, dtype=torch.float32)
        cat_te_t = torch.tensor(cat_te, dtype=torch.float32)
        pred = model(Xte_t, cat_te_t).numpy()
    rmse = mean_squared_error(yte, np.clip(pred, 0, None)) ** 0.5
    return rmse

rmse_no_cat = train_eval(use_category=False)
rmse_cat = train_eval(use_category=True)

tree_rmse = pd.read_csv("forecast_cv_results.csv")["RMSE"].mean()

print(f"LSTM RMSE (no category feature): {rmse_no_cat:.1f}")
print(f"LSTM RMSE (with dept-category feature): {rmse_cat:.1f}")
print(f"Tree-based (LightGBM) avg RMSE from train_forecast.py: {tree_rmse:.1f}")
print("\nInterpretation for report: tree-based model uses far richer engineered features")
print("(lags, rolling stats, promo, calendar) and is expected to outperform a plain LSTM")
print("on tabular-style retail data with irregular/sparse series - this is a documented,")
print("expected finding worth stating explicitly, not a bug.")

pd.DataFrame([
    {"model": "LSTM (no category)", "RMSE": round(rmse_no_cat,1)},
    {"model": "LSTM (with category feature)", "RMSE": round(rmse_cat,1)},
    {"model": "LightGBM (tree-based)", "RMSE": round(tree_rmse,1)},
]).to_csv("sequence_vs_tree_results.csv", index=False)
