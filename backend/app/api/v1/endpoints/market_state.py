from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.market_state_service import market_state_service, MarketStateSnapshot

router = APIRouter(prefix="/market-state", tags=["Market State"])
logger = logging.getLogger(__name__)

@router.get("/{symbol}", response_model=MarketStateSnapshot)
async def get_symbol_market_state(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Get unified market state snapshot for a symbol.
    
    Includes:
    - Real-time LTP and basic market data
    - Market depth / Order book
    - Feed health status
    - User-specific state (active trades)
    """
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        snapshot = await market_state_service.get_market_state(
            symbol=symbol,
            user_id=current_user.id,
            db=db
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error fetching market state for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        pass
