"""
Strategy API Endpoints
RESTful API for strategy management and webhook automation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.models_strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    SymbolMappingCreate,
    SymbolMappingResponse,
    SymbolMappingBulkCreate
)
from app.services.strategy_service import StrategyService, get_webhook_url
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/strategy", tags=["Strategy Management"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new trading strategy.
    
    - **name**: Strategy name (3-50 chars, alphanumeric + spaces/hyphens/underscores)
    - **platform**: TradingView, ChartInk, Python, or Manual
    - **is_intraday**: Whether strategy is intraday (requires time controls)
    - **trading_mode**: LONG (buy to enter), SHORT (sell to enter), or BOTH (position_size based)
    - **start_time**: Entry window start (HH:MM format, intraday only)
    - **end_time**: Entry window end (HH:MM format, intraday only)
    - **squareoff_time**: Auto-squareoff time (HH:MM format, intraday only)
    
    Returns strategy with unique webhook_id for external platform integration.
    """
    try:
        service = StrategyService(db)
        strategy = await service.create_strategy(current_user, data)
        
        # Build response
        return StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            webhook_id=strategy.webhook_id,
            webhook_url=get_webhook_url(strategy.webhook_id),
            user_id=strategy.user_id,
            platform=strategy.platform,
            is_active=strategy.is_active,
            is_intraday=strategy.is_intraday,
            trading_mode=strategy.trading_mode,
            start_time=strategy.start_time.strftime('%H:%M') if strategy.start_time else None,
            end_time=strategy.end_time.strftime('%H:%M') if strategy.end_time else None,
            squareoff_time=strategy.squareoff_time.strftime('%H:%M') if strategy.squareoff_time else None,
            description=strategy.description,
            symbol_count=len(strategy.symbol_mappings),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create strategy")


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List all strategies for current user."""
    service = StrategyService(db)
    strategies = await service.get_user_strategies(current_user)
    
    return [
        StrategyResponse(
            id=s.id,
            name=s.name,
            webhook_id=s.webhook_id,
            webhook_url=get_webhook_url(s.webhook_id),
            user_id=s.user_id,
            platform=s.platform,
            is_active=s.is_active,
            is_intraday=s.is_intraday,
            trading_mode=s.trading_mode,
            start_time=s.start_time.strftime('%H:%M') if s.start_time else None,
            end_time=s.end_time.strftime('%H:%M') if s.end_time else None,
            squareoff_time=s.squareoff_time.strftime('%H:%M') if s.squareoff_time else None,
            description=s.description,
            symbol_count=len(s.symbol_mappings),
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in strategies
    ]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get strategy by ID."""
    service = StrategyService(db)
    strategy = await service.get_strategy(strategy_id, current_user)
    
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        webhook_id=strategy.webhook_id,
        webhook_url=get_webhook_url(strategy.webhook_id),
        user_id=strategy.user_id,
        platform=strategy.platform,
        is_active=strategy.is_active,
        is_intraday=strategy.is_intraday,
        trading_mode=strategy.trading_mode,
        start_time=strategy.start_time.strftime('%H:%M') if strategy.start_time else None,
        end_time=strategy.end_time.strftime('%H:%M') if strategy.end_time else None,
        squareoff_time=strategy.squareoff_time.strftime('%H:%M') if strategy.squareoff_time else None,
        description=strategy.description,
        symbol_count=len(strategy.symbol_mappings),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at
    )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update strategy."""
    try:
        service = StrategyService(db)
        strategy = await service.update_strategy(strategy_id, current_user, data)
        
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
        
        return StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            webhook_id=strategy.webhook_id,
            webhook_url=get_webhook_url(strategy.webhook_id),
            user_id=strategy.user_id,
            platform=strategy.platform,
            is_active=strategy.is_active,
            is_intraday=strategy.is_intraday,
            trading_mode=strategy.trading_mode,
            start_time=strategy.start_time.strftime('%H:%M') if strategy.start_time else None,
            end_time=strategy.end_time.strftime('%H:%M') if strategy.end_time else None,
            squareoff_time=strategy.squareoff_time.strftime('%H:%M') if strategy.squareoff_time else None,
            description=strategy.description,
            symbol_count=len(strategy.symbol_mappings),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/toggle", response_model=StrategyResponse)
async def toggle_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Toggle strategy active status."""
    service = StrategyService(db)
    strategy = await service.toggle_strategy(strategy_id, current_user)
    
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        webhook_id=strategy.webhook_id,
        webhook_url=get_webhook_url(strategy.webhook_id),
        user_id=strategy.user_id,
        platform=strategy.platform,
        is_active=strategy.is_active,
        is_intraday=strategy.is_intraday,
        trading_mode=strategy.trading_mode,
        start_time=strategy.start_time.strftime('%H:%M') if strategy.start_time else None,
        end_time=strategy.end_time.strftime('%H:%M') if strategy.end_time else None,
        squareoff_time=strategy.squareoff_time.strftime('%H:%M') if strategy.squareoff_time else None,
        description=strategy.description,
        symbol_count=len(strategy.symbol_mappings),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at
    )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete strategy (cascade deletes symbol mappings)."""
    service = StrategyService(db)
    success = await service.delete_strategy(strategy_id, current_user)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    return None


# Symbol Mapping Endpoints

@router.post("/{strategy_id}/symbols", response_model=SymbolMappingResponse, status_code=status.HTTP_201_CREATED)
async def add_symbol_mapping(
    strategy_id: int,
    data: SymbolMappingCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Add symbol mapping to strategy.
    
    - **symbol**: Stock symbol (e.g., "RELIANCE")
    - **exchange**: Exchange (NSE, BSE, NFO, etc.)
    - **quantity**: Order quantity
    - **product_type**: MIS (intraday), CNC (delivery), NRML (F&O)
    - **broker**: Optional specific broker (None = auto-select best broker)
    """
    try:
        service = StrategyService(db)
        mapping = await service.add_symbol_mapping(strategy_id, current_user, data)
        
        if not mapping:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
        
        return SymbolMappingResponse(
            id=mapping.id,
            strategy_id=mapping.strategy_id,
            symbol=mapping.symbol,
            exchange=mapping.exchange,
            quantity=mapping.quantity,
            product_type=mapping.product_type,
            broker=mapping.broker,
            created_at=mapping.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{strategy_id}/symbols", response_model=List[SymbolMappingResponse])
async def list_symbol_mappings(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List all symbol mappings for strategy."""
    service = StrategyService(db)
    
    # Verify ownership
    strategy = await service.get_strategy(strategy_id, current_user)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    mappings = await service.get_symbol_mappings(strategy_id)
    
    return [
        SymbolMappingResponse(
            id=m.id,
            strategy_id=m.strategy_id,
            symbol=m.symbol,
            exchange=m.exchange,
            quantity=m.quantity,
            product_type=m.product_type,
            broker=m.broker,
            created_at=m.created_at
        )
        for m in mappings
    ]


@router.delete("/{strategy_id}/symbols/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symbol_mapping(
    strategy_id: int,
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Delete symbol mapping."""
    service = StrategyService(db)
    success = await service.delete_symbol_mapping(mapping_id, current_user)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol mapping not found")
    
    return None
