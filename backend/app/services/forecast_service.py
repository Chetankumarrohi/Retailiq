"""
Forecasting service for RetailIQ.
Wraps the Phase 1 production predictor engine and handles validation and formatting.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import HTTPException
from src.forecasting.predictor import RetailForecasterPredictor
from backend.app.core.config import settings
from backend.app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastPoint, HistoricalSummary


class ForecastService:
    """Service providing demand forecasting capabilities."""

    _predictor_instance: Optional[RetailForecasterPredictor] = None

    @classmethod
    def get_predictor(cls) -> RetailForecasterPredictor:
        """Lazy loads and caches the production predictor."""
        if cls._predictor_instance is None:
            if not settings.MODEL_PATH.exists():
                raise HTTPException(
                    status_code=503,
                    detail=f"Forecasting model artifact not found at {settings.MODEL_PATH}. Train the model first."
                )
            cls._predictor_instance = RetailForecasterPredictor(
                model_path=settings.MODEL_PATH,
                history_path=settings.HISTORY_PARQUET_PATH,
                future_features_path=settings.FEATURES_PARQUET_PATH
            )
        return cls._predictor_instance

    @classmethod
    def generate_forecast(cls, request: ForecastRequest) -> ForecastResponse:
        """
        Validates store-department pair, executes recursive multi-step forecasting,
        and returns structured response.
        """
        predictor = cls.get_predictor()
        try:
            raw_result = predictor.predict(
                store_id=request.store_id,
                dept_id=request.dept_id,
                horizon_weeks=request.horizon_weeks
            )
        except ValueError as e:
            # Series not found or insufficient history
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Forecasting computation failed: {str(e)}"
            )

        # Convert to Pydantic models
        predictions = [
            ForecastPoint(
                step=p["step"],
                week=p["week"],
                weekly_sales=p["weekly_sales"],
                is_holiday=p["is_holiday"],
                assumptions=p.get("assumptions", [])
            )
            for p in raw_result["predictions"]
        ]

        hist = raw_result["historical_summary"]
        hist_summary = HistoricalSummary(
            last_known_date=hist["last_known_date"],
            last_known_sales=hist["last_known_sales"],
            historical_mean_sales=hist["historical_mean_sales"],
            historical_std_sales=hist["historical_std_sales"],
            total_historical_weeks=hist["total_historical_weeks"]
        )

        return ForecastResponse(
            store_id=raw_result["store_id"],
            dept_id=raw_result["dept_id"],
            horizon_weeks=raw_result["horizon_weeks"],
            model_version=raw_result["model_version"],
            model_type=raw_result["model_type"],
            predictions=predictions,
            historical_summary=hist_summary
        )

    @classmethod
    def check_model_health(cls) -> Dict[str, Any]:
        """Verifies predictor can load and returns model status."""
        try:
            if settings.MODEL_PATH.exists():
                return {
                    "status": "loaded",
                    "model_path": str(settings.MODEL_PATH.name),
                    "version": "1.0.0"
                }
            return {
                "status": "not_found",
                "detail": f"Model file missing at {settings.MODEL_PATH}"
            }
        except Exception as e:
            return {
                "status": "error",
                "detail": str(e)
            }
