# Fortune Trading Backend (FastAPI)

The Python-based core engine for the Fortune Trading Platform, powering the Institutional QUAD Reasoning Engine, Data Ingestion, and Execution Services.

## 🏗️ Architecture

The backend is built with **FastAPI** and follows a service-oriented architecture.

### Key Directories

-   **`app/api/`**: API Route definitions (v1).
-   **`app/core/`**: Core configs, decision engines (`six_pillar_engine.py`), and base classes.
-   **`app/services/`**: Business logic layer.
    -   `institutional_quad_service.py`: Orchestrates QUAD v2 Analysis.
    -   `quad_analysis_engine.py`: Hybrid engine for triggers.
    -   `input_builders.py`: Data fetchers for specific pillars.
    -   `broker_gateway.py`: Unified interface for broker interactions.
-   **`app/workers/`**: Celery worker definitions for background tasks.
-   **`app/database/`**: SQLAlchemy models and DB connection logic.

## 🧠 QUAD Reasoning Engine

The core differentiator is the **QUAD (Quantitative, Universal, Algo-Driven) Engine**, which uses a 6-pillar approach to generate trading signals.

### The 6 Pillars
1.  **Price Structure**: Technicals, MTF (Multi-Timeframe) Trends.
2.  **Institutional Flow**: Smart Money Concepts (SMC), Volume profiles.
3.  **Derivatives Positioning**: OI Analysis, PCR, Option Chain.
4.  **Regime Context**: VIX, Sector Performance, Macro regime.
5.  **Fundamental Thematic**: Sentiment, News (Placeholder).
6.  **Execution Feasibility**: Liquidity check, Spread analysis.

### Execution Flow
1.  **Trigger**: API request or Scheduler.
2.  **Input Construction**: `InputBuilderRegistry` fetches raw data for all pillars.
3.  **Pillar Execution**: Each pillar calculates a score (0-100) and bias.
4.  **Aggregation**: `BayesianDecisionAssembler` combines scores into a `TradeIntent`.
5.  **Persistence**: Result stored in `quad_decisions_v2` (PostgreSQL).

## 🚀 Development

### Prerequisites
-   Python 3.11+
-   PostgreSQL 15 (TimescaleDB)
-   Redis 7
-   OpenAlgo (for external data/execution)

### Running Manually

```bash
# Activate virtual env
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# Run Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

Once running, access the auto-generated Swagger UI at:
[http://localhost:8000/docs](http://localhost:8000/docs)

## 🧪 Testing

```bash
# Run pytest
pytest
```
