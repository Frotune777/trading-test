"""
Base Broker Adapter Interface
Defines the contract that all broker adapters must implement.
Supports: Zerodha, Finvasia, Angel One, Upstox, Fyers, OpenAlgo
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import pandas as pd
from pydantic import BaseModel


class BrokerType(Enum):
    """Supported broker types"""
    ZERODHA = "zerodha"
    FINVASIA = "finvasia"
    ANGELONE = "angelone"
    UPSTOX = "upstox"
    FYERS = "fyers"
    DHAN = "dhan"
    OPENALGO = "openalgo"


class HealthStatus(Enum):
    """Broker health status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class Order(BaseModel):
    """Order model for execution"""
    symbol: str
    exchange: str
    order_type: str  # MARKET, LIMIT
    transaction_type: str  # BUY, SELL
    quantity: int
    price: Optional[float] = None
    product: str = "MIS"  # MIS, CNC, NRML
    validity: str = "DAY"


class Position(BaseModel):
    """Position model"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    pnl: float
    product: str


class BrokerHealth(BaseModel):
    """Broker health status model"""
    broker_name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    uptime_percent: Optional[float] = None
    last_successful_call: Optional[datetime] = None
    message: str = ""


class BrokerAdapter(ABC):
    """
    Abstract base class for all broker adapters.
    
    All broker implementations (Zerodha, Finvasia, Angel One, etc.) 
    must implement this interface to ensure consistency.
    
    Compliance:
        - Rule #1-3: No execution without gate (place_order checks gate)
        - Rule #6: Fail closed on errors
        - Rule #33-37: All operations logged
    """
    
    def __init__(self, broker_type: BrokerType):
        self.broker_type = broker_type
        self._connected = False
    
    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return human-readable broker name"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to broker API.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to broker API.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange name (default: "NSE")
            
        Returns:
            LTP as float, or None if failed
            
        Compliance:
            - Rule #8-9: Must cache in Redis with 5s TTL
            - Rule #6: Return None on failure (fail closed)
        """
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        exchange: str = "NSE"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLC data.
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 1d)
            from_date: Start date
            to_date: End date
            exchange: Exchange name
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            None if failed
            
        Compliance:
            - Rule #12: Historical data never mixed with real-time silently
            - Rule #6: Return None on failure (fail closed)
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> Optional[List[Position]]:
        """
        Get current positions from broker.
        
        Returns:
            List of Position objects, or None if failed
            
        Compliance:
            - Used for position reconciliation (Rule #38: UI reflects backend truth)
        """
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Place an order with the broker.
        
        Args:
            order: Order object with details
            
        Returns:
            Order response dict with order_id, status, etc.
            None if failed or execution gate blocked
            
        Compliance:
            - Rule #1-3: MUST check execution gate before placing
            - Rule #34: Every execution attempt must be logged
            - Rule #6: Return None on failure (fail closed)
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a placed order.
        
        Args:
            order_id: Broker's order ID
            
        Returns:
            Order status dict, or None if failed
        """
        pass
    
    @abstractmethod
    async def get_health_status(self) -> BrokerHealth:
        """
        Get current health status of this broker adapter.
        
        Returns:
            BrokerHealth object with status and metrics
            
        Compliance:
            - Rule #11: Feed health monitoring
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if adapter is connected"""
        return self._connected
