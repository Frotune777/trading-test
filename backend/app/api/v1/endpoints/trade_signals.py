"""
Trade Signals API Endpoints

Provides:
- Entry/Exit zones
- Support/Resistance levels
- Stop-Loss and Take-Profit setups
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.trade_signals_service import TradeSignalsService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/trade-signals/{symbol}/setup")
async def get_trade_setup(
    symbol: str,
    price: Optional[float] = Query(None, description="Custom current price"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get professional trade setup for a symbol
    
    Includes:
    - Support and Resistance zones
    - Recommended SL and TP targets
    - Risk/Reward parameters
    """
    try:
        service = TradeSignalsService(db)
        setup = await service.get_trade_setup(symbol, price)
        
        if "error" in setup:
            raise HTTPException(status_code=404, detail=setup["error"])
            
        return setup
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating trade setup for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
