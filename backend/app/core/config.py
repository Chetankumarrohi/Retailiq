"""
Central configuration settings for RetailIQ Backend.
Loads environment variables safely with sensible project-relative defaults.
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


# Resolve project root relative to this file
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "RetailIQ API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Project Paths
    DATABASE_PATH: Path = PROJECT_ROOT / "retailiq.db"
    MODEL_PATH: Path = PROJECT_ROOT / "models" / "trained" / "retailiq_forecaster.pkl"
    MODEL_METADATA_PATH: Path = PROJECT_ROOT / "models" / "metadata" / "model_metadata.json"
    POLICY_DOC_PATH: Path = PROJECT_ROOT / "data" / "knowledge_base" / "policy_docs.txt"
    HISTORY_PARQUET_PATH: Path = PROJECT_ROOT / "data" / "processed" / "integrated_sales.parquet"
    FEATURES_PARQUET_PATH: Path = PROJECT_ROOT / "data" / "processed" / "clean_features.parquet"

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]

    # AI Assistant Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "anthropic")
    AI_API_KEY: str = os.getenv("AI_API_KEY", os.getenv("ANTHROPIC_API_KEY", os.getenv("OPENAI_API_KEY", "")))
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-sonnet-4-5")

    class Config:
        env_file = BACKEND_DIR / ".env"
        extra = "ignore"


settings = Settings()
