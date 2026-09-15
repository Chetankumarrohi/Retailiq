# RetailIQ Backend (Phase 2 Target)

This directory is designated for the **FastAPI Backend Service** in Phase 2.

## Architecture Blueprint

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization, CORS, routers
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── dashboard.py # /api/dashboard/* endpoints
│   │   │   ├── forecast.py  # /api/forecast endpoint
│   │   │   └── assistant.py # /api/assistant/chat endpoint
│   ├── core/
│   │   ├── config.py        # Settings, API keys, database paths
│   │   └── security.py      # Rate limiting, query validation
│   ├── services/
│   │   ├── analytics.py     # Invokes src.database.build_database.RetailAnalyticsService
│   │   ├── forecasting.py   # Invokes src.forecasting.predictor.RetailForecasterPredictor
│   │   └── assistant.py     # AI agent planner-executor with tools
│   └── schemas/
│       ├── forecast.py      # Pydantic request/response models
│       ├── dashboard.py     # Pydantic KPI schemas
│       └── chat.py          # Pydantic assistant chat models
```

Phase 1 provides all core models (`models/trained/retailiq_forecaster.pkl`), database services, and the production predictor (`src/forecasting/predictor.py`) ready to be plugged in.
