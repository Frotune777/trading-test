from fastapi import APIRouter
from app.api.v1.endpoints import (
    data, health, recommendations, stocks, market, derivatives, insider, 
    technicals, reasoning, execution, alerts, analytics, ws_market, ws_alerts,
    decision_history,  # v1.1 addition
    feed_health, scheduler,  # Data pipeline additions
    quad_analytics,  # QUAD Analytics v1.1 enhancement (READ-ONLY)
    quad_analysis,  # QUAD Analysis v1.1 (WRITE - triggers analysis)
    quad_scheduler,  # QUAD Scheduler v1.1 (schedule management)
    strategy,  # Strategy Management
    risk_metrics,  # Risk Metrics (VaR, Beta, Sharpe)
    trade_signals, # Trade Signals (SL/TP, S/R Zones)
    preferences, # User Preferences (Weights)
    risk_control, # New Risk Control router
    auth,  # User Authentication (Argon2/Fernet)
    action_center,  # Action Center (Order Approval Workflow)
    monitoring, # Monitoring endpoints
    reconciliation, # Position Reconciliation
    market_state, # Unified Market State
    ta_config, # TA Configuration
    risk, # Phase 3: Risk Management
    decisions, # Decision Ledger with Causal Explainability
)

api_router = APIRouter()
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(derivatives.router, prefix="/derivatives", tags=["derivatives"])
api_router.include_router(insider.router, prefix="/insider", tags=["insider"])
api_router.include_router(technicals.router, prefix="/technicals", tags=["technicals"])
api_router.include_router(reasoning.router, prefix="/reasoning", tags=["reasoning"])
api_router.include_router(execution.router, prefix="/execution", tags=["execution"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(decision_history.router, tags=["decision-history"])  # v1.1 addition
api_router.include_router(feed_health.router, prefix="/feed-health", tags=["feed-health"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(quad_analytics.router, tags=["quad-analytics"])  # QUAD Analytics v1.1 (READ-ONLY)
api_router.include_router(quad_analysis.router, tags=["quad-analysis"])  # QUAD Analysis v1.1 (WRITE)
api_router.include_router(quad_scheduler.router, tags=["quad-scheduler"])  # QUAD Scheduler v1.1
api_router.include_router(strategy.router, tags=["strategy"])  # Strategy Management
api_router.include_router(risk_metrics.router, prefix="/risk", tags=["risk-metrics"])  # Risk Metrics
api_router.include_router(trade_signals.router, tags=["trade-signals"]) # Trade Signals
api_router.include_router(ws_market.router, tags=["websocket"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["authentication"])  # User Authentication
api_router.include_router(action_center.router, tags=["action-center"])  # Action Center
api_router.include_router(preferences.router, tags=["preferences"])
api_router.include_router(risk_control.router, prefix="/risk-control", tags=["risk-control"])
api_router.include_router(monitoring.router, tags=["monitoring"])  # Monitoring endpoints
api_router.include_router(reconciliation.router, tags=["reconciliation"])
api_router.include_router(market_state.router, tags=["market-state"])
api_router.include_router(ta_config.router, tags=["ta-config"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])  # Phase 3: Risk Management
api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])  # Decision Ledger
api_router.include_router(ws_alerts.router, tags=["websockets"])


