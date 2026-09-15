"""
Forecasting API endpoint.
"""
from fastapi import APIRouter, HTTPException
from backend.app.schemas.forecast import ForecastRequest, ForecastResponse
from backend.app.services.forecast_service import ForecastService

router = APIRouter(tags=["Forecasting"])


@router.post("/forecast", response_model=ForecastResponse, summary="Generate multi-week demand forecast")
def generate_forecast(request: ForecastRequest):
    """
    Generates recursive multi-step demand predictions for a store-department pair
    across 1 to 12 future weeks using the production LightGBM model.
    """
    return ForecastService.generate_forecast(request)
