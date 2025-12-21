"""
Hybrid data aggregator combining all sources
UPDATED VERSION - Now includes Screener.in integration + Error handling fixes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.nse_complete import NSEComplete
from data_sources.screener_enhanced import ScreenerEnhanced
from data_sources.yahoo_finance import YahooFinance
from core.cache_manager import CacheManager
from core.rate_limiter import RateLimiter
from core.data_merger import DataMerger, DataQualityChecker
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

logger = logging.getLogger(__name__)


class HybridAggregator:
    """
    Intelligent data aggregator combining multiple sources.
    
    Priority Strategy:
    - Price: NSE (real-time) → Yahoo (fallback)
    - Fundamentals: Screener (detailed) → Yahoo (fallback)
    - Historical: NSE (best for Indian stocks) → Yahoo (backup)
    """
    
    def __init__(self, use_cache: bool = True):
        self.name = "HybridAggregator"
        self.use_cache = use_cache
        
        # Initialize all sources
        self.nse = NSEComplete()
        self.screener = ScreenerEnhanced()
        self.yahoo = YahooFinance()
        
        self.sources = {
            'nse': self.nse,
            'screener': self.screener,
            'yahoo': self.yahoo
        }
        
        # Initialize utilities
        self.cache = CacheManager() if use_cache else None
        self.rate_limiter = RateLimiter(calls_per_minute=30)
        
        logger.info("HybridAggregator initialized with all sources")
        self._test_sources()
    
    def _test_sources(self):
        """Test all data sources."""
        for name, source in self.sources.items():
            try:
                source.test_connection()
                logger.info(f"✅ {name} connected")
            except Exception as e:
                logger.warning(f"⚠️  {name} connection issue: {e}")
    
    def get_stock_data(self, symbol: str, include_historical: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive stock data from NSE and Yahoo.
        
        Args:
            symbol: NSE symbol (e.g., 'TCS', 'INFY')
            include_historical: Include historical data
        
        Returns:
            Unified dictionary with all available data
        """
        cache_key = f"stock_data_{symbol}_{include_historical}"
        
        if self.use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {symbol}")
                return cached
        
        self.rate_limiter.wait_if_needed()
        
        # Fetch from all sources in parallel
        raw_data = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._fetch_from_source, symbol, name): name
                for name in ['nse', 'yahoo']
            }
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    raw_data[source_name] = future.result()
                except Exception as e:
                    logger.error(f"Error fetching from {source_name}: {e}")
                    raw_data[source_name] = {}
        
        # Merge data intelligently
        merged = self._merge_data(symbol, raw_data)
        
        if self.use_cache:
            self.cache.set(cache_key, merged, ttl=config.CACHE_TTL_REALTIME)
        
        return merged
    
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive fundamental data from Screener.
        
        Args:
            symbol: NSE symbol
        
        Returns:
            Complete Screener data with all 9 sections
        """
        cache_key = f"fundamentals_{symbol}"
        
        if self.use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for fundamentals: {symbol}")
                return cached
        
        self.rate_limiter.wait_if_needed()
        
        try:
            logger.info(f"Fetching fundamentals for {symbol} from Screener")
            data = self.screener.get_complete_data(symbol)
            
            if self.use_cache:
                self.cache.set(cache_key, data, ttl=config.CACHE_TTL_FUNDAMENTAL)
            
            return data
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {}
    
    def get_complete_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get EVERYTHING: NSE price data + Screener fundamentals + Yahoo backup.
        
        This is the MASTER method that gets all available data.
        
        Args:
            symbol: NSE symbol
        
        Returns:
            Complete dataset combining all sources
        """
        logger.info(f"Fetching complete analysis for {symbol}")
        
        # Get market data from NSE/Yahoo
        market_data = self.get_stock_data(symbol, include_historical=True)
        
        # Get fundamentals from Screener
        fundamental_data = self.get_fundamental_data(symbol)
        
        # Combine everything
        complete_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            
            # Market Data (NSE primary, Yahoo fallback)
            'company_info': market_data.get('company_info'),
            'price': market_data.get('price'),
            'historical_daily': market_data.get('historical_daily'),
            'historical_weekly': market_data.get('historical_weekly'),
            'intraday': market_data.get('intraday_5m'),
            'corporate_actions': market_data.get('corporate_actions'),
            'bulk_deals': market_data.get('bulk_deals'),
            'insider_trading': market_data.get('insider_trading'),
            'option_chain': market_data.get('option_chain'),
            'futures_data': market_data.get('futures_data'),
            'market_depth': market_data.get('market_depth'),
            '52week_high_low': market_data.get('52week_high_low'),
            
            # Fundamental Data (Screener)
            'key_metrics': fundamental_data.get('key_metrics'),
            'quarterly_results': fundamental_data.get('quarterly_results'),
            'profit_loss': fundamental_data.get('profit_loss'),
            'balance_sheet': fundamental_data.get('balance_sheet'),
            'cash_flow': fundamental_data.get('cash_flow'),
            'ratios': fundamental_data.get('ratios'),
            'shareholding': fundamental_data.get('shareholding'),
            'peer_comparison': fundamental_data.get('peer_comparison'),
            
            # Metadata
            'data_sources': {
                'nse_available': bool(market_data),
                'screener_available': bool(fundamental_data),
                'yahoo_fallback_used': market_data.get('source') == 'yahoo' if market_data else False
            }
        }
        
        return complete_data
    
    def _fetch_from_source(self, symbol: str, source_name: str) -> Dict:
        """Fetch all available data from a single source."""
        source = self.sources.get(source_name)
        if not source:
            return {}
        
        data = {}
        
        try:
            # Basic info
            try:
                data['company_info'] = source.get_company_info(symbol)
            except Exception as e:
                logger.warning(f"Could not get company info from {source_name}: {e}")
            
            try:
                data['price'] = source.get_price_data(symbol)
            except Exception as e:
                logger.warning(f"Could not get price data from {source_name}: {e}")
            
            # Historical data (if supported)
            try:
                data['historical_daily'] = source.get_historical_prices(symbol, period='1y', interval='1d')
            except Exception as e:
                logger.debug(f"Historical data not available from {source_name}: {e}")
            
            # NSE-specific data
            if source_name == 'nse':
                # Intraday data
                try:
                    data['intraday_5m'] = self.nse.get_intraday_data(symbol, interval='5m')
                except Exception as e:
                    logger.debug(f"Intraday data not available: {e}")
                
                # Corporate actions
                try:
                    data['corporate_actions'] = self.nse.get_corporate_actions()
                except Exception as e:
                    logger.debug(f"Corporate actions not available: {e}")
                
                # Option chain (may not be available for all stocks)
                try:
                    option_chain = self.nse.get_option_chain(symbol, indices=False)
                    if option_chain is not None:
                        data['option_chain'] = option_chain
                except KeyError as e:
                    logger.debug(f"Option chain not available for {symbol}: {e}")
                except Exception as e:
                    logger.debug(f"Could not fetch option chain: {e}")
                
                # 52 week high/low
                try:
                    week_52_data = self.nse.get_52week_high_low(symbol)
                    if week_52_data is not None:
                        data['52week_high_low'] = week_52_data
                except Exception as e:
                    logger.debug(f"52 week data not available: {e}")
            
            data['source'] = source_name
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name} for {symbol}: {e}")
        
        return data
    
    def _merge_data(self, symbol: str, raw_data: Dict) -> Dict:
        """Intelligently merge data from multiple sources."""
        merged = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        
        # Merge company info
        merged['company_info'] = self._merge_company_info(raw_data)
        
        # Merge price data (NSE preferred)
        merged['price'] = self._merge_price_data(raw_data)
        
        # Select best historical data
        merged.update(self._select_best_historical(raw_data))
        
        # Add NSE-specific data
        if 'nse' in raw_data:
            nse_data = raw_data['nse']
            merged['intraday_5m'] = nse_data.get('intraday_5m')
            merged['corporate_actions'] = nse_data.get('corporate_actions')
            merged['option_chain'] = nse_data.get('option_chain')
            merged['52week_high_low'] = nse_data.get('52week_high_low')
        
        return merged
    
    def _merge_company_info(self, raw_data: Dict) -> Dict:
        """Merge company information from all sources."""
        info = {}
        
        # Priority: NSE → Yahoo
        for source in ['nse', 'yahoo']:
            if source in raw_data and raw_data[source].get('company_info'):
                source_info = raw_data[source]['company_info']
                info.update(source_info)
        
        return info
    
    def _merge_price_data(self, raw_data: Dict) -> Optional[Dict]:
        """Merge price data with priority."""
        # Priority list
        priority = ['nse', 'yahoo']
        
        sources = []
        for source_name in priority:
            if source_name in raw_data and raw_data[source_name].get('price'):
                sources.append(raw_data[source_name]['price'])
        
        if not sources:
            return None
        
        return DataMerger.merge_price_data(sources, priority)
    
    def _select_best_historical(self, raw_data: Dict) -> Dict:
        """Select best historical data."""
        result = {}
        
        # Prefer NSE for historical data
        for source in ['nse', 'yahoo']:
            if source in raw_data:
                hist = raw_data[source].get('historical_daily')
                if hist is not None and not hist.empty:
                    result['historical_daily'] = hist
                    result['historical_source'] = source
                    break
        
        return result
    
    def get_quick_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get only price data (fast).
        
        Args:
            symbol: NSE symbol
        
        Returns:
            Price data only
        """
        cache_key = f"quick_quote_{symbol}"
        
        if self.use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        self.rate_limiter.wait_if_needed()
        
        # Try NSE first
        try:
            price = self.nse.get_price_data(symbol)
            if price:
                if self.use_cache:
                    self.cache.set(cache_key, price, ttl=60)  # 1 min cache
                return price
        except:
            pass
        
        # Fallback to Yahoo
        try:
            price = self.yahoo.get_price_data(symbol + ".NS")
            if price and self.use_cache:
                self.cache.set(cache_key, price, ttl=60)
            return price
        except Exception as e:
            logger.error(f"Error getting quick quote for {symbol}: {e}")
            return None
    
    def batch_fetch(self, symbols: List[str], max_workers: int = 5) -> Dict[str, Dict]:
        """
        Fetch data for multiple symbols in parallel.
        
        Args:
            symbols: List of symbols
            max_workers: Number of parallel workers
        
        Returns:
            Dictionary mapping symbol to data
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.get_stock_data, symbol): symbol
                for symbol in symbols
            }
            
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
                    results[symbol] = None
        
        return results