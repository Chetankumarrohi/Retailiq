# RetailIQ System Architecture

This document defines the high-level system architecture of RetailIQ: a unified Streamlit application connecting an analytical SQLite star schema database, a LightGBM production demand forecaster, and an autonomous multi-tool business assistant.

```mermaid
graph TD
    User([👤 Retail Executive / Business User])

    subgraph App ["Streamlit Web Application (app.py)"]
        Dash[📊 Executive Dashboard<br/><i>7 KPIs, Trends, Rankings, Lift</i>]
        FC[🔮 Demand Forecast Explorer<br/><i>Interactive Horizon, Historical Context</i>]
        Assist[💬 AI Business Assistant<br/><i>Chat, Tool Traces, Policy Citations</i>]
    end

    subgraph Services ["Python Service Layer (src/)"]
        AnalyticsSvc[AnalyticsService<br/><i>Filter-Aware Dashboard Queries</i>]
        ForecastSvc[RetailForecasterPredictor<br/><i>44-Feature Recursive Inference</i>]
        AgentSvc[RetailIQAssistant<br/><i>Planner-Executor Orchestrator</i>]
        Guard[SQLSecurityValidator<br/><i>Read-Only AST & Whitelist</i>]
        RAG[PolicyRetriever<br/><i>TF-IDF Cosine Similarity</i>]
    end

    subgraph Storage ["Data & Model Engines"]
        DB[(SQLite Star Schema<br/>retailiq.db<br/><i>421,570 fact rows</i>)]
        LGBM[LightGBM Forecaster<br/><i>44 Features, Lags, Rolling Stats</i>]
        KB[TF-IDF Knowledge Index<br/><i>policy_docs.txt (11 Sections)</i>]
    end

    User -->|http://localhost:8501| App

    Dash --> AnalyticsSvc
    FC --> ForecastSvc
    Assist --> AgentSvc

    AnalyticsSvc -->|Read-Only URI| DB
    ForecastSvc -->|Inference Pipeline| LGBM
    AgentSvc -->|Planner Loop| Guard
    Guard -->|Safe SELECT| DB
    AgentSvc -->|Multi-Step Roll| ForecastSvc
    AgentSvc -->|Cosine Similarity| RAG
    RAG --> KB
```
