"""
Pydantic schemas for Executive Dashboard & Metadata APIs.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class StoreItem(BaseModel):
    store_id: int
    store_type: str
    store_size: int
    first_active_week: Optional[str] = None
    last_active_week: Optional[str] = None


class DepartmentItem(BaseModel):
    dept_id: int


class DashboardSummary(BaseModel):
    total_revenue: float
    avg_weekly_sales: float
    total_stores: int
    total_departments: int
    return_rate_pct: float
    top_store_id: int
    top_store_revenue: float
    top_dept_id: int
    top_dept_revenue: float
    holiday_lift_pct: float
    promotion_lift_pct: float


class SalesTrendPoint(BaseModel):
    period: str
    year: int
    month: Optional[int] = None
    week: Optional[int] = None
    sales: float


class StoreRankingItem(BaseModel):
    store_id: int
    store_type: str
    store_size: int
    total_sales: float
    avg_weekly_sales: float


class DeptRankingItem(BaseModel):
    dept_id: int
    total_sales: float
    avg_weekly_sales: float
    revenue_share_pct: Optional[float] = None


class PromoEffectivenessItem(BaseModel):
    period: str
    observation_count: int
    avg_weekly_sales: float
    total_sales: float


class HolidayAnalysisItem(BaseModel):
    period: str
    is_holiday: int
    observation_count: int
    avg_weekly_sales: float
    total_sales: float


class StoreTypePerformanceItem(BaseModel):
    store_type: str
    num_stores: int
    avg_store_size: float
    total_sales: float
    avg_weekly_sales: float
    revenue_share_pct: float
