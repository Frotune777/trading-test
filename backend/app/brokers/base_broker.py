"""
Base Broker Interface
Abstract class defining the standard broker interface for multi-broker support
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrderType(str, Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class TransactionType(str, Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class MarketDataMode(str, Enum):
    """Market data subscription modes"""
    LTP = "LTP"  # Last Traded Price only
    QUOTE = "QUOTE"  # OHLC + LTP
    FULL = "FULL"  # Full market depth


# Request/Response Models

class OrderRequest(BaseModel):
    """Order placement request"""
    symbol: str
    exchange: str
    transaction_type: TransactionType
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    product_type: str = "DELIVERY"  # DELIVERY, INTRADAY, etc.


class OrderResponse(BaseModel):
    """Order placement response"""
    order_id: str
    status: OrderStatus
    message: str
    timestamp: datetime


class Position(BaseModel):
    """Position data"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    ltp: float
    pnl: float
    product_type: str


class Holding(BaseModel):
    """Holding data"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    ltp: float
    pnl: float


class MarketData(BaseModel):
    """Market data tick"""
    symbol: str
    exchange: str
    ltp: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    timestamp: datetime


class BaseBroker(ABC):
    """
    Abstract base class for broker implementations
    All brokers must implement this interface
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize broker with configuration
        
        Args:
            config: Broker-specific configuration
        """
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to broker
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def subscribe_market_data(
        self,
        symbols: List[str],
        mode: MarketDataMode = MarketDataMode.LTP
    ) -> bool:
        """
        Subscribe to market data
        
        Args:
            symbols: List of symbols (e.g., ["NSE:RELIANCE", "NSE:TCS"])
            mode: Subscription mode (LTP, QUOTE, FULL)
            
        Returns:
            True if subscription successful
        """
        pass
    
    @abstractmethod
    async def unsubscribe_market_data(self, symbols: List[str]) -> bool:
        """
        Unsubscribe from market data
        
        Args:
            symbols: List of symbols to unsubscribe
            
        Returns:
            True if unsubscription successful
        """
        pass
    
    @abstractmethod
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """
        Place an order
        
        Args:
            order: Order request details
            
        Returns:
            Order response with order ID and status
        """
        pass
    
    @abstractmethod
    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any]
    ) -> OrderResponse:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID to modify
            modifications: Fields to modify (quantity, price, etc.)
            
        Returns:
            Order response with updated status
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> OrderResponse:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Order response with cancellation status
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """
        Get order status
        
        Args:
            order_id: Order ID
            
        Returns:
            Current order status
        """
        pass
    
    @abstractmethod
    async def get_orders(self) -> List[OrderResponse]:
        """
        Get all orders
        
        Returns:
            List of all orders
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        Get current positions
        
        Returns:
            List of open positions
        """
        pass
    
    @abstractmethod
    async def get_holdings(self) -> List[Holding]:
        """
        Get holdings
        
        Returns:
            List of holdings
        """
        pass
    
    @abstractmethod
    def get_broker_name(self) -> str:
        """
        Get broker name
        
        Returns:
            Broker identifier (e.g., "angelone", "openalgo")
        """
        pass
