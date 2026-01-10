from .unified_data_service import UnifiedDataService
from ..core.cache import CacheManager
from ..core.rate_limiter import RateLimiter

from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HybridAggregator:
    """
    Intelligent data aggregator refactored to use UnifiedDataService.
    Provides backward compatibility for existing code.
    """
    
    def __init__(self, use_cache: bool = True):
        self.name = "HybridAggregator"
        self.use_cache = use_cache
        self.unified = UnifiedDataService()
        self.cache = CacheManager() if use_cache else None
        self.rate_limiter = RateLimiter(calls_per_minute=30)
        
        logger.info("HybridAggregator initialized with UnifiedDataService")

    async def get_stock_data(self, symbol: str, include_historical: bool = True) -> Dict[str, Any]:
        """Get stock data using UnifiedDataService."""
        data = await self.unified.get_comprehensive_data(symbol)
        
        results = {
            'symbol': symbol,
            'company_info': data.get('company_info'),
            'price': data.get('price_data'),
            'historical_daily': await self.unified.get_historical_data(symbol) if include_historical else None,
            'source': 'unified'
        }
        return results

    async def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data."""
        data = await self.unified.get_comprehensive_data(symbol)
        return {
            'key_metrics': data.get('key_metrics'),
            **data.get('financials', {})
        }

    async def get_complete_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get EVERYTHING using UnifiedDataService.
        """
        logger.info(f"Fetching complete analysis for {symbol}")
        
        data = await self.unified.get_comprehensive_data(symbol)
        hist_data = await self.unified.get_historical_data(symbol)
        
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'company_info': data.get('company_info'),
            'price': data.get('price_data'),
            'historical_daily': hist_data,
            'key_metrics': data.get('key_metrics'),
            'quarterly_results': data.get('financials', {}).get('quarterly'),
            'profit_loss': data.get('financials', {}).get('annual'),
            'balance_sheet': data.get('financials', {}).get('balance_sheet'),
            'cash_flow': data.get('financials', {}).get('cash_flow'),
            'ratios': data.get('financials', {}).get('ratios'),
            'shareholding': data.get('financials', {}).get('shareholding'),
            'peer_comparison': data.get('financials', {}).get('peers'),
            '52week_high_low': {
                'high_52w': data.get('price_data', {}).get('high_52w'),
                'low_52w': data.get('price_data', {}).get('low_52w')
            },
            'data_sources': {
                'unified': True
            }
        }
        
        return results

    def get_quick_quote(self, symbol: str) -> Optional[Dict]:
        """Fast price quote."""
        data = self.unified.nse_utils.get_price_data(symbol)
        if not data:
            # Fallback to yahoo via nse_complete
            data = self.unified.nse_complete.get_price_data(symbol)
        return data

    def batch_fetch(self, symbols: List[str], max_workers: int = 5) -> Dict[str, Dict]:
        """Batch fetch symbols."""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(symbol)
        return results


class DataAggregator(HybridAggregator):
    """
    Legacy DataAggregator wrapper.
    Inherits from HybridAggregator to provide all features + legacy compatibility.
    """
    
    def __init__(self, db: Optional[Any] = None, use_cache: bool = True):
        super().__init__(use_cache=use_cache)
        self.db = db
        
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Get historical data with date filtering.
        Compatibility method for strategy endpoints.
        """
        try:
            # Default to 1 year if not specified
            period = '1y'
            
            # If dates provided, fetch enough data
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    now = datetime.now()
                    days = (now - start_dt).days
                    
                    if days <= 1: period = '1d'
                    elif days <= 5: period = '5d'
                    elif days <= 30: period = '1m'
                    elif days <= 90: period = '3m'
                    elif days <= 180: period = '6m'
                    elif days <= 365: period = '1y'
                    elif days <= 730: period = '2y'
                    else: period = '5y'
                except Exception as e:
                    logger.warning(f"Error parsing start_date: {e}, using default period")
            
            # Fetch using UnifiedDataService (via parent)
            df = await self.unified.get_historical_data(
                symbol=symbol,
                interval=interval,
                period=period
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
                
            # Filter by date range
            if start_date or end_date:
                if 'date' in df.columns:
                    # Ensure date is datetime
                    if not pd.api.types.is_datetime64_any_dtype(df['date']):
                        df['date'] = pd.to_datetime(df['date'])
                    
                    # Remove timezone if present
                    if df['date'].dt.tz is not None:
                        df['date'] = df['date'].dt.tz_localize(None)
                    
                    mask = pd.Series([True] * len(df), index=df.index)
                    
                    if start_date:
                        start_dt = pd.to_datetime(start_date)
                        mask &= (df['date'] >= start_dt)
                        
                    if end_date:
                        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        mask &= (df['date'] <= end_dt)
                        
                    df = df[mask]
            
            return df
            
        except Exception as e:
            logger.error(f"Error in DataAggregator.get_historical_data: {e}")
            return pd.DataFrame()