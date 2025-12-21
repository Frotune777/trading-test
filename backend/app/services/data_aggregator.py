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

    def get_stock_data(self, symbol: str, include_historical: bool = True) -> Dict[str, Any]:
        """Get stock data using UnifiedDataService."""
        data = self.unified.get_comprehensive_data(symbol)
        
        results = {
            'symbol': symbol,
            'company_info': data.get('company_info'),
            'price': data.get('price_data'),
            'historical_daily': self.unified.get_historical_data(symbol) if include_historical else None,
            'source': 'unified'
        }
        return results

    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data."""
        data = self.unified.get_comprehensive_data(symbol)
        return {
            'key_metrics': data.get('key_metrics'),
            **data.get('financials', {})
        }

    def get_complete_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get EVERYTHING using UnifiedDataService.
        """
        logger.info(f"Fetching complete analysis for {symbol}")
        
        data = self.unified.get_comprehensive_data(symbol)
        hist_data = self.unified.get_historical_data(symbol)
        
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