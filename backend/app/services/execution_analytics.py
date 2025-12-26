"""
Execution Analytics Service
Tracks and analyzes order execution quality.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
import statistics

Base = declarative_base()

logger = logging.getLogger(__name__)


class ExecutionRecord(Base):
    """Execution analytics record"""
    __tablename__ = "execution_analytics"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), nullable=False, index=True)
    broker = Column(String(20), nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy_id = Column(Integer)
    order_time = Column(DateTime, nullable=False)
    execution_time = Column(DateTime)
    latency_ms = Column(Integer)
    requested_price = Column(DECIMAL(10, 2))
    executed_price = Column(DECIMAL(10, 2))
    slippage = Column(DECIMAL(10, 4))
    quantity = Column(Integer)
    status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionAnalyticsService:
    """
    Execution Analytics Service
    
    Tracks:
        - Order latency
        - Slippage
        - Fill rate
        - Broker performance
        - Strategy performance
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_order_execution(
        self,
        order_id: str,
        broker: str,
        symbol: str,
        order_time: datetime,
        execution_time: Optional[datetime] = None,
        requested_price: Optional[float] = None,
        executed_price: Optional[float] = None,
        quantity: Optional[int] = None,
        status: str = "PENDING",
        strategy_id: Optional[int] = None
    ):
        """Track order execution"""
        latency_ms = None
        slippage = None
        
        if execution_time and order_time:
            latency_ms = int((execution_time - order_time).total_seconds() * 1000)
        
        if requested_price and executed_price and requested_price > 0:
            slippage = float((executed_price - requested_price) / requested_price * 100)
        
        record = ExecutionRecord(
            order_id=order_id,
            broker=broker,
            symbol=symbol,
            strategy_id=strategy_id,
            order_time=order_time,
            execution_time=execution_time,
            latency_ms=latency_ms,
            requested_price=requested_price,
            executed_price=executed_price,
            slippage=slippage,
            quantity=quantity,
            status=status
        )
        
        self.db.add(record)
        self.db.commit()
        
        logger.info(f"Tracked execution: {order_id} - Latency: {latency_ms}ms, Slippage: {slippage}%")
    
    def get_broker_performance(
        self,
        broker: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get broker performance metrics"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        records = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.broker == broker,
            ExecutionRecord.created_at >= cutoff
        ).all()
        
        if not records:
            return {"broker": broker, "no_data": True}
        
        latencies = [r.latency_ms for r in records if r.latency_ms]
        slippages = [r.slippage for r in records if r.slippage]
        
        return {
            "broker": broker,
            "period_hours": hours,
            "total_orders": len(records),
            "avg_latency_ms": statistics.mean(latencies) if latencies else None,
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else None,
            "avg_slippage_percent": statistics.mean(slippages) if slippages else None,
            "fill_rate": len([r for r in records if r.status == "COMPLETE"]) / len(records) * 100
        }
    
    def get_strategy_performance(
        self,
        strategy_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        cutoff = datetime.now() - timedelta(days=days)
        
        records = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.strategy_id == strategy_id,
            ExecutionRecord.created_at >= cutoff
        ).all()
        
        if not records:
            return {"strategy_id": strategy_id, "no_data": True}
        
        return {
            "strategy_id": strategy_id,
            "period_days": days,
            "total_orders": len(records),
            "successful_orders": len([r for r in records if r.status == "COMPLETE"]),
            "avg_slippage": statistics.mean([r.slippage for r in records if r.slippage]) if records else None
        }
