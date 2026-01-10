"""
Historical Data Service
Handles retrieval of consolidated OHLC and indicator data from PostgreSQL.
"""

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models_historical import HistoricalOHLC, IndicatorHistory, MarketBulkDeal, MarketInsiderTrading, MarketFIIDII, OHLCVMetadata
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class HistoricalDataService:
    """
    Service for querying consolidated historical market data.
    Provides methods to fetch price history, associated indicators, and market activity.
    """
    
    async def get_historical_ohlcv(
        self, 
        symbol: str, 
        interval: str = '1d', 
        limit: int = 100,
        include_indicators: bool = True
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from PostgreSQL.
        Optionally joins with indicator_history.
        """
        async with SessionLocal() as session:
            # Query price history
            query = select(HistoricalOHLC).where(
                and_(
                    HistoricalOHLC.symbol == symbol.upper(),
                    HistoricalOHLC.interval == interval
                )
            ).order_by(HistoricalOHLC.timestamp.desc()).limit(limit)
            
            if include_indicators:
                query = query.options(selectinload(HistoricalOHLC.indicators))
                
            result = await session.execute(query)
            records = result.scalars().all()
            
            if not records:
                return pd.DataFrame()
                
            # Convert to list of dicts for DataFrame
            data = []
            for r in reversed(records): # Reverse to get ascending time order
                row = {
                    "datetime": r.timestamp,
                    "open": float(r.open) if r.open else None,
                    "high": float(r.high) if r.high else None,
                    "low": float(r.low) if r.low else None,
                    "close": float(r.close) if r.close else None,
                    "volume": int(r.volume) if r.volume else 0,
                    "source": r.source
                }
                
                # Flatten indicators from JSONB if present
                if include_indicators and r.indicators:
                    for ind_record in r.indicators:
                        if ind_record.indicators:
                            row.update(ind_record.indicators)
                data.append(row)
                
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('datetime', inplace=True)
                
            return df

    async def get_market_bulk_deals(self, symbol: Optional[str] = None, limit: int = 50) -> pd.DataFrame:
        """Fetch bulk/block deals from PostgreSQL."""
        async with SessionLocal() as session:
            query = select(MarketBulkDeal)
            if symbol:
                query = query.where(MarketBulkDeal.symbol == symbol.upper())
            query = query.order_by(MarketBulkDeal.date.desc()).limit(limit)
            
            result = await session.execute(query)
            records = result.scalars().all()
            return pd.DataFrame([r.__dict__ for r in records])

    async def get_market_insider_trading(self, symbol: Optional[str] = None, limit: int = 50) -> pd.DataFrame:
        """Fetch insider trading activity."""
        async with SessionLocal() as session:
            query = select(MarketInsiderTrading)
            if symbol:
                query = query.where(MarketInsiderTrading.symbol == symbol.upper())
            query = query.order_by(MarketInsiderTrading.acquisition_date.desc()).limit(limit)
            
            result = await session.execute(query)
            records = result.scalars().all()
            return pd.DataFrame([r.__dict__ for r in records])

    async def get_market_fii_dii(self, limit: int = 30) -> pd.DataFrame:
        """Fetch daily FII/DII activity."""
        async with SessionLocal() as session:
            query = select(MarketFIIDII).order_by(MarketFIIDII.date.desc()).limit(limit)
            result = await session.execute(query)
            records = result.scalars().all()
            return pd.DataFrame([r.__dict__ for r in records])

    async def get_available_metadata(self) -> pd.DataFrame:
        """Fetch sync status metadata for all symbols using ORM model."""
        async with SessionLocal() as session:
            query = select(OHLCVMetadata).order_by(OHLCVMetadata.symbol.asc())
            result = await session.execute(query)
            records = result.scalars().all()
            return pd.DataFrame([r.__dict__ for r in records])

historical_data_service = HistoricalDataService()
