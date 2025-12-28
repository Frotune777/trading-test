"""
Monitoring Middleware
Automatically tracks API latency and traffic
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.database import SessionLocalSync
from app.services.latency_monitor_service import LatencyMonitor
from app.services.traffic_monitor_service import TrafficMonitor

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track API latency and traffic"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get user ID if authenticated
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics (async, don't block response)
        try:
            db = SessionLocalSync()
            
            # Record latency
            latency_monitor = LatencyMonitor(db)
            await latency_monitor.record(
                metric_type="api_call",
                operation=f"{request.method} {request.url.path}",
                latency_ms=latency_ms,
                user_id=user_id
            )
            
            # Record traffic
            traffic_monitor = TrafficMonitor(db)
            await traffic_monitor.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=latency_ms,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
        
        # Add latency header
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log errors"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Log error
            try:
                db = SessionLocalSync()
                traffic_monitor = TrafficMonitor(db)
                
                await traffic_monitor.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=None,  # Could add traceback here
                    endpoint=request.url.path,
                    user_id=getattr(request.state, 'user_id', None),
                    severity="ERROR"
                )
                
                db.close()
                
            except Exception as log_error:
                logger.error(f"Error logging error: {log_error}")
            
            # Re-raise the original exception
            raise e
