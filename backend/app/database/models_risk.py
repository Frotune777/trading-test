"""
Risk Metrics Database Models

Stores calculated risk metrics including VaR, Beta, Sharpe Ratio, and Volatility.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from app.database.models_quad import Base


class RiskMetrics(Base):
    """Risk metrics for stocks"""
    __tablename__ = 'risk_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Value at Risk (VaR) - Different confidence levels and windows
    var_95_30d = Column(DECIMAL(10, 4), comment="95% VaR, 30-day window")
    var_99_30d = Column(DECIMAL(10, 4), comment="99% VaR, 30-day window")
    var_95_60d = Column(DECIMAL(10, 4), comment="95% VaR, 60-day window")
    var_99_60d = Column(DECIMAL(10, 4), comment="99% VaR, 60-day window")
    var_95_90d = Column(DECIMAL(10, 4), comment="95% VaR, 90-day window")
    var_99_90d = Column(DECIMAL(10, 4), comment="99% VaR, 90-day window")
    
    # Beta (market correlation)
    beta_30d = Column(DECIMAL(10, 4), comment="30-day beta vs NIFTY")
    beta_60d = Column(DECIMAL(10, 4), comment="60-day beta vs NIFTY")
    beta_252d = Column(DECIMAL(10, 4), comment="252-day beta vs NIFTY (1 year)")
    
    # Sharpe Ratio (risk-adjusted returns)
    sharpe_30d = Column(DECIMAL(10, 4), comment="30-day Sharpe ratio")
    sharpe_60d = Column(DECIMAL(10, 4), comment="60-day Sharpe ratio")
    sharpe_252d = Column(DECIMAL(10, 4), comment="252-day Sharpe ratio")
    
    # Volatility (annualized standard deviation)
    volatility_30d = Column(DECIMAL(10, 4), comment="30-day annualized volatility")
    volatility_60d = Column(DECIMAL(10, 4), comment="60-day annualized volatility")
    volatility_252d = Column(DECIMAL(10, 4), comment="252-day annualized volatility")
    
    # Metadata
    data_points_used = Column(Integer, comment="Number of data points in calculation")
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_risk_metrics_symbol_date', 'symbol', 'calculated_at'),
    )
    
    def __repr__(self):
        return f"<RiskMetrics(symbol={self.symbol}, var_95_30d={self.var_95_30d}, beta_252d={self.beta_252d})>"
