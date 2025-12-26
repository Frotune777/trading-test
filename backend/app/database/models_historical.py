"""
Database models for historical OHLC data storage.
"""

from sqlalchemy import Column, Integer, String, Numeric, BigInteger, DateTime, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


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
