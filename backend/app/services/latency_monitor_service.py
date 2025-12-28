"""
Latency Monitor Service
Tracks operation latency and provides analytics
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models_monitoring import LatencyMetric

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class LatencyMonitor:
    """Monitor and track operation latency"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def record(
        self,
        metric_type: str,
        operation: str,
        latency_ms: float,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a latency metric
        
        Args:
            metric_type: Type of metric ('order_execution', 'api_call', 'websocket')
            operation: Operation name
            latency_ms: Latency in milliseconds
            user_id: Optional user ID
            metadata: Optional additional context
        """
        try:
            metric = LatencyMetric(
                metric_type=metric_type,
                operation=operation,
                latency_ms=latency_ms,
                user_id=user_id,
                timestamp=datetime.now(IST),
                metadata=metadata
            )
            
            self.db.add(metric)
            self.db.commit()
            
            # Log if latency is high
            if latency_ms > 1000:  # > 1 second
                logger.warning(
                    f"High latency detected: {operation} took {latency_ms:.2f}ms"
                )
                
        except Exception as e:
            logger.error(f"Failed to record latency metric: {e}")
            self.db.rollback()
    
    def get_metrics(
        self,
        metric_type: Optional[str] = None,
        operation: Optional[str] = None,
        hours: int = 24
    ) -> List[LatencyMetric]:
        """Get latency metrics"""
        query = self.db.query(LatencyMetric)
        
        # Filter by time
        since = datetime.now(IST) - timedelta(hours=hours)
        query = query.filter(LatencyMetric.timestamp >= since)
        
        # Filter by type
        if metric_type:
            query = query.filter(LatencyMetric.metric_type == metric_type)
        
        # Filter by operation
        if operation:
            query = query.filter(LatencyMetric.operation == operation)
        
        return query.order_by(LatencyMetric.timestamp.desc()).all()
    
    def get_stats(
        self,
        metric_type: Optional[str] = None,
        operation: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, float]:
        """
        Get latency statistics
        
        Returns:
            Dictionary with avg, min, max, p50, p95, p99
        """
        query = self.db.query(LatencyMetric.latency_ms)
        
        # Filter by time
        since = datetime.now(IST) - timedelta(hours=hours)
        query = query.filter(LatencyMetric.timestamp >= since)
        
        # Filter by type
        if metric_type:
            query = query.filter(LatencyMetric.metric_type == metric_type)
        
        # Filter by operation
        if operation:
            query = query.filter(LatencyMetric.operation == operation)
        
        latencies = [row[0] for row in query.all()]
        
        if not latencies:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }
        
        latencies.sort()
        count = len(latencies)
        
        return {
            "count": count,
            "avg": sum(latencies) / count,
            "min": latencies[0],
            "max": latencies[-1],
            "p50": latencies[int(count * 0.50)],
            "p95": latencies[int(count * 0.95)] if count > 20 else latencies[-1],
            "p99": latencies[int(count * 0.99)] if count > 100 else latencies[-1]
        }
    
    def get_operations_summary(self, hours: int = 24) -> List[Dict]:
        """Get summary of all operations"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        results = self.db.query(
            LatencyMetric.operation,
            func.count(LatencyMetric.id).label('count'),
            func.avg(LatencyMetric.latency_ms).label('avg_latency'),
            func.max(LatencyMetric.latency_ms).label('max_latency')
        ).filter(
            LatencyMetric.timestamp >= since
        ).group_by(
            LatencyMetric.operation
        ).all()
        
        return [
            {
                "operation": row.operation,
                "count": row.count,
                "avg_latency": round(row.avg_latency, 2),
                "max_latency": round(row.max_latency, 2)
            }
            for row in results
        ]


@asynccontextmanager
async def track_latency(
    metric_type: str,
    operation: str,
    db: Session,
    user_id: Optional[int] = None,
    metadata: Optional[Dict] = None
):
    """
    Context manager for tracking latency
    
    Usage:
        async with track_latency("order_execution", "place_order", db):
            # Your code here
            pass
    """
    start_time = time.time()
    
    try:
        yield
    finally:
        latency_ms = (time.time() - start_time) * 1000
        
        monitor = LatencyMonitor(db)
        await monitor.record(
            metric_type=metric_type,
            operation=operation,
            latency_ms=latency_ms,
            user_id=user_id,
            metadata=metadata
        )
