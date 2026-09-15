"""
Data pipeline runner for RetailIQ.
Executes raw data loading, auditing, cleaning, and integrated artifact generation.
"""
from pathlib import Path
import pandas as pd
import json
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner


def run_data_pipeline(raw_dir: Path = None, processed_dir: Path = None) -> Path:
    """Runs the complete data preparation pipeline."""
    base_dir = Path(__file__).resolve().parents[2]
    if raw_dir is None:
        raw_dir = base_dir / "data" / "raw"
    if processed_dir is None:
        processed_dir = base_dir / "data" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    print("==========================================")
    print("STEP 1: Loading & Auditing Raw Datasets")
    print("==========================================")
    loader = DataLoader(raw_dir=raw_dir)
    stores_df = loader.load_stores()
    features_df = loader.load_features()
    train_df = loader.load_train()
    test_df = loader.load_test()

    audit = loader.audit_datasets()
    print("Dataset audit complete.")
    for name, stats in audit.items():
        print(f"  - {name}: {stats['rows']:,} rows, {stats['columns']} cols, {stats['memory_usage_mb']} MB")

    print("\n==========================================")
    print("STEP 2: Cleaning and Integrating Data")
    print("==========================================")
    cleaner = DataCleaner()
    clean_feat_df = cleaner.clean_features(features_df)
    clean_sales_df = cleaner.clean_sales(train_df)
    integrated_df, stats = cleaner.integrate_modelling_dataset(train_df, features_df, stores_df)

    print(f"Integration complete: {stats['rows']:,} rows across {stats['stores']} stores and {stats['departments']} departments.")
    print(f"Returns preserved: {stats['returns_count']:,} rows ({stats['returns_pct']}%) flagged with returns_flag=1.")

    print("\n==========================================")
    print("STEP 3: Saving Processed Artifacts")
    print("==========================================")
    integrated_path = processed_dir / "integrated_sales.parquet"
    features_path = processed_dir / "clean_features.parquet"
    audit_path = processed_dir / "data_audit_summary.json"

    integrated_df.to_parquet(integrated_path, index=False)
    clean_feat_df.to_parquet(features_path, index=False)
    
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)

    print(f"Artifacts saved:")
    print(f"  - {integrated_path}")
    print(f"  - {features_path}")
    print(f"  - {audit_path}")

    return integrated_path


if __name__ == "__main__":
    run_data_pipeline()
