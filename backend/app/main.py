"""
RetailIQ FastAPI Application Entry Point.
Provides RESTful APIs for Executive Dashboards, ML Demand Forecasting, and Multi-Tool AI Assistant.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from backend.app.core.config import settings
from backend.app.api import api_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "RetailIQ is an enterprise demand forecasting platform and multi-tool AI business assistant. "
        "This REST API powers executive dashboards, real-time ML demand forecasting, and an autonomous "
        "planner-executor assistant with SQL analytics, ML prediction, and policy retrieval tools."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error occurred. Please check server logs."}
        )

# Register API Routers
app.include_router(api_router)


@app.get("/", tags=["Root"], summary="API Root Overview")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "stores": "/api/stores",
            "departments": "/api/departments",
            "dashboard_summary": "/api/dashboard/summary",
            "sales_trend": "/api/dashboard/sales-trend",
            "store_ranking": "/api/dashboard/store-ranking",
            "forecast": "/api/forecast",
            "assistant": "/api/assistant/chat"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
