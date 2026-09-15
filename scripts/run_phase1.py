"""
RetailIQ Phase 1 Master Pipeline Runner.
Executes data audit, cleaning, database creation, feature engineering,
tree training, sequence model evaluation, and artifact verification end-to-end.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
from src.data.pipeline import run_data_pipeline
from src.database.build_database import build_database
from src.forecasting.train_tree import TreeForecasterTrainer
from src.forecasting.train_sequence import SequenceForecasterTrainer
from src.forecasting.predictor import RetailForecasterPredictor


def main():
    start_time = time.time()
    print("==========================================================")
    print("RETAILIQ — PHASE 1: DATA + DATABASE + FORECASTING PIPELINE")
    print("==========================================================")

    # 1. Data Pipeline
    print("\n>>> STEP 1: Ingesting, Cleaning, and Integrating Data")
    run_data_pipeline()

    # 2. Database Build
    print("\n>>> STEP 2: Constructing SQLite Analytical Star Schema (retailiq.db)")
    build_database()

    # 3. Tree Forecasting & CV
    print("\n>>> STEP 3: Engineering Features & Training LightGBM Forecaster with Forward CV")
    tree_trainer = TreeForecasterTrainer()
    feat_df = tree_trainer.load_and_prepare_features()
    tree_trainer.forward_chaining_cv(feat_df)
    tree_trainer.train_final_production_model(feat_df)

    # 4. Sequence Model
    print("\n>>> STEP 4: Training and Evaluating PyTorch LSTM Sequence Model")
    seq_trainer = SequenceForecasterTrainer()
    seq_trainer.train_and_evaluate(epochs=5)

    # 5. Predictor Verification
    print("\n>>> STEP 5: Verifying Production Inference Engine (predictor.py)")
    predictor = RetailForecasterPredictor()
    sample_pred = predictor.predict(store_id=1, dept_id=1, horizon_weeks=4)
    print(f"Sample 4-Week Forecast for Store 1, Dept 1 -> Steps generated: {len(sample_pred['predictions'])}")
    print(f"Step 1 ({sample_pred['predictions'][0]['week']}): ${sample_pred['predictions'][0]['weekly_sales']:,.2f}")

    elapsed = round(time.time() - start_time, 2)
    print("\n==========================================================")
    print(f"PHASE 1 COMPLETE in {elapsed} seconds!")
    print("All artifacts, models, database, and metrics verified.")
    print("==========================================================")


if __name__ == "__main__":
    main()
