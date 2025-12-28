"""
Risk Metrics API Endpoints

Provides endpoints for:
- Value at Risk (VaR)
- Beta calculation
- Sharpe Ratio
- Volatility metrics
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.risk_metrics_service import RiskMetricsService
from app.database.models_risk import RiskMetrics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/risk/{symbol}/var")
async def get_var(
    symbol: str,
    days: int = Query(30, ge=10, le=252, description="Historical window (10-252 days)"),
    confidence: float = Query(0.95, ge=0.90, le=0.99, description="Confidence level (0.90-0.99)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Value at Risk (VaR) for a symbol
    
    VaR represents the maximum expected loss over a given time period
    at a specified confidence level.
    
    Args:
        symbol: Stock symbol
        days: Historical window (default: 30)
        confidence: Confidence level (default: 0.95 = 95%)
        
    Returns:
        VaR metrics with interpretation
    """
    try:
        service = RiskMetricsService(db)
        var = await service.calculate_var(symbol, days, confidence)
        
        if var is None:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data to calculate VaR for {symbol}"
            )
        
        interpretation = service.get_var_interpretation(var, confidence)
        
        return {
            "symbol": symbol,
            "var": var,
            "days": days,
            "confidence": confidence,
            **interpretation,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating VaR for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{symbol}/beta")
async def get_beta(
    symbol: str,
    days: int = Query(252, ge=30, le=504, description="Historical window (30-504 days)"),
    market_symbol: str = Query("NIFTY", description="Market index symbol"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Beta - stock's volatility relative to market
    
    Beta measures how much a stock moves relative to the market.
    
    Args:
        symbol: Stock symbol
        days: Historical window (default: 252 = 1 year)
        market_symbol: Market index (default: NIFTY)
        
    Returns:
        Beta value with interpretation
    """
    try:
        service = RiskMetricsService(db)
        beta = await service.calculate_beta(symbol, market_symbol, days)
        
        if beta is None:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data to calculate Beta for {symbol}"
            )
        
        interpretation = service.get_beta_interpretation(beta)
        
        return {
            "symbol": symbol,
            "beta": beta,
            "days": days,
            "market_symbol": market_symbol,
            **interpretation,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Beta for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{symbol}/sharpe")
async def get_sharpe_ratio(
    symbol: str,
    days: int = Query(252, ge=30, le=504, description="Historical window (30-504 days)"),
    risk_free_rate: float = Query(0.065, ge=0.0, le=0.15, description="Annual risk-free rate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Sharpe Ratio - risk-adjusted return
    
    Sharpe Ratio measures return per unit of risk.
    
    Args:
        symbol: Stock symbol
        days: Historical window (default: 252 = 1 year)
        risk_free_rate: Annual risk-free rate (default: 6.5%)
        
    Returns:
        Sharpe ratio with interpretation
    """
    try:
        service = RiskMetricsService(db)
        sharpe = await service.calculate_sharpe_ratio(symbol, days, risk_free_rate)
        
        if sharpe is None:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data to calculate Sharpe Ratio for {symbol}"
            )
        
        interpretation = service.get_sharpe_interpretation(sharpe)
        
        return {
            "symbol": symbol,
            "sharpe_ratio": sharpe,
            "days": days,
            "risk_free_rate": risk_free_rate,
            **interpretation,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Sharpe Ratio for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{symbol}/all")
async def get_all_metrics(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate all risk metrics for a symbol
    
    Calculates and stores:
    - VaR (95%, 99% for 30d, 60d, 90d)
    - Beta (30d, 60d, 252d)
    - Sharpe Ratio (30d, 60d, 252d)
    - Volatility (30d, 60d, 252d)
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Complete risk metrics
    """
    try:
        service = RiskMetricsService(db)
        metrics = await service.calculate_all_metrics(symbol)
        
        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to calculate risk metrics for {symbol}"
            )
        
        return {
            "symbol": metrics.symbol,
            "calculated_at": metrics.calculated_at.isoformat(),
            "data_points_used": metrics.data_points_used,
            "var": {
                "95_30d": float(metrics.var_95_30d) if metrics.var_95_30d else None,
                "99_30d": float(metrics.var_99_30d) if metrics.var_99_30d else None,
                "95_60d": float(metrics.var_95_60d) if metrics.var_95_60d else None,
                "99_60d": float(metrics.var_99_60d) if metrics.var_99_60d else None,
                "95_90d": float(metrics.var_95_90d) if metrics.var_95_90d else None,
                "99_90d": float(metrics.var_99_90d) if metrics.var_99_90d else None,
            },
            "beta": {
                "30d": float(metrics.beta_30d) if metrics.beta_30d else None,
                "60d": float(metrics.beta_60d) if metrics.beta_60d else None,
                "252d": float(metrics.beta_252d) if metrics.beta_252d else None,
            },
            "sharpe": {
                "30d": float(metrics.sharpe_30d) if metrics.sharpe_30d else None,
                "60d": float(metrics.sharpe_60d) if metrics.sharpe_60d else None,
                "252d": float(metrics.sharpe_252d) if metrics.sharpe_252d else None,
            },
            "volatility": {
                "30d": float(metrics.volatility_30d) if metrics.volatility_30d else None,
                "60d": float(metrics.volatility_60d) if metrics.volatility_60d else None,
                "252d": float(metrics.volatility_252d) if metrics.volatility_252d else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating all metrics for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{symbol}/latest")
async def get_latest_metrics(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the most recently calculated risk metrics for a symbol
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Latest risk metrics from database
    """
    try:
        service = RiskMetricsService(db)
        metrics = await service.get_latest_metrics(symbol)
        
        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"No risk metrics found for {symbol}. Calculate them first using /risk/{symbol}/all"
            )
        
        return {
            "symbol": metrics.symbol,
            "calculated_at": metrics.calculated_at.isoformat(),
            "data_points_used": metrics.data_points_used,
            "var": {
                "95_30d": float(metrics.var_95_30d) if metrics.var_95_30d else None,
                "99_30d": float(metrics.var_99_30d) if metrics.var_99_30d else None,
                "95_60d": float(metrics.var_95_60d) if metrics.var_95_60d else None,
                "99_60d": float(metrics.var_99_60d) if metrics.var_99_60d else None,
            },
            "beta": {
                "30d": float(metrics.beta_30d) if metrics.beta_30d else None,
                "60d": float(metrics.beta_60d) if metrics.beta_60d else None,
                "252d": float(metrics.beta_252d) if metrics.beta_252d else None,
            },
            "sharpe": {
                "30d": float(metrics.sharpe_30d) if metrics.sharpe_30d else None,
                "60d": float(metrics.sharpe_60d) if metrics.sharpe_60d else None,
                "252d": float(metrics.sharpe_252d) if metrics.sharpe_252d else None,
            },
            "volatility": {
                "30d": float(metrics.volatility_30d) if metrics.volatility_30d else None,
                "60d": float(metrics.volatility_60d) if metrics.volatility_60d else None,
                "252d": float(metrics.volatility_252d) if metrics.volatility_252d else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest metrics for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
