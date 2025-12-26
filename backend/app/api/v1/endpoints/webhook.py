"""
Webhook Endpoint
Processes webhook signals from external platforms (TradingView, ChartInk, Python).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import pytz

from app.database.models_strategy import WebhookPayload, TradingMode
from app.services.strategy_service import StrategyService
from app.services.order_queue import order_queue
from app.core.database import get_db

router = APIRouter(prefix="/webhook", tags=["Webhook"])
logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


@router.post("/{webhook_id}")
async def process_webhook(
    webhook_id: str,
    payload: WebhookPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process webhook from external platforms.
    
    **Supported Platforms:**
    - TradingView alerts
    - ChartInk scanner
    - Python scripts
    - Manual triggers
    
    **Payload Format:**
    ```json
    {
        "symbol": "RELIANCE",
        "action": "BUY",  // or "SELL"
        "position_size": 100  // For BOTH mode only
    }
    ```
    
    **Trading Modes:**
    - **LONG**: BUY to enter, SELL to exit
    - **SHORT**: SELL to enter, BUY to exit
    - **BOTH**: position_size determines direction (positive=long, negative=short, 0=exit)
    
    **Time Controls (Intraday):**
    - Entry orders only allowed between start_time and end_time
    - Exit orders allowed until squareoff_time
    - Auto-squareoff at squareoff_time
    """
    try:
        # Get strategy by webhook ID
        service = StrategyService(db)
        strategy = await service.get_strategy_by_webhook(webhook_id)
        
        if not strategy:
            logger.warning(f"Invalid webhook ID: {webhook_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid webhook ID"
            )
        
        # Check if strategy is active
        if not strategy.is_active:
            logger.warning(f"Inactive strategy webhook called: {strategy.name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Strategy is inactive"
            )
        
        # Validate payload
        if not payload.symbol or not payload.action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: symbol, action"
            )
        
        # Validate action
        if payload.action.upper() not in ['BUY', 'SELL']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use BUY or SELL"
            )
        
        # Check trading hours for intraday strategies
        if strategy.is_intraday:
            is_valid_time, error_msg = _check_trading_hours(
                strategy,
                payload.action,
                payload.position_size or 0
            )
            
            if not is_valid_time:
                logger.warning(f"Trading hours violation for {strategy.name}: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        
        # Validate trading mode compatibility
        if strategy.trading_mode == TradingMode.BOTH and payload.position_size is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="position_size required for BOTH mode"
            )
        
        # Get symbol mapping
        mappings = await service.get_symbol_mappings(strategy.id)
        mapping = next((m for m in mappings if m.symbol == payload.symbol), None)
        
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No mapping found for symbol {payload.symbol}"
            )
        
        # Determine if this is a smart order (position-aware)
        is_smart_order = _should_use_smart_order(
            strategy.trading_mode,
            payload.action,
            payload.position_size or 0
        )
        
        # Prepare order data
        order_data = {
            "symbol": mapping.symbol,
            "exchange": mapping.exchange,
            "product": mapping.product_type,
            "action": payload.action.upper(),
            "pricetype": "MARKET",
            "strategy": strategy.name,
            "broker": mapping.broker  # Optional specific broker
        }
        
        # Set quantity based on mode
        if strategy.trading_mode == TradingMode.BOTH:
            # For BOTH mode, use position_size
            order_data["quantity"] = str(abs(payload.position_size)) if payload.position_size != 0 else "0"
            order_data["position_size"] = str(payload.position_size)
        else:
            # For LONG/SHORT modes, use mapping quantity
            order_data["quantity"] = str(mapping.quantity) if not is_smart_order else "0"
            if is_smart_order:
                order_data["position_size"] = "0"  # Close position
        
        # Add to order queue
        await order_queue.enqueue_order(
            order_data=order_data,
            is_smart_order=is_smart_order
        )
        
        logger.info(
            f"Webhook processed: {strategy.name} - {payload.symbol} {payload.action} "
            f"(smart={is_smart_order})"
        )
        
        return {
            "status": "success",
            "message": f"Order queued for {payload.symbol}",
            "strategy": strategy.name,
            "is_smart_order": is_smart_order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _check_trading_hours(strategy, action: str, position_size: int) -> tuple[bool, str]:
    """
    Check if current time is within allowed trading hours.
    
    Returns:
        (is_valid, error_message)
    """
    now = datetime.now(IST)
    current_time = now.time()
    
    # Determine if this is an exit order
    is_exit_order = False
    if strategy.trading_mode == TradingMode.LONG:
        is_exit_order = action.upper() == 'SELL'
    elif strategy.trading_mode == TradingMode.SHORT:
        is_exit_order = action.upper() == 'BUY'
    else:  # BOTH mode
        is_exit_order = position_size == 0
    
    # For entry orders, check entry window
    if not is_exit_order:
        if strategy.start_time and current_time < strategy.start_time:
            return False, f"Entry orders not allowed before {strategy.start_time.strftime('%H:%M')}"
        
        if strategy.end_time and current_time > strategy.end_time:
            return False, f"Entry orders not allowed after {strategy.end_time.strftime('%H:%M')}"
    
    # For exit orders, check until squareoff time
    else:
        if strategy.start_time and current_time < strategy.start_time:
            return False, f"Exit orders not allowed before {strategy.start_time.strftime('%H:%M')}"
        
        if strategy.squareoff_time and current_time > strategy.squareoff_time:
            return False, f"Exit orders not allowed after {strategy.squareoff_time.strftime('%H:%M')}"
    
    return True, ""


def _should_use_smart_order(trading_mode: TradingMode, action: str, position_size: int) -> bool:
    """
    Determine if smart order (position-aware) should be used.
    
    Smart orders are used for:
    - LONG mode: SELL (exit)
    - SHORT mode: BUY (exit)
    - BOTH mode: position_size = 0 (exit)
    """
    if trading_mode == TradingMode.LONG:
        return action.upper() == 'SELL'
    elif trading_mode == TradingMode.SHORT:
        return action.upper() == 'BUY'
    else:  # BOTH mode
        return position_size == 0
