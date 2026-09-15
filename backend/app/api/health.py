"""
Health check and system status endpoint.
"""
from fastapi import APIRouter
from backend.app.database.connection import check_database_health
from backend.app.services.forecast_service import ForecastService
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Check system health and dependency status")
def get_health():
    """
    Returns API status, database connectivity, and forecast model status.
    """
    db_health = check_database_health()
    model_health = ForecastService.check_model_health()

    is_healthy = db_health.get("status") == "connected" and model_health.get("status") == "loaded"

    return {
        "status": "ok" if is_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": db_health,
        "forecast_model": model_health,
        "ai_provider": settings.AI_PROVIDER
    }
