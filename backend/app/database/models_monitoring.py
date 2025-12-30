"""
Database Models for Monitoring and Observability
Tracks latency, traffic, errors, and P&L metrics
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from app.core.database import Base

IST = pytz.timezone('Asia/Kolkata')


class LatencyMetric(Base):
    """Track operation latency metrics"""
    __tablename__ = "latency_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # 'order_execution', 'api_call', 'websocket'
    operation = Column(String(100), nullable=False, index=True)   # 'place_order', 'GET /api/v1/health', etc.
    latency_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST), index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    additional_metadata = Column("metadata", JSON, nullable=True)  # Additional context
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_latency_type_timestamp', 'metric_type', 'timestamp'),
        Index('ix_latency_operation_timestamp', 'operation', 'timestamp'),
    )


class APITraffic(Base):
    """Track API usage and traffic patterns"""
    __tablename__ = "api_traffic"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST), index=True)
    
    # Indexes for analytics
    __table_args__ = (
        Index('ix_traffic_endpoint_timestamp', 'endpoint', 'timestamp'),
        Index('ix_traffic_status_timestamp', 'status_code', 'timestamp'),
        Index('ix_traffic_user_timestamp', 'user_id', 'timestamp'),
    )


class ErrorLog(Base):
    """Track errors and exceptions"""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    error_type = Column(String(100), nullable=False, index=True)  # 'ValidationError', 'DatabaseError', etc.
    error_message = Column(String(1000), nullable=False)
    stack_trace = Column(String(5000), nullable=True)
    endpoint = Column(String(200), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    severity = Column(String(20), nullable=False, default='ERROR', index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST), index=True)
    additional_metadata = Column("metadata", JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_error_type_timestamp', 'error_type', 'timestamp'),
        Index('ix_error_severity_timestamp', 'severity', 'timestamp'),
    )


class PnLSnapshot(Base):
    """Real-time P&L snapshots"""
    __tablename__ = "pnl_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    total_pnl = Column(Float, nullable=False, default=0.0)
    day_pnl = Column(Float, nullable=False, default=0.0)
    positions_count = Column(Integer, nullable=False, default=0)
    trades_count = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST), index=True)
    
    # Relationship
    user = relationship("User", backref="pnl_snapshots")
    
    # Indexes
    __table_args__ = (
        Index('ix_pnl_user_timestamp', 'user_id', 'timestamp'),
    )


class TradePerformance(Base):
    """Per-trade performance metrics"""
    __tablename__ = "trade_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=True, index=True)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    holding_time_minutes = Column(Integer, nullable=True)
    trade_type = Column(String(10), nullable=False)  # 'LONG', 'SHORT'
    status = Column(String(20), nullable=False, default='OPEN', index=True)  # 'OPEN', 'CLOSED'
    
    # Relationship
    user = relationship("User", backref="trade_performances")
    
    # Indexes
    __table_args__ = (
        Index('ix_trade_user_symbol', 'user_id', 'symbol'),
        Index('ix_trade_strategy_status', 'strategy_name', 'status'),
        Index('ix_trade_entry_time', 'entry_time'),
    )


class SystemHealth(Base):
    """System health metrics"""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)  # 'cpu_usage', 'memory_usage', 'db_connections'
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # '%', 'MB', 'count'
    status = Column(String(20), nullable=False, default='HEALTHY')  # 'HEALTHY', 'WARNING', 'CRITICAL'
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST), index=True)
    additional_metadata = Column("metadata", JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_health_metric_timestamp', 'metric_name', 'timestamp'),
    )
