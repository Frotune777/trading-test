from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class CustomStockList(Base):
    """
    User-defined stock lists for focused screening.
    """
    __tablename__ = "custom_stock_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    stocks = Column(ARRAY(String), nullable=False) # Postgres ARRAY type for efficient symbol storage
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PKScreenerResult(Base):
    """
    Historical log of PKScreener scan results.
    """
    __tablename__ = "pkscreener_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(50), index=True) # Task ID or unique run ID
    index_name = Column(String(50))
    strategy_name = Column(String(100))
    results = Column(JSONB) # Full scan findings as JSON
    scan_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Store path to the actual CSV/XLSX if needed for legacy download
    file_path = Column(Text, nullable=True)
