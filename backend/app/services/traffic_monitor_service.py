"""
Traffic Monitor Service
Tracks API usage, traffic patterns, and error rates
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models_monitoring import APITraffic, ErrorLog

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class TrafficMonitor:
    """Monitor API traffic and usage patterns"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Record an API request"""
        try:
            traffic = APITraffic(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(IST)
            )
            
            self.db.add(traffic)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record traffic: {e}")
            self.db.rollback()
    
    async def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[int] = None,
        severity: str = "ERROR",
        metadata: Optional[Dict] = None
    ):
        """Record an error"""
        try:
            error = ErrorLog(
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                endpoint=endpoint,
                user_id=user_id,
                severity=severity,
                timestamp=datetime.now(IST),
                metadata=metadata
            )
            
            self.db.add(error)
            self.db.commit()
            
            # Log critical errors
            if severity == "CRITICAL":
                logger.critical(f"Critical error: {error_type} - {error_message}")
                
        except Exception as e:
            logger.error(f"Failed to record error: {e}")
            self.db.rollback()
    
    def get_traffic_stats(self, hours: int = 24) -> Dict:
        """Get traffic statistics"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        total_requests = self.db.query(func.count(APITraffic.id)).filter(
            APITraffic.timestamp >= since
        ).scalar()
        
        error_requests = self.db.query(func.count(APITraffic.id)).filter(
            APITraffic.timestamp >= since,
            APITraffic.status_code >= 400
        ).scalar()
        
        avg_response_time = self.db.query(func.avg(APITraffic.response_time_ms)).filter(
            APITraffic.timestamp >= since
        ).scalar() or 0
        
        return {
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": (error_requests / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time_ms": round(avg_response_time, 2),
            "period_hours": hours
        }
    
    def get_endpoint_stats(self, hours: int = 24) -> List[Dict]:
        """Get per-endpoint statistics"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        results = self.db.query(
            APITraffic.endpoint,
            APITraffic.method,
            func.count(APITraffic.id).label('count'),
            func.avg(APITraffic.response_time_ms).label('avg_response_time'),
            func.sum(func.case((APITraffic.status_code >= 400, 1), else_=0)).label('errors')
        ).filter(
            APITraffic.timestamp >= since
        ).group_by(
            APITraffic.endpoint,
            APITraffic.method
        ).order_by(
            func.count(APITraffic.id).desc()
        ).limit(50).all()
        
        return [
            {
                "endpoint": row.endpoint,
                "method": row.method,
                "count": row.count,
                "avg_response_time_ms": round(row.avg_response_time, 2),
                "errors": row.errors,
                "error_rate": round(row.errors / row.count * 100, 2) if row.count > 0 else 0
            }
            for row in results
        ]
    
    def get_error_stats(self, hours: int = 24) -> Dict:
        """Get error statistics"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        total_errors = self.db.query(func.count(ErrorLog.id)).filter(
            ErrorLog.timestamp >= since
        ).scalar()
        
        # Group by error type
        error_types = self.db.query(
            ErrorLog.error_type,
            func.count(ErrorLog.id).label('count')
        ).filter(
            ErrorLog.timestamp >= since
        ).group_by(
            ErrorLog.error_type
        ).order_by(
            func.count(ErrorLog.id).desc()
        ).limit(10).all()
        
        # Group by severity
        severity_counts = self.db.query(
            ErrorLog.severity,
            func.count(ErrorLog.id).label('count')
        ).filter(
            ErrorLog.timestamp >= since
        ).group_by(
            ErrorLog.severity
        ).all()
        
        return {
            "total_errors": total_errors,
            "error_types": [
                {"type": row.error_type, "count": row.count}
                for row in error_types
            ],
            "by_severity": {
                row.severity: row.count
                for row in severity_counts
            }
        }
    
    def get_user_activity(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """Get user activity statistics"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        results = self.db.query(
            APITraffic.user_id,
            func.count(APITraffic.id).label('request_count'),
            func.avg(APITraffic.response_time_ms).label('avg_response_time')
        ).filter(
            APITraffic.timestamp >= since,
            APITraffic.user_id.isnot(None)
        ).group_by(
            APITraffic.user_id
        ).order_by(
            func.count(APITraffic.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "user_id": row.user_id,
                "request_count": row.request_count,
                "avg_response_time_ms": round(row.avg_response_time, 2)
            }
            for row in results
        ]
