from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor

from ..data_sources.nse_complete import NSEComplete
from ..data_sources.screener_enhanced import ScreenerEnhanced
from .nse_utils_wrapper import NseUtilsWrapper
from ..core.data_normalizer import DataNormalizer

logger = logging.getLogger(__name__)

class UnifiedDataService:
    """
    Central service to aggregate data from multiple sources with fallback logic.
    """
    
    def __init__(self):
        self.nse_complete = NSEComplete()
        self.nse_utils = NseUtilsWrapper()
        self.screener = ScreenerEnhanced()
        self.normalizer = DataNormalizer()
        
    def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch data from all sources and merge into a single standardized dictionary.
        Uses threading for faster parallel fetching.
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Plan fetching tasks
            future_nse_utils_price = executor.submit(self.nse_utils.get_price_data, symbol)
            future_nse_utils_info = executor.submit(self.nse_utils.get_company_info, symbol)
            future_nse_complete = executor.submit(self.nse_complete.get_price_data, symbol) # This uses Yahoo/NSE
            future_screener = executor.submit(self.screener.get_complete_data, symbol)
            
            # Collect results
            nse_utils_price = future_nse_utils_price.result()
            nse_utils_info = future_nse_utils_info.result()
            nse_complete_data = future_nse_complete.result()
            screener_data = future_screener.result()
            
        # 1. Price Data (Priority: NseUtils > NseComplete)
        price_data = nse_complete_data.get('price_data', {})
        if nse_utils_price:
            for k, v in nse_utils_price.items():
                if v is not None:
                    price_data[k] = v
        
        # 2. Company Info (Priority: NseUtils > NseComplete > Screener)
        company_info = screener_data.get('company_info', {})
        
        if nse_complete_data.get('company_info'):
            company_info.update(nse_complete_data['company_info'])
            
        if nse_utils_info:
            for k, v in nse_utils_info.items():
                if v is not None:
                    company_info[k] = v
            
        # 3. Fundamentals (Base: Screener, Update metrics with NSE data)
        key_metrics = screener_data.get('key_metrics', {})
        
        # Update metrics from NSEComplete (e.g. fresh PE/MarketCap)
        if nse_complete_data.get('key_metrics'):
             key_metrics.update(nse_complete_data['key_metrics'])
             
        # Add real-time metrics from NseUtils price data if mapped
        if nse_utils_price:
             # Map real-time price fields to key metrics if relevant (e.g. market_cap if available in price?)
             # Usually NseUtils price info has Upper/Lower circuit etc.
             # We rely on NSEComplete for standard metrics like PE/MarketCap as YF provides them well.
             pass
        
        # 4. Financial Tables (From Screener)
        results = {
            'symbol': symbol,
            'price_data': price_data,
            'company_info': company_info,
            'key_metrics': key_metrics,
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
        
        return results

    def get_historical_data(self, symbol: str, interval: str = '1d', period: str = '1y', source: str = 'auto'):
        """Fetch historical data from NSE or Yahoo."""
        return self.nse_complete.get_historical_prices(symbol, interval=interval, period=period, source=source)

    def get_options_data(self, symbol: str, indices: bool = False):
        """Fetch live option chain."""
        return self.nse_utils.get_option_chain(symbol, indices=indices)
