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
from app.services.strategy_executor import StrategyExecutor
from app.core.database import get_db
from app.core.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

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


# Strategy Code Management Endpoints

class CodeValidationRequest(BaseModel):
    code: str

class CodeValidationResponse(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]
    timestamp: str

class BacktestRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100000.0
    slippage_pct: float = 0.001
    commission_fixed: float = 20.0
    params: Optional[Dict[str, Any]] = None

class BacktestResponse(BaseModel):
    symbol: str
    total_trades: int
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    final_capital: float
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    max_drawdown: float = 0.0
    error: Optional[str] = None


@router.post("/validate-code", response_model=CodeValidationResponse)
async def validate_strategy_code(
    request: CodeValidationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Validate strategy code before saving.
    
    Checks for:
    - Syntax errors
    - Dangerous imports/functions
    - Required methods (setup, on_data)
    - StrategyBase inheritance
    """
    executor = StrategyExecutor(db)
    result = await executor.validate_strategy_code(request.code)
    
    return CodeValidationResponse(**result)


@router.post("/{strategy_id}/backtest", response_model=BacktestResponse)
async def backtest_strategy(
    strategy_id: int,
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Backtest a strategy against historical data.
    
    - **symbol**: Stock symbol to backtest
    - **start_date**: Start date (YYYY-MM-DD, optional)
    - **end_date**: End date (YYYY-MM-DD, optional)
    - **initial_capital**: Starting capital (default: 100,000)
    - **params**: Strategy parameters (optional)
    
    Returns backtest results with equity curve and trade history.
    """
    try:
        # Verify ownership
        service = StrategyService(db)
        strategy = await service.get_strategy(strategy_id, current_user)
        
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
        
        # Get historical data (placeholder - integrate with your data service)
        # For now, we'll return an error if no data service is available
        from app.services.data_aggregator import DataAggregator
        
        data_service = DataAggregator(db)
        historical_data = await data_service.get_historical_data(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if historical_data is None or historical_data.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for {request.symbol}"
            )
        
        # Run backtest
        executor = StrategyExecutor(db)
        result = await executor.backtest_strategy(
            strategy_id=strategy_id,
            symbol=request.symbol,
            historical_data=historical_data,
            params=request.params,
            initial_capital=request.initial_capital,
            slippage_pct=request.slippage_pct,
            commission_fixed=request.commission_fixed
        )
        
        if "error" in result:
            return BacktestResponse(
                symbol=request.symbol,
                total_trades=0,
                equity_curve=[],
                trades=[],
                final_capital=request.initial_capital,
                error=result["error"]
            )
        
        return BacktestResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backtesting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/{strategy_id}/code")
async def get_strategy_code(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get strategy code for editing.
    
    Returns the Python code for the strategy.
    """
    service = StrategyService(db)
    strategy = await service.get_strategy(strategy_id, current_user)
    
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    return {
        "strategy_id": strategy.id,
        "name": strategy.name,
        "code": strategy.strategy_code or "",
        "platform": strategy.platform
    }


@router.put("/{strategy_id}/code")
async def update_strategy_code(
    strategy_id: int,
    request: CodeValidationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update strategy code.
    
    Validates code before saving.
    """
    # Validate code first
    executor = StrategyExecutor(db)
    validation = await executor.validate_strategy_code(request.code)
    
    if not validation['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code: {', '.join(validation['errors'])}"
        )
    
    # Update strategy
    service = StrategyService(db)
    strategy = await service.get_strategy(strategy_id, current_user)
    
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    
    # Update code
    strategy.strategy_code = request.code
    strategy.updated_at = datetime.now()
    await db.commit()
    await db.refresh(strategy)
    
    return {
        "strategy_id": strategy.id,
        "name": strategy.name,
        "code": strategy.strategy_code,
        "updated_at": strategy.updated_at.isoformat(),
        "validation": validation
    }

