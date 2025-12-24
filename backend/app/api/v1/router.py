from fastapi import APIRouter
from app.api.v1.endpoints import (
    data, health, recommendations, stocks, market, derivatives, insider, 
    technicals, reasoning, execution, alerts, analytics, ws_market,
    decision_history  # v1.1 addition
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
api_router.include_router(ws_market.router, tags=["websocket"])
api_router.include_router(health.router, tags=["health"])
