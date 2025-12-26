"""
Strategy Database Models
Models for strategy management and webhook-based automation.
"""

from sqlalchemy import Column, Integer, String, Boolean, Time, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, time
import enum
from typing import Optional
from pydantic import BaseModel
import uuid

Base = declarative_base()


class TradingMode(str, enum.Enum):
    """Trading mode enum"""
    LONG = "LONG"      # Only long positions (BUY to enter, SELL to exit)
    SHORT = "SHORT"    # Only short positions (SELL to enter, BUY to exit)
    BOTH = "BOTH"      # Both long and short (position_size determines direction)


class Platform(str, enum.Enum):
    """Trading platform enum"""
    TRADINGVIEW = "TradingView"
    CHARTINK = "ChartInk"
    PYTHON = "Python"
    MANUAL = "Manual"


class Strategy(Base):
    """
    Strategy model for webhook-based automation.
    
    Each strategy has a unique webhook_id that external platforms
    (TradingView, ChartInk, Python scripts) use to send signals.
    """
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    webhook_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    user_id = Column(String(50), nullable=False, index=True)
    platform = Column(SQLEnum(Platform), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False)
    is_intraday = Column(Boolean, default=True, nullable=False)
    
    # Trading mode
    trading_mode = Column(SQLEnum(TradingMode), nullable=False, default=TradingMode.LONG)
    
    # Time controls (for intraday strategies)
    start_time = Column(Time, nullable=True)      # Entry window start
    end_time = Column(Time, nullable=True)        # Entry window end
    squareoff_time = Column(Time, nullable=True)  # Auto-squareoff time
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    symbol_mappings = relationship("StrategySymbolMapping", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', active={self.is_active})>"


class StrategySymbolMapping(Base):
    """
    Symbol mapping for strategy.
    
    Maps which symbols a strategy trades, with quantity and product type.
    Optionally can specify a specific broker for the symbol.
    """
    __tablename__ = "strategy_symbol_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Symbol details
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(10), nullable=False)  # NSE, BSE, NFO, etc.
    quantity = Column(Integer, nullable=False)
    product_type = Column(String(10), nullable=False)  # MIS, CNC, NRML
    
    # Optional: specific broker for this symbol (None = auto-select)
    broker = Column(String(20), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="symbol_mappings")
    
    def __repr__(self):
        return f"<StrategySymbolMapping(strategy_id={self.strategy_id}, symbol='{self.symbol}', qty={self.quantity})>"


# Pydantic models for API

class StrategyCreate(BaseModel):
    """Request model for creating strategy"""
    name: str
    platform: Platform
    is_intraday: bool = True
    trading_mode: TradingMode = TradingMode.LONG
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None
    squareoff_time: Optional[str] = None
    description: Optional[str] = None


class StrategyUpdate(BaseModel):
    """Request model for updating strategy"""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_intraday: Optional[bool] = None
    trading_mode: Optional[TradingMode] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    squareoff_time: Optional[str] = None
    description: Optional[str] = None


class SymbolMappingCreate(BaseModel):
    """Request model for adding symbol to strategy"""
    symbol: str
    exchange: str
    quantity: int
    product_type: str
    broker: Optional[str] = None


class SymbolMappingBulkCreate(BaseModel):
    """Request model for bulk adding symbols"""
    symbols: list[SymbolMappingCreate]


class StrategyResponse(BaseModel):
    """Response model for strategy"""
    id: int
    name: str
    webhook_id: str
    webhook_url: str  # Computed field
    user_id: str
    platform: Platform
    is_active: bool
    is_intraday: bool
    trading_mode: TradingMode
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    squareoff_time: Optional[str] = None
    description: Optional[str] = None
    symbol_count: int  # Computed field
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SymbolMappingResponse(BaseModel):
    """Response model for symbol mapping"""
    id: int
    strategy_id: int
    symbol: str
    exchange: str
    quantity: int
    product_type: str
    broker: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """
    Webhook payload from external platforms.
    
    TradingView example:
    {
        "symbol": "RELIANCE",
        "action": "BUY",
        "position_size": 100  # For BOTH mode
    }
    """
    symbol: str
    action: str  # BUY or SELL
    position_size: Optional[int] = None  # For BOTH mode
    price: Optional[float] = 0.0  # 0 for MARKET
    trigger_price: Optional[float] = 0.0
