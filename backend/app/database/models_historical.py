"""
Database models for historical OHLC data storage.
"""

from sqlalchemy import Column, Integer, String, Numeric, BigInteger, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class HistoricalOHLC(Base):
    """
    Historical OHLC candlestick data.
    
    Stores time-series price data with quality metrics.
    Complies with Rule #12 (historical data never mixed with real-time silently).
    """
    __tablename__ = "historical_ohlc"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(10), nullable=False, default="NSE")
    interval = Column(String(5), nullable=False)  # 1m, 5m, 15m, 30m, 1h, 1d
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV data
    open = Column(Numeric(12, 2), nullable=True)
    high = Column(Numeric(12, 2), nullable=True)
    low = Column(Numeric(12, 2), nullable=True)
    close = Column(Numeric(12, 2), nullable=True)
    volume = Column(BigInteger, nullable=True)
    
    # Metadata
    source = Column(String(20), nullable=False)  # 'openalgo', 'nse', 'yahoo'
    quality_score = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('symbol', 'exchange', 'interval', 'timestamp', name='uix_symbol_interval_timestamp'),
        Index('idx_ohlc_lookup', 'symbol', 'interval', 'timestamp'),
        Index('idx_ohlc_quality', 'symbol', 'quality_score'),
    )
    
    def __repr__(self):
        return f"<HistoricalOHLC(symbol={self.symbol}, interval={self.interval}, timestamp={self.timestamp}, close={self.close})>"


class DataFetchLog(Base):
    """
    Audit log for data fetching operations.
    
    Compliance:
        - Rule #33-34: Every decision traceable, every execution logged
    """
    __tablename__ = "data_fetch_log"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    interval = Column(String(5), nullable=False)
    source = Column(String(20), nullable=False)
    
    # Request details
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    period = Column(String(10), nullable=True)  # 1d, 1mo, 1y, etc.
    
    # Response details
    success = Column(Integer, nullable=False)  # 1 = success, 0 = failure
    candles_fetched = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    elapsed_ms = Column(Integer, nullable=True)
    
    # Quality metrics
    quality_score = Column(Numeric(3, 2), nullable=True)
    quality_issues = Column(String(1000), nullable=True)  # JSON string
    
    __table_args__ = (
        Index('idx_fetch_log_time', 'requested_at'),
        Index('idx_fetch_log_symbol', 'symbol', 'requested_at'),
    )
    
    def __repr__(self):
        return f"<DataFetchLog(symbol={self.symbol}, success={self.success}, requested_at={self.requested_at})>"


class PriceHistory(Base):
    """
    Simple price history table for NSE data.
    Used by risk metrics calculations.
    """
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric(12, 2))
    high = Column(Numeric(12, 2))
    low = Column(Numeric(12, 2))
    close = Column(Numeric(12, 2))
    volume = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_price_history_symbol_date'),
        Index('idx_price_history_symbol_date', 'symbol', 'date'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(symbol={self.symbol}, date={self.date}, close={self.close})>"


class MarketTick(Base):
    """
    Persistent tick-level storage for all subscribed symbols.
    
    Compliance:
        - Rule #14: Every TradeDecision must include decision_id for traceability (ticks are the foundation).
        - High-performance storage for real-time stream.
    """
    __tablename__ = "market_ticks"
    
    id = Column(BigInteger, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(10), nullable=False, default="NSE")
    ltp = Column(Numeric(12, 2), nullable=False)
    volume = Column(BigInteger, nullable=True)
    oi = Column(BigInteger, nullable=True)
    
    # Time metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)  # Broker/Feed TS
    received_at = Column(DateTime(timezone=True), server_default=func.now(), index=True) # Local TS
    
    __table_args__ = (
        Index('idx_ticks_lookup', 'symbol', 'exchange', 'timestamp'),
        Index('idx_ticks_time', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MarketTick(symbol={self.symbol}, ltp={self.ltp}, ts={self.timestamp})>"
