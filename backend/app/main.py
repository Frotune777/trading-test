from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.router import api_router
from app.services.feed_health_monitor import feed_health_monitor
from app.core.scheduler_config import scheduler_config
from app.middleware.monitoring import MonitoringMiddleware, ErrorLoggingMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks"""
    # Startup
    logger.info("Starting Fortune Trading QUAD backend...")
    
    # Start feed health monitor
    logger.info("Starting feed health monitor...")
    await feed_health_monitor.start_monitoring()
    
    # Start scheduler
    logger.info("Starting data pipeline scheduler...")
    scheduler_config.start()
    
    logger.info("✅ All services started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fortune Trading QUAD backend...")
    
    # Stop feed health monitor
    await feed_health_monitor.stop_monitoring()
    
    # Stop scheduler
    scheduler_config.stop()
    
    logger.info("✅ All services stopped successfully")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
# Allow frontend origins for development
origins = [
    "http://localhost:3000",
    "http://localhost:3006", 
    "http://localhost:3010",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3006",
    "http://127.0.0.1:3010"
]

# Add any additional origins from settings
if settings.BACKEND_CORS_ORIGINS:
    origins.extend([str(origin) for origin in settings.BACKEND_CORS_ORIGINS])

logger.info(f"CORS enabled for origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,  # Commented out in favor of regex
    allow_origin_regex=r".*",  # Allow ALL origins for debugging
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Register Monitoring Middleware
app.add_middleware(MonitoringMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
