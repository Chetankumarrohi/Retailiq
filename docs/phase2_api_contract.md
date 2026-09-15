# RetailIQ: Phase 2 API & AI Tool Integration Contract

## 1. Overview

This document specifies the exact interface contracts between the **Phase 1 Data/Forecasting Engine** and the **Phase 2 FastAPI Backend & AI Assistant Layer**.

---

## 2. FastAPI REST Endpoints Specification

### 2.1 System & Metadata

#### `GET /api/health`
- **Description:** Verifies service health, database connectivity, and loaded model status.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "model_loaded": true,
  "model_version": "1.0.0"
}
```

#### `GET /api/stores`
- **Description:** Returns list of all available store IDs and their metadata.
- **Response `200 OK`:**
```json
[
  {
    "store_id": 1,
    "store_type": "A",
    "store_size": 151315,
    "first_active_week": "2010-02-05",
    "last_active_week": "2012-10-26"
  }
]
```

#### `GET /api/departments`
- **Description:** Returns list of all valid department IDs.
- **Response `200 OK`:**
```json
{
  "departments": [1, 2, 3, 4, 5, ..., 99],
  "total_count": 81
}
```

---

### 2.2 Executive Dashboard Services

#### `GET /api/dashboard/summary`
- **Description:** Returns high-level KPI summary metrics for the executive dashboard.
- **Response `200 OK`:**
```json
{
  "total_stores": 45,
  "total_departments": 81,
  "total_revenue": 6737218987.11,
  "avg_weekly_sales": 15981.26,
  "return_rate_pct": 0.305
}
```

#### `GET /api/dashboard/sales-trend?granularity=monthly`
- **Query Params:** `granularity` (`monthly` | `weekly`)
- **Response `200 OK`:**
```json
[
  {
    "period": "2010-02",
    "year": 2010,
    "month": 2,
    "month_name": "February",
    "sales": 191328902.45
  }
]
```

#### `GET /api/dashboard/store-ranking?limit=15`
- **Response `200 OK`:**
```json
[
  {
    "store_id": 20,
    "store_type": "A",
    "store_size": 203742,
    "total_sales": 301397792.46,
    "avg_weekly_sales": 29508.69
  }
]
```

#### `GET /api/dashboard/department-ranking?limit=15`
- **Response `200 OK`:**
```json
[
  {
    "dept_id": 92,
    "total_sales": 483943332.08,
    "avg_weekly_sales": 75208.59
  }
]
```

#### `GET /api/dashboard/promotion-effectiveness`
- **Response `200 OK`:**
```json
[
  {
    "period": "Promo",
    "observation_count": 150615,
    "avg_weekly_sales": 17409.12,
    "total_sales": 2622071987.54
  },
  {
    "period": "No Promo",
    "observation_count": 270955,
    "avg_weekly_sales": 15188.45,
    "total_sales": 4115146999.57
  }
]
```

#### `GET /api/dashboard/holiday-analysis`
- **Response `200 OK`:**
```json
[
  {
    "period": "Holiday Week",
    "observation_count": 29661,
    "avg_weekly_sales": 17035.82,
    "total_sales": 505300355.85
  },
  {
    "period": "Non-Holiday Week",
    "observation_count": 391909,
    "avg_weekly_sales": 15901.44,
    "total_sales": 6231918631.26
  }
]
```

---

### 2.3 Demand Forecasting Endpoint

#### `POST /api/forecast`
- **Request Body:**
```json
{
  "store_id": 1,
  "dept_id": 1,
  "horizon_weeks": 4
}
```
- **Response `200 OK`:**
```json
{
  "store_id": 1,
  "dept_id": 1,
  "horizon_weeks": 4,
  "model_version": "1.0.0",
  "model_type": "LightGBM Regressor",
  "predictions": [
    {
      "step": 1,
      "week": "2012-11-02",
      "weekly_sales": 34148.41,
      "is_holiday": 0,
      "assumptions": ["Known calendar features loaded from feature schedule"]
    },
    {
      "step": 2,
      "week": "2012-11-09",
      "weekly_sales": 25830.88,
      "is_holiday": 0,
      "assumptions": ["Known calendar features loaded from feature schedule"]
    },
    {
      "step": 3,
      "week": "2012-11-16",
      "weekly_sales": 24385.72,
      "is_holiday": 0,
      "assumptions": ["Known calendar features loaded from feature schedule"]
    },
    {
      "step": 4,
      "week": "2012-11-23",
      "weekly_sales": 28275.14,
      "is_holiday": 1,
      "assumptions": ["Known calendar features loaded from feature schedule"]
    }
  ],
  "historical_summary": {
    "last_known_date": "2012-10-26",
    "last_known_sales": 27390.81,
    "historical_mean_sales": 22513.32,
    "historical_std_sales": 9854.35,
    "total_historical_weeks": 143
  }
}
```

---

### 2.4 Conversational Assistant Endpoint

#### `POST /api/assistant/chat`
- **Request Body:**
```json
{
  "message": "What is our customer returns policy and how does it relate to negative sales?",
  "conversation_id": "optional-session-id"
}
```
- **Response `200 OK`:**
```json
{
  "answer": "Under RetailIQ's internal Returns Policy (Section 4), customer returns are accepted within 30 days with a receipt (14 days without). Returned inventory is inspected within 48 hours. Negative weekly sales figures in our reporting reflect weeks where return volume exceeded new sales, representing an expected business pattern rather than data corruption.",
  "reasoning_trace": [
    {
      "step": 1,
      "tool": "retrieval_tool",
      "input": {"question": "customer returns policy and negative sales"},
      "result": "[Source: policy_docs.txt - '4. RETURNS POLICY']\nCustomer returns are accepted within 30 days..."
    }
  ],
  "citations": [
    {
      "document": "policy_docs.txt",
      "section": "4. RETURNS POLICY"
    }
  ]
}
```

---

## 3. Phase 2 AI Planner-Executor Tool Specifications

### Tool 1: `sql_tool`
- **Purpose:** Executes safe `SELECT` analytical queries against SQLite star schema `retailiq.db`.
- **JSON Schema:**
```json
{
  "name": "sql_tool",
  "description": "Executes read-only SQL queries against the RetailIQ star schema (fact_sales, dim_store, dim_dept, dim_date) for analytical and aggregation questions.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Valid SQLite SELECT query adhering to the star schema."
      }
    },
    "required": ["query"]
  }
}
```

### Tool 2: `forecast_tool`
- **Purpose:** Calls `RetailForecasterPredictor` for multi-step sales predictions.
- **JSON Schema:**
```json
{
  "name": "forecast_tool",
  "description": "Generates weekly sales forecasts for a specific store and department across a chosen horizon (1 to 52 weeks).",
  "parameters": {
    "type": "object",
    "properties": {
      "store_id": {"type": "integer", "description": "Store identifier (1-45)."},
      "dept_id": {"type": "integer", "description": "Department identifier (1-99)."},
      "horizon_weeks": {"type": "integer", "description": "Forecast horizon in weeks (default: 4)."}
    },
    "required": ["store_id", "dept_id"]
  }
}
```

### Tool 3: `retrieval_tool`
- **Purpose:** Semantic / keyword retrieval over `data/knowledge_base/policy_docs.txt` with citations.
- **JSON Schema:**
```json
{
  "name": "retrieval_tool",
  "description": "Retrieves internal business documentation sections covering Inventory Policy, Markdown Rules, Supplier Terms, Returns Policy, and SOPs.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Natural language question or search query."}
    },
    "required": ["query"]
  }
}
```
