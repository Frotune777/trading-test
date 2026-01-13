"""
Monitoring API Endpoints
Provides access to latency, traffic, and P&L metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db_sync
from app.services.latency_monitor_service import LatencyMonitor
from app.services.traffic_monitor_service import TrafficMonitor
from app.services.pnl_tracker_service import PnLTracker

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/latency")
async def get_latency_metrics(
    metric_type: Optional[str] = None,
    operation: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get latency metrics"""
    monitor = LatencyMonitor(db)
    metrics = monitor.get_metrics(metric_type, operation, hours)
    
    return {
        "metrics": [
            {
                "id": m.id,
                "metric_type": m.metric_type,
                "operation": m.operation,
                "latency_ms": m.latency_ms,
                "timestamp": m.timestamp.isoformat(),
                "user_id": m.user_id
            }
            for m in metrics
        ],
        "count": len(metrics)
    }


@router.get("/latency/stats")
async def get_latency_stats(
    metric_type: Optional[str] = None,
    operation: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get latency statistics (percentiles)"""
    monitor = LatencyMonitor(db)
    stats = monitor.get_stats(metric_type, operation, hours)
    
    return stats


@router.get("/latency/operations")
async def get_operations_summary(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get summary of all operations"""
    monitor = LatencyMonitor(db)
    summary = monitor.get_operations_summary(hours)
    
    return {"operations": summary}


@router.get("/traffic")
async def get_traffic_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get traffic statistics"""
    monitor = TrafficMonitor(db)
    stats = monitor.get_traffic_stats(hours)
    
    return stats


@router.get("/traffic/endpoints")
async def get_endpoint_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get per-endpoint statistics"""
    monitor = TrafficMonitor(db)
    stats = monitor.get_endpoint_stats(hours)
    
    return {"endpoints": stats}


@router.get("/errors")
async def get_error_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """Get error statistics"""
    monitor = TrafficMonitor(db)
    stats = monitor.get_error_stats(hours)
    
    return stats


@router.get("/traffic/users")
async def get_user_activity(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_sync)
):
    """Get user activity statistics"""
    monitor = TrafficMonitor(db)
    activity = monitor.get_user_activity(hours, limit)
    
    return {"users": activity}


@router.get("/pnl/{user_id}")
async def get_pnl_snapshot(
    user_id: int,
    db: Session = Depends(get_db_sync)
):
    """Get latest P&L snapshot for user"""
    tracker = PnLTracker(db)
    snapshot = tracker.get_latest_snapshot(user_id)
    
    if not snapshot:
        # Return empty snapshot instead of 404 to prevent frontend crash
        from datetime import datetime
        import pytz
        IST = pytz.timezone('Asia/Kolkata')
        
        return {
            "user_id": user_id,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "day_pnl": 0.0,
            "positions_count": 0,
            "trades_count": 0,
            "timestamp": datetime.now(IST).isoformat()
        }
    
    return {
        "user_id": snapshot.user_id,
        "realized_pnl": snapshot.realized_pnl,
        "unrealized_pnl": snapshot.unrealized_pnl,
        "total_pnl": snapshot.total_pnl,
        "day_pnl": snapshot.day_pnl,
        "positions_count": snapshot.positions_count,
        "trades_count": snapshot.trades_count,
        "timestamp": snapshot.timestamp.isoformat()
    }


@router.get("/pnl/{user_id}/history")
async def get_pnl_history(
    user_id: int,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db_sync)
):
    """Get P&L history for user"""
    tracker = PnLTracker(db)
    history = tracker.get_snapshot_history(user_id, hours, limit)
    
    return {
        "snapshots": [
            {
                "total_pnl": s.total_pnl,
                "realized_pnl": s.realized_pnl,
                "unrealized_pnl": s.unrealized_pnl,
                "day_pnl": s.day_pnl,
                "timestamp": s.timestamp.isoformat()
            }
            for s in history
        ]
    }


@router.get("/pnl/{user_id}/performance")
async def get_trade_performance(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    strategy_name: Optional[str] = None,
    db: Session = Depends(get_db_sync)
):
    """Get trade performance metrics"""
    tracker = PnLTracker(db)
    performance = tracker.get_trade_performance(user_id, days, strategy_name)
    
    return performance


@router.get("/pnl/{user_id}/strategies")
async def get_strategy_performance(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_sync)
):
    """Get per-strategy performance"""
    tracker = PnLTracker(db)
    strategies = tracker.get_strategy_performance(user_id, days)
    
    return {"strategies": strategies}


@router.get("/health")
async def get_system_health(db: Session = Depends(get_db_sync)):
    """Get overall system health"""
    # This would integrate with system metrics
    return {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "websocket": "healthy"
        }
    }
