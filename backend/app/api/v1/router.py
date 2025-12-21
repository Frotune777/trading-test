from fastapi import APIRouter
from app.api.v1.endpoints import data, health, recommendations

api_router = APIRouter()
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(health.router, tags=["health"])
