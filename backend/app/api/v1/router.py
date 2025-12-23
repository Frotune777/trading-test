from fastapi import APIRouter
from app.api.v1.endpoints import data, health, recommendations, stocks, market, derivatives, insider, technicals, reasoning

api_router = APIRouter()
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(derivatives.router, prefix="/derivatives", tags=["derivatives"])
api_router.include_router(insider.router, prefix="/insider", tags=["insider"])
api_router.include_router(technicals.router, prefix="/technicals", tags=["technicals"])
api_router.include_router(reasoning.router, prefix="/reasoning", tags=["reasoning"])

api_router.include_router(health.router, tags=["health"])
