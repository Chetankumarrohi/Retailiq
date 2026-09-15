"""
Metadata endpoints providing store and department lists from the database.
"""
from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.schemas.dashboard import StoreItem
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Metadata"])


@router.get("/stores", response_model=List[StoreItem], summary="Get all stores with types and sizes")
def get_stores():
    """Returns list of 45 stores from dim_store."""
    return AnalyticsService.get_stores()


@router.get("/departments", response_model=List[int], summary="Get list of valid department IDs")
def get_departments(
    store_id: Optional[int] = Query(None, description="Optional store_id filter")
):
    """Returns unique department IDs across the chain or for a specific store."""
    return AnalyticsService.get_departments(store_id=store_id)
