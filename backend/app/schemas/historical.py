from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class HistoricalOHLCBase(BaseModel):
    symbol: str
    exchange: str = "NSE"
    interval: str
    timestamp: datetime
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: Optional[int] = None
    source: str

class HistoricalOHLCSchema(HistoricalOHLCBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IndicatorHistorySchema(BaseModel):
    symbol: str
    interval: str
    timestamp: datetime
    indicators: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class MarketBulkDealSchema(BaseModel):
    id: int
    date: date
    order_type: Optional[str] = None
    symbol: str
    scrip_name: Optional[str] = None
    client_name: Optional[str] = None
    buy_sell: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    remarks: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class MarketInsiderTradingSchema(BaseModel):
    id: int
    symbol: str
    company: Optional[str] = None
    person_name: Optional[str] = None
    person_category: Optional[str] = None
    transaction_type: Optional[str] = None
    securities_type: Optional[str] = None
    number_of_securities: Optional[int] = None
    value: Optional[Decimal] = None
    acquisition_date: Optional[date] = None
    
    model_config = ConfigDict(from_attributes=True)

class MarketFIIDIISchema(BaseModel):
    id: int
    date: date
    category: str # FII, DII
    buy_value: Decimal
    sell_value: Decimal
    net_value: Decimal
    
    model_config = ConfigDict(from_attributes=True)

class OHLCVMetadataSchema(BaseModel):
    symbol: str
    exchange: str
    interval: str
    last_sync: Optional[datetime] = None
    earliest_available: Optional[datetime] = None
    latest_available: Optional[datetime] = None
    total_records: int
    is_actively_trading: int
    last_source: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
