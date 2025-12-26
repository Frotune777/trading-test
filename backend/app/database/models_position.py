"""
Position Reconciliation Database Models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ARRAY, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

Base = declarative_base()


class PositionSnapshot(Base):
    """Position snapshot from broker"""
    __tablename__ = "position_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    broker = Column(String(20), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(DECIMAL(10, 2))
    current_price = Column(DECIMAL(10, 2))
    pnl = Column(DECIMAL(12, 2))
    product_type = Column(String(10))
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PositionDiscrepancy(Base):
    """Position discrepancy between local and broker"""
    __tablename__ = "position_discrepancies"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False)
    broker = Column(String(20), nullable=False, index=True)
    local_quantity = Column(Integer)
    broker_quantity = Column(Integer)
    difference = Column(Integer, nullable=False)
    local_avg_price = Column(DECIMAL(10, 2))
    broker_avg_price = Column(DECIMAL(10, 2))
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime)
    resolution_action = Column(Text)
    resolution_method = Column(String(50))  # AUTO, MANUAL, IGNORED


class ReconciliationRun(Base):
    """Reconciliation job execution record"""
    __tablename__ = "reconciliation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    brokers_checked = Column(ARRAY(String), nullable=False)
    total_positions = Column(Integer, default=0)
    discrepancies_found = Column(Integer, default=0)
    auto_corrections = Column(Integer, default=0)
    status = Column(String(20), nullable=False, index=True)  # RUNNING, COMPLETED, FAILED
    error_message = Column(Text)
    duration_ms = Column(Integer)
    completed_at = Column(DateTime)


# Pydantic models for API

class PositionSnapshotResponse(BaseModel):
    """Position snapshot response"""
    id: int
    broker: str
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: Optional[float] = None
    pnl: Optional[float] = None
    product_type: Optional[str] = None
    snapshot_time: datetime
    
    class Config:
        from_attributes = True


class DiscrepancyResponse(BaseModel):
    """Discrepancy response"""
    id: int
    symbol: str
    exchange: str
    broker: str
    local_quantity: Optional[int] = None
    broker_quantity: Optional[int] = None
    difference: int
    local_avg_price: Optional[float] = None
    broker_avg_price: Optional[float] = None
    detected_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    resolution_action: Optional[str] = None
    resolution_method: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReconciliationRunResponse(BaseModel):
    """Reconciliation run response"""
    id: int
    run_time: datetime
    brokers_checked: List[str]
    total_positions: int
    discrepancies_found: int
    auto_corrections: int
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReconciliationReportResponse(BaseModel):
    """Reconciliation report"""
    run_id: int
    run_time: datetime
    status: str
    summary: dict
    discrepancies: List[DiscrepancyResponse]
    snapshots: List[PositionSnapshotResponse]
