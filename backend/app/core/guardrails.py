# app/core/guardrails.py

import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class LiveGuardrails:
    """
    Final pre-flight safety checks for LIVE trading.
    Enforces whitelists and limits to prevent catastrophic errors.
    """
    
    # Configuration (Could be moved to a YAML or DB later)
    WHITELISTED_SYMBOLS = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY", "NSE:HDFCBANK", "NSE:ICICIBANK"]
    WHITELISTED_EXCHANGES = ["NSE", "NSE_INDEX"]
    WHITELISTED_STRATEGIES = ["QUAD_V1"]
    
    MAX_QUANTITY_PER_TRADE = 100
    MAX_NOTIONAL_PER_TRADE = 500000.0 # 5 Lakh INR
    MAX_TRADES_PER_SYMBOL_DAY = 10
    
    @classmethod
    async def validate_execution(cls, symbol: str, payload: Dict[str, Any], decision: Any, db: Any) -> tuple[bool, Optional[str]]:
        """
        Comprehensive guardrail validation.
        Returns (is_allowed, block_reason)
        """
        # 1. Exchange Whitelist
        exchange = symbol.split(":")[0] if ":" in symbol else "NSE"
        if exchange not in cls.WHITELISTED_EXCHANGES:
            return False, f"EXCHANGE_NOT_WHITELISTED: {exchange}"
            
        # 2. Symbol Whitelist
        target_symbol = symbol if ":" in symbol else f"NSE:{symbol}"
        if target_symbol not in cls.WHITELISTED_SYMBOLS:
             return False, f"SYMBOL_NOT_WHITELISTED: {target_symbol}"
             
        # 3. Strategy Whitelist
        if decision.strategy_name not in cls.WHITELISTED_STRATEGIES:
            return False, f"STRATEGY_NOT_WHITELISTED: {decision.strategy_name}"
            
        # 4. Quantity Limit
        qty = payload.get("quantity", 0)
        if qty > cls.MAX_QUANTITY_PER_TRADE:
            return False, f"MAX_QUANTITY_EXCEEDED: {qty} > {cls.MAX_QUANTITY_PER_TRADE}"
            
        # 5. Notional Value Limit
        price = decision.decision_ltp
        notional = qty * price
        if notional > cls.MAX_NOTIONAL_PER_TRADE:
             return False, f"MAX_NOTIONAL_EXCEEDED: {notional:.0f} > {cls.MAX_NOTIONAL_PER_TRADE}"
             
        # 6. Trade Frequency (Symbol/Day) [Audit Re-check]
        # In a real system, we'd query the DB for today's trade count for this symbol
        # For now, we'll assume a basic check or placeholder
        # TODO: Implement DB-based frequency check
        
        return True, None
