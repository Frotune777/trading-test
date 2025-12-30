"""
Risk Management Models
Tracks risk limits, P&L, positions, and kill switch state
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from app.core.database import Base


class RiskLimit(Base):
    """User-defined risk limits"""
    __tablename__ = "risk_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Position limits
    max_positions = Column(Integer, default=10)
    max_position_size = Column(DECIMAL(15, 2), default=100000)  # Per position
    max_portfolio_value = Column(DECIMAL(15, 2), default=1000000)
    
    # Loss limits
    max_daily_loss = Column(DECIMAL(15, 2), default=50000)
    max_weekly_loss = Column(DECIMAL(15, 2), default=100000)
    max_drawdown_pct = Column(Float, default=20.0)
    
    # Concentration limits
    max_sector_concentration_pct = Column(Float, default=30.0)
    max_single_stock_pct = Column(Float, default=10.0)
    
    # Kill switch
    kill_switch_enabled = Column(Boolean, default=False)
    kill_switch_reason = Column(String, nullable=True)
    kill_switch_activated_at = Column(DateTime, nullable=True)
    kill_switch_activated_by = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RiskMetric(Base):
    """Real-time risk metrics snapshot"""
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    # P&L metrics
    total_pnl = Column(DECIMAL(15, 2), default=0)
    daily_pnl = Column(DECIMAL(15, 2), default=0)
    weekly_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    
    # Position metrics
    position_count = Column(Integer, default=0)
    total_exposure = Column(DECIMAL(15, 2), default=0)
    portfolio_value = Column(DECIMAL(15, 2), default=0)
    
    # Risk metrics
    current_drawdown_pct = Column(Float, default=0)
    var_95 = Column(DECIMAL(15, 2), nullable=True)  # Value at Risk
    sharpe_ratio = Column(Float, nullable=True)
    
    # Concentration (JSON: {symbol: percentage})
    concentration_by_symbol = Column(JSON, default={})
    concentration_by_sector = Column(JSON, default={})
    
    # Limit utilization (0-100%)
    position_limit_utilization = Column(Float, default=0)
    daily_loss_limit_utilization = Column(Float, default=0)
    weekly_loss_limit_utilization = Column(Float, default=0)


class KillSwitchLog(Base):
    """Audit log for kill switch activations"""
    __tablename__ = "kill_switch_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    activated_at = Column(DateTime, server_default=func.now())
    activated_by = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    
    # State at activation
    active_positions = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    portfolio_value = Column(DECIMAL(15, 2), default=0)
    
    # Deactivation
    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by = Column(String, nullable=True)
    deactivation_reason = Column(String, nullable=True)


class AlertLog(Base):
    """System alerts and notifications"""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    # Alert details
    alert_type = Column(String, nullable=False)  # CRITICAL, WARNING, INFO
    category = Column(String, nullable=False)  # RISK, DATA, SYSTEM, TRADE
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    # Context
    related_symbol = Column(String, nullable=True)
    related_strategy_id = Column(Integer, nullable=True)
    metadata = Column(JSON, default={})
    
    # Status
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
