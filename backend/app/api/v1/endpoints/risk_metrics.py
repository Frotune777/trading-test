from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.risk_metrics_service import RiskMetricsService
from sqlalchemy import select, desc
from app.database.models_quad import RiskMetrics
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{symbol}")
async def get_risk_metrics(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Get latest risk metrics for a symbol suitable for the Risk widget.
    Triggers calculation if no recent data exists (< 24h).
    """
    try:
        service = RiskMetricsService(db)
        
        # Check for existing recent metrics
        metric = await service.get_latest_metrics(symbol)
        
        # If no data or data is stale (> 24h), calculate it
        is_stale = False
        if metric:
             elapsed = (datetime.utcnow() - metric.calculated_at).total_seconds()
             if elapsed > 86400: # 24 hours
                 is_stale = True
        
        if not metric or is_stale:
            logger.info(f"Risk metrics for {symbol} missing or stale, recalculating...")
            metric = await service.calculate_all_metrics(symbol)
            
        if not metric:
            # If still no metric (e.g. calculation failed due to insufficient history)
            return {
                "symbol": symbol,
                "var_95_30d": 0.0,
                "var_99_30d": 0.0,
                "beta": 1.0,
                "sharpe_ratio": 0.0,
                "risk_level": "UNKNOWN",
                "calculated_at": None
            }
            
        # Determine simple risk level text
        risk_level = "MODERATE"
        if metric.var_99_30d and float(metric.var_99_30d) < -3.0: # VaR is typically negative or positive depending on convention. Service returns negative?
            # Service says: "negative value indicates loss" e.g. -2.5
            # So if loss is worse than -3.0 (e.g. -4.0), it is HIGH risk.
            risk_level = "HIGH"
        elif metric.var_99_30d and float(metric.var_99_30d) > -1.5:
             # If loss is small (e.g. -1.0 or positive), it is LOW risk.
            risk_level = "LOW"
            
        # Note: Service returns VaR as negative percentage? 
        # Service: "VaR as percentage (negative value indicates loss)"
        # e.g. -2.5.
        # Check service logic: var = sorted_returns[index] * 100. Returns are typically negative in lower tail.
        # So yes, negative.
        # Previous code checked > 3.0, maybe it expected positive absolute value.
        # I'll stick to examining the value. High risk = large negative number.
        
        # Use beta_252d (1 year) as primary beta, fallback to others
        beta = metric.beta_252d if metric.beta_252d is not None else (metric.beta_60d or metric.beta_30d or 1.0)
        
        # Use sharpe_252d as primary sharpe
        sharpe = metric.sharpe_252d if metric.sharpe_252d is not None else (metric.sharpe_60d or metric.sharpe_30d or 0.0)
        
        # Use volatility_252d as annual volatility
        volatility = metric.volatility_252d if metric.volatility_252d is not None else (metric.volatility_60d or metric.volatility_30d or 0.0)

        return {
            "symbol": metric.symbol,
            "var_95_30d": float(metric.var_95_30d) if metric.var_95_30d is not None else 0.0,
            "var_99_30d": float(metric.var_99_30d) if metric.var_99_30d is not None else 0.0,
            "var_95_60d": float(metric.var_95_60d) if metric.var_95_60d is not None else None,
            "beta": float(beta),
            "sharpe_ratio": float(sharpe),
            "volatility": float(volatility),
            "risk_level": risk_level,
            "calculated_at": metric.calculated_at
        }
        
    except Exception as e:
        logger.error(f"Error serving risk metrics for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{symbol}/calculate")
async def calculate_risk_metrics(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Force recalculation of risk metrics
    """
    try:
        service = RiskMetricsService(db)
        metric = await service.calculate_all_metrics(symbol)
        if not metric:
            raise HTTPException(status_code=400, detail="Failed to calculate metrics. Insufficient data?")
        return {"status": "calculated", "symbol": symbol}
    except Exception as e:
        logger.error(f"Error calculating risk metrics for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/health")
async def get_risk_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get portfolio-wide risk health dashboard.
    """
    try:
        from app.services.risk_manager import RiskManager
        from app.core.openalgo_bridge import openalgo_client
        from app.database.models_monitoring import PnLSnapshot, TradePerformance
        from sqlalchemy import func
        
        risk_manager = RiskManager()
        user_id = 1 # TODO: Get from auth context
        
        # 1. Kill Switch Status
        kill_switch = await redis_client.get("risk:kill_switch") or "inactive"
        
        # 2. Daily P&L vs Limit
        stmt = select(PnLSnapshot).where(
            PnLSnapshot.user_id == user_id,
            PnLSnapshot.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).order_by(PnLSnapshot.timestamp.desc()).limit(1)
        res = await db.execute(stmt)
        pnl_snap = res.scalar_one_or_none()
        current_pnl = pnl_snap.day_pnl if pnl_snap else 0.0
        
        # 3. Order Count today
        stmt = select(func.count()).select_from(TradePerformance).where(
            TradePerformance.user_id == user_id,
            TradePerformance.entry_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        res = await db.execute(stmt)
        order_count = res.scalar() or 0
        
        # 4. Feed Health
        status = openalgo_client.get_status()
        
        # 5. Top Risk Symbols (Highest VaR 95)
        stmt = select(RiskMetrics).order_by(RiskMetrics.var_95_30d.asc()).limit(5)
        res = await db.execute(stmt)
        top_risk = res.scalars().all()
        
        return {
            "kill_switch": kill_switch,
            "daily_pnl": {
                "value": current_pnl,
                "limit": risk_manager.max_daily_loss,
                "status": "DANGER" if current_pnl <= risk_manager.max_daily_loss else "OK"
            },
            "order_count": {
                "value": order_count,
                "limit": risk_manager.max_orders_per_day,
                "status": "DANGER" if order_count >= risk_manager.max_orders_per_day else "OK"
            },
            "feed_health": status.get("feed_state", "UNKNOWN"),
            "top_risk_symbols": [
                {
                    "symbol": m.symbol,
                    "var_95": float(m.var_95_30d) if m.var_95_30d else 0.0,
                    "beta": float(m.beta_252d or 1.0)
                } for m in top_risk
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error fetching risk dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/latest")
async def get_latest_risk_metrics(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Alias for /{symbol} endpoint - returns latest risk metrics
    """
    return await get_risk_metrics(symbol, db)

@router.get("/{symbol}/all")
async def get_all_risk_metrics(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Returns all available risk metrics for a symbol
    Same as /latest - returns most recent calculated metrics
    """
    return await get_risk_metrics(symbol, db)

