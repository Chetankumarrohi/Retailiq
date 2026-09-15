"""
Pydantic schemas for Demand Forecasting API.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    store_id: int = Field(..., gt=0, le=45, description="Store identifier (1 to 45)")
    dept_id: int = Field(..., gt=0, le=99, description="Department identifier (1 to 99)")
    horizon_weeks: int = Field(4, ge=1, le=12, description="Forecast horizon in weeks (1 to 12)")


class ForecastPoint(BaseModel):
    step: int
    week: str
    weekly_sales: float
    is_holiday: int
    assumptions: List[str] = []


class HistoricalSummary(BaseModel):
    last_known_date: str
    last_known_sales: float
    historical_mean_sales: float
    historical_std_sales: float
    total_historical_weeks: int


class ForecastResponse(BaseModel):
    store_id: int
    dept_id: int
    horizon_weeks: int
    model_version: str
    model_type: str
    predictions: List[ForecastPoint]
    historical_summary: HistoricalSummary
