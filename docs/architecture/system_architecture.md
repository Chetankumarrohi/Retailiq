# RetailIQ System Architecture

This document defines the high-level multi-tier software architecture of RetailIQ, connecting the React 18 frontend SPA, the FastAPI asynchronous backend, the SQLite analytical star schema warehouse, the LightGBM production forecaster, and the autonomous multi-tool agent.

```mermaid
graph TD
    User([👤 Retail Executive / Business User])

    subgraph Presentation_Layer ["Presentation Layer (React 18 + Vite SPA)"]
        Dash[Executive Dashboard<br/><i>7 KPIs, Trends, Rankings, Lift</i>]
        FC[Demand Forecast Explorer<br/><i>Interactive Horizon, Baseline Viz</i>]
        Assist[AI Business Assistant<br/><i>Chat, Tool Traces, Policy Citations</i>]
        Insight[Data Insights & Architecture<br/><i>Feature Importance, Schema, Stores</i>]
    end

    subgraph API_Gateway ["Application Server (FastAPI + Python 3.11)"]
        Router{REST API Gateway<br/>/api/*}
        AnalyticsSvc[Analytics Service]
        ForecastSvc[Forecast Service]
        AgentSvc[Assistant Service]
        Guard[SQL Security Validator<br/><i>Read-Only AST & Whitelist</i>]
    end

    subgraph Storage_and_ML ["Data & Model Engines"]
        DB[(SQLite Star Schema<br/>retailiq.db<br/><i>421,570 fact rows</i>)]
        LGBM[LightGBM Forecaster<br/><i>44 Features, Lags, Rolling Stats</i>]
        KB[TF-IDF Knowledge Index<br/><i>policy_docs.txt (11 Sections)</i>]
    end

    User -->|HTTPS / Port 5173| Dash
    User -->|HTTPS / Port 5173| FC
    User -->|HTTPS / Port 5173| Assist
    User -->|HTTPS / Port 5173| Insight

    Dash -->|JSON /api/dashboard/*| Router
    FC -->|JSON /api/forecast| Router
    Assist -->|JSON /api/assistant/chat| Router
    Insight -->|JSON /api/stores| Router

    Router --> AnalyticsSvc
    Router --> ForecastSvc
    Router --> AgentSvc

    AnalyticsSvc -->|Read-Only URI| DB
    ForecastSvc -->|Inference Pipeline| LGBM
    AgentSvc -->|Planner Loop| Guard
    Guard -->|Safe SELECT| DB
    AgentSvc -->|Multi-Step Roll| ForecastSvc
    AgentSvc -->|Cosine Similarity| KB
```
