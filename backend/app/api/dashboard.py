"""
Dashboard analytics API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.schemas.dashboard import (
    DashboardSummary, SalesTrendPoint, StoreRankingItem,
    DeptRankingItem, PromoEffectivenessItem, HolidayAnalysisItem,
    StoreTypePerformanceItem
)
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Executive KPI summary")
def get_summary():
    """Returns top-level KPIs (revenue, average weekly sales, return rate, lifts)."""
    return AnalyticsService.get_summary()


@router.get("/sales-trend", response_model=List[SalesTrendPoint], summary="Historical sales trend")
def get_sales_trend(
    store_id: Optional[int] = Query(None, description="Optional store filter"),
    dept_id: Optional[int] = Query(None, description="Optional department filter"),
    granularity: str = Query("monthly", pattern="^(monthly|weekly)$", description="Aggregation level"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """Returns monthly or weekly sales time-series."""
    return AnalyticsService.get_sales_trend(
        store_id=store_id,
        dept_id=dept_id,
        granularity=granularity,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/store-ranking", response_model=List[StoreRankingItem], summary="Store revenue rankings")
def get_store_ranking(
    limit: int = Query(15, ge=1, le=45, description="Number of stores to return")
):
    """Returns top stores ranked by historical sales."""
    return AnalyticsService.get_store_ranking(limit=limit)


@router.get("/department-ranking", response_model=List[DeptRankingItem], summary="Department revenue rankings")
def get_department_ranking(
    limit: int = Query(15, ge=1, le=81, description="Number of departments to return"),
    store_id: Optional[int] = Query(None, description="Optional store filter")
):
    """Returns top departments ranked by total sales."""
    return AnalyticsService.get_department_ranking(limit=limit, store_id=store_id)


@router.get("/promotion-effectiveness", response_model=List[PromoEffectivenessItem], summary="Promotional markdown impact")
def get_promotion_effectiveness(
    store_id: Optional[int] = Query(None, description="Optional store filter")
):
    """Compares average sales during promotional vs non-promotional markdown weeks."""
    return AnalyticsService.get_promotion_effectiveness(store_id=store_id)


@router.get("/holiday-analysis", response_model=List[HolidayAnalysisItem], summary="Holiday vs normal sales comparison")
def get_holiday_analysis(
    store_id: Optional[int] = Query(None, description="Optional store filter")
):
    """Compares average weekly sales between holiday and normal weeks."""
    return AnalyticsService.get_holiday_analysis(store_id=store_id)


@router.get("/store-types", response_model=List[StoreTypePerformanceItem], summary="Store Type A/B/C breakdown")
def get_store_types():
    """Returns store count, average size, and revenue breakdown by store type."""
    return AnalyticsService.get_store_types()
