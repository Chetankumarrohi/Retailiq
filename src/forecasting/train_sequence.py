"""
PyTorch sequence forecasting (LSTM) module for RetailIQ.
Implements a 12-week lookback LSTM with strict date-based chronological splitting.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, Tuple, Optional
from src.forecasting.evaluate import calculate_metrics, print_metrics


class RetailSequenceDataset(Dataset):
    """PyTorch Dataset for time-series sequences."""

    def __init__(self, X: np.ndarray, y: np.ndarray, is_holiday: Optional[np.ndarray] = None):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        self.is_holiday = is_holiday

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMForecaster(nn.Module):
    """PyTorch LSTM demand forecasting network."""

    def __init__(self, input_dim: int = 1, hidden_dim: int = 48, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 24),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(24, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        if x.dim() == 2:
            x = x.unsqueeze(-1)
        out, (hn, cn) = self.lstm(x)
        last_hidden = out[:, -1, :]
        pred = self.fc(last_hidden).squeeze(-1)
        return pred


class SequenceForecasterTrainer:
    """Trains and evaluates PyTorch LSTM sequence forecaster with strict date-based splitting."""

    def __init__(
        self,
        data_path: Optional[Path] = None,
        seq_len: int = 12,
        train_cutoff: str = "2012-05-31"
    ):
        base_dir = Path(__file__).resolve().parents[2]
        self.data_path = data_path or base_dir / "data" / "processed" / "integrated_sales.parquet"
        self.seq_len = seq_len
        self.train_cutoff = pd.to_datetime(train_cutoff)

    def prepare_sequences(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Builds 12-week lookback sequences per store-dept series.
        Applies strict date-cutoff splitting to prevent cross-series time leakage.
        """
        print(f"Loading data from {self.data_path}...")
        df = pd.read_parquet(self.data_path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["store_id", "dept_id", "date"]).reset_index(drop=True)

        X_train_list, y_train_list, hol_train_list = [], [], []
        X_val_list, y_val_list, hol_val_list = [], [], []

        # Iterate over each store-dept series
        grouped = df.groupby(["store_id", "dept_id"])
        
        for (store_id, dept_id), series in grouped:
            sales = series["weekly_sales"].values
            dates = series["date"].values
            holidays = series["is_holiday"].values

            n_samples = len(sales)
            if n_samples <= self.seq_len:
                continue

            for i in range(n_samples - self.seq_len):
                seq_x = sales[i:i + self.seq_len]
                target_y = sales[i + self.seq_len]
                target_date = dates[i + self.seq_len]
                target_hol = holidays[i + self.seq_len]

                # Strict date cutoff: if target date <= cutoff, it belongs to train set
                if pd.to_datetime(target_date) <= self.train_cutoff:
                    X_train_list.append(seq_x)
                    y_train_list.append(target_y)
                    hol_train_list.append(target_hol)
                else:
                    X_val_list.append(seq_x)
                    y_val_list.append(target_y)
                    hol_val_list.append(target_hol)

        X_train = np.array(X_train_list)
        y_train = np.array(y_train_list)
        hol_train = np.array(hol_train_list)

        X_val = np.array(X_val_list)
        y_val = np.array(y_val_list)
        hol_val = np.array(hol_val_list)

        print(f"Prepared sequence datasets:")
        print(f"  - Train sequences (<= {self.train_cutoff.date()}): {len(X_train):,}")
        print(f"  - Validation sequences (> {self.train_cutoff.date()}): {len(X_val):,}")

        # Scale features using training statistics only (fit on train, transform both)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        return X_train_scaled, y_train, hol_train, X_val_scaled, y_val, hol_val

    def train_and_evaluate(self, epochs: int = 15, batch_size: int = 256, lr: float = 0.005) -> Dict[str, float]:
        """Trains the PyTorch LSTM model and evaluates on the date-safe validation set."""
        torch.manual_seed(42)
        np.random.seed(42)

        X_tr, y_tr, hol_tr, X_val, y_val, hol_val = self.prepare_sequences()

        train_dataset = RetailSequenceDataset(X_tr, y_tr)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        model = LSTMForecaster(input_dim=1, hidden_dim=48, num_layers=1)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
        loss_fn = nn.MSELoss()

        print("\n==========================================")
        print(f"Training PyTorch LSTM Forecaster ({epochs} Epochs)")
        print("==========================================")

        for epoch in range(1, epochs + 1):
            model.train()
            running_loss = 0.0
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                preds = model(batch_x)
                loss = loss_fn(preds, batch_y)
                loss.backward()
                optimizer.step()
                running_loss += loss.item() * len(batch_y)

            epoch_rmse = np.sqrt(running_loss / len(train_dataset))
            if epoch % 3 == 0 or epoch == epochs:
                print(f"Epoch {epoch:2d}/{epochs:2d} | Train Loss (MSE): {running_loss/len(train_dataset):,.1f} | Train RMSE: {epoch_rmse:,.2f}")

        # Evaluation on holdout
        model.eval()
        with torch.no_grad():
            val_tensor = torch.tensor(X_val, dtype=torch.float32)
            raw_preds = model(val_tensor).numpy()

        metrics = calculate_metrics(y_val, raw_preds, hol_val)
        print_metrics("PyTorch LSTM Final Holdout Evaluation", metrics)

        return metrics


def run_sequence_pipeline():
    trainer = SequenceForecasterTrainer()
    metrics = trainer.train_and_evaluate(epochs=12)
    return metrics


if __name__ == "__main__":
    run_sequence_pipeline()
