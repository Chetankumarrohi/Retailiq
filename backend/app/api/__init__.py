"""
API routers package init.
"""
from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.metadata import router as metadata_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.assistant import router as assistant_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(metadata_router)
api_router.include_router(dashboard_router)
api_router.include_router(forecast_router)
api_router.include_router(assistant_router)

__all__ = ["api_router"]
