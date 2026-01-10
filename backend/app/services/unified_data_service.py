from typing import Dict, Any, List, Optional
import pandas as pd
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..data_sources.nse_complete import NSEComplete
from ..data_sources.screener_enhanced import ScreenerEnhanced
from .nse_utils_wrapper import NseUtilsWrapper
from ..core.data_normalizer import DataNormalizer

logger = logging.getLogger(__name__)

class UnifiedDataService:
    """
    Central service to aggregate data from multiple sources with fallback logic.
    Refactored for Phase 3: Prioritizes PostgreSQL Consolidated Data Lake.
    """
    
    def __init__(self):
        self.nse_complete = NSEComplete()
        self.nse_utils = NseUtilsWrapper()
        self.screener = ScreenerEnhanced()
        self.normalizer = DataNormalizer()
        from .historical_data_service import historical_data_service
        self.historical_service = historical_data_service
        
    async def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch data from all sources and merge into a single standardized dictionary.
        """
        # 1. Fetch live/fundamental data (Sync sources)
        # We still use ThreadPoolExecutor for these to avoid blocking
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_nse_utils_price = executor.submit(self.nse_utils.get_price_data, symbol)
            future_nse_utils_info = executor.submit(self.nse_utils.get_company_info, symbol)
            future_nse_complete = executor.submit(self.nse_complete.get_price_data, symbol)
            future_screener = executor.submit(self.screener.get_complete_data, symbol)
            
            nse_utils_price = future_nse_utils_price.result()
            nse_utils_info = future_nse_utils_info.result()
            nse_complete_data = future_nse_complete.result()
            screener_data = future_screener.result()
            
        # 2. Extract price data
        price_data = nse_complete_data.get('price_data', {}) or {}
        
        screener_price = screener_data.get('price_data', {})
        if screener_price:
            for k, v in screener_price.items():
                if k not in price_data or price_data[k] is None:
                    price_data[k] = v
        
        if nse_utils_price:
            for k, v in nse_utils_price.items():
                if v is not None:
                    price_data[k] = v
        
        # 3. Company Info
        company_info = screener_data.get('company_info', {})
        if nse_complete_data.get('company_info'):
            company_info.update(nse_complete_data['company_info'])
        if nse_utils_info:
            for k, v in nse_utils_info.items():
                if v is not None:
                    company_info[k] = v
            
        # 4. Results
        return {
            'symbol': symbol,
            'price_data': price_data,
            'company_info': company_info,
            'key_metrics': screener_data.get('key_metrics', {}),
            'financials': {
                'quarterly': screener_data.get('quarterly_results'),
                'annual': screener_data.get('profit_loss'),
                'balance_sheet': screener_data.get('balance_sheet'),
                'cash_flow': screener_data.get('cash_flow'),
                'ratios': screener_data.get('ratios'),
                'shareholding': screener_data.get('shareholding'),
                'peers': screener_data.get('peer_comparison')
            }
        }

    async def get_historical_data(self, 
                                  symbol: str, 
                                  interval: str = '1d', 
                                  period: str = '1y', 
                                  limit: int = 1000,
                                  include_indicators: bool = True):
        """
        Fetch historical data.
        PRIORITY 1: PostgreSQL Data Lake
        PRIORITY 2: NSE Master Data (NSE Charting API)
        PRIORITY 3: Yahoo Finance (Fallback)
        """
        # 1. Try PostgreSQL
        logger.info(f"Fetching {symbol} ({interval}) from PostgreSQL...")
        df = await self.historical_service.get_historical_ohlcv(
            symbol=symbol, 
            interval=interval, 
            limit=limit,
            include_indicators=include_indicators
        )
        
        if not df.empty:
            logger.info(f"✅ Found {len(df)} records for {symbol} in PostgreSQL")
            return df
            
        # 2. Fallback to External APIs
        logger.info(f"⚠️ {symbol} not found in PostgreSQL. Falling back to NSE APIs...")
        
        # We use a thread for the sync call
        loop = asyncio.get_event_loop()
        df_ext = await loop.run_in_executor(
            None, 
            self.nse_complete.get_historical_prices, 
            symbol, period, interval
        )
        
        return df_ext

    async def get_market_activity(self, limit: int = 30) -> Dict[str, Any]:
        """Fetch consolidated institutional market activity."""
        fii_dii = await self.historical_service.get_market_fii_dii(limit=limit)
        bulk_deals = await self.historical_service.get_market_bulk_deals(limit=limit)
        return {
            "fii_dii": fii_dii.to_dict(orient="records"),
            "bulk_deals": bulk_deals.to_dict(orient="records")
        }

    async def get_insider_trading(self, symbol: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch insider trading data."""
        df = await self.historical_service.get_market_insider_trading(symbol=symbol, limit=limit)
        return df.to_dict(orient="records")

    def get_options_data(self, symbol: str, indices: bool = False):
        """Fetch live option chain. (Sync wrapper)"""
        return self.nse_utils.get_option_chain(symbol, indices=indices)
