"""
Symbol Transformation Service
Normalizes symbols between different broker formats.
"""

import logging
from typing import Dict, Optional
from app.brokers.base_adapter import BrokerType

logger = logging.getLogger(__name__)


class SymbolTransformer:
    """
    Transform symbols between standard format and broker-specific formats.
    
    Standard Format: NSE:RELIANCE
    
    Broker Formats:
        - Zerodha: RELIANCE
        - Angel One: RELIANCE-EQ
        - Fyers: NSE:RELIANCE-EQ
        - Dhan: Uses security_id (requires lookup)
        - Upstox: NSE_EQ|RELIANCE
    
    Usage:
        transformer = SymbolTransformer()
        br_symbol = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.FYERS)
        # Returns: "NSE:RELIANCE-EQ"
    """
    
    def __init__(self):
        self._symbol_cache: Dict[str, str] = {}
        logger.info("SymbolTransformer initialized")
    
    def to_broker_format(
        self,
        symbol: str,
        exchange: str = "NSE",
        broker: BrokerType = BrokerType.ZERODHA
    ) -> str:
        """
        Convert standard symbol to broker-specific format.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange name (e.g., "NSE", "BSE")
            broker: Target broker type
            
        Returns:
            Broker-specific symbol format
        """
        cache_key = f"{broker.value}:{exchange}:{symbol}"
        
        # Check cache
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        # Transform based on broker
        if broker == BrokerType.ZERODHA:
            # Zerodha: Just symbol name
            br_symbol = symbol
            
        elif broker == BrokerType.ANGELONE:
            # Angel One: SYMBOL-EQ
            br_symbol = f"{symbol}-EQ"
            
        elif broker == BrokerType.FYERS:
            # Fyers: EXCHANGE:SYMBOL-EQ
            br_symbol = f"{exchange}:{symbol}-EQ"
            
        elif broker == BrokerType.DHAN:
            # Dhan: Uses security_id (requires database lookup)
            # For now, return symbol as-is
            br_symbol = symbol
            logger.warning(f"Dhan requires security_id lookup for {symbol}")
            
        elif broker == BrokerType.UPSTOX:
            # Upstox: EXCHANGE_EQ|SYMBOL
            br_symbol = f"{exchange}_EQ|{symbol}"
            
        elif broker == BrokerType.FINVASIA:
            # Finvasia (Shoonya): NSE:SYMBOL-EQ
            br_symbol = f"{exchange}:{symbol}-EQ"
            
        else:
            # Default: return symbol as-is
            br_symbol = symbol
            logger.warning(f"Unknown broker format for {broker.value}, using symbol as-is")
        
        # Cache result
        self._symbol_cache[cache_key] = br_symbol
        
        logger.debug(f"Transformed {symbol} → {br_symbol} for {broker.value}")
        return br_symbol
    
    def from_broker_format(
        self,
        br_symbol: str,
        exchange: str = "NSE",
        broker: BrokerType = BrokerType.ZERODHA
    ) -> str:
        """
        Convert broker-specific symbol to standard format.
        
        Args:
            br_symbol: Broker-specific symbol
            exchange: Exchange name
            broker: Source broker type
            
        Returns:
            Standard symbol format (e.g., "RELIANCE")
        """
        if broker == BrokerType.ZERODHA:
            # Zerodha: Already in simple format
            return br_symbol
            
        elif broker == BrokerType.ANGELONE:
            # Angel One: Remove -EQ suffix
            return br_symbol.replace("-EQ", "")
            
        elif broker == BrokerType.FYERS:
            # Fyers: Remove EXCHANGE: prefix and -EQ suffix
            symbol = br_symbol.split(":")[-1]  # Remove exchange prefix
            symbol = symbol.replace("-EQ", "")  # Remove -EQ suffix
            return symbol
            
        elif broker == BrokerType.DHAN:
            # Dhan: Return as-is (would need reverse lookup)
            return br_symbol
            
        elif broker == BrokerType.UPSTOX:
            # Upstox: Extract symbol from EXCHANGE_EQ|SYMBOL
            return br_symbol.split("|")[-1]
            
        elif broker == BrokerType.FINVASIA:
            # Finvasia: Remove EXCHANGE: prefix and -EQ suffix
            symbol = br_symbol.split(":")[-1]
            symbol = symbol.replace("-EQ", "")
            return symbol
            
        else:
            # Default: return as-is
            return br_symbol
    
    def get_standard_format(self, symbol: str, exchange: str = "NSE") -> str:
        """
        Get standard format: EXCHANGE:SYMBOL
        
        Args:
            symbol: Symbol name
            exchange: Exchange name
            
        Returns:
            Standard format (e.g., "NSE:RELIANCE")
        """
        return f"{exchange}:{symbol}"
    
    def clear_cache(self):
        """Clear the symbol transformation cache"""
        self._symbol_cache.clear()
        logger.info("Symbol transformation cache cleared")


# Global singleton instance
symbol_transformer = SymbolTransformer()
