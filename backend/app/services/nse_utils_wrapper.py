from typing import Dict, Any, Optional
import pandas as pd
from ..data_sources.base_source import DataSource
from ..data_sources.nse_utils import NseUtils
from ..core.data_normalizer import DataNormalizer
import logging

logger = logging.getLogger(__name__)

class NseUtilsWrapper(DataSource):
    """
    Wrapper for NseUtils to align with DataSource interface and provide normalized data.
    """
    
    def __init__(self):
        super().__init__("NseUtils")
        self.nse = NseUtils()
        self.normalizer = DataNormalizer()
        
    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Get normalized real-time price data from NSE."""
        try:
            raw_data = self.nse.price_info(symbol)
            if not raw_data:
                return {}
                
            # Normalize using NSEMapper (which price_info already uses similar keys)
            normalized = self.normalizer.normalize_price_data(raw_data, 'nse')
            
            # Add NseUtils specific fields
            normalized['upper_circuit'] = raw_data.get('UpperCircuit')
            normalized['lower_circuit'] = raw_data.get('LowerCircuit')
            normalized['vwap'] = raw_data.get('VWAP')
            
            return normalized
        except Exception as e:
            logger.error(f"Error in NseUtilsWrapper.get_price_data for {symbol}: {e}")
            return {}
            
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get normalized company info from NSE."""
        try:
            raw_data = self.nse.equity_info(symbol)
            if not raw_data or 'info' not in raw_data:
                return {}
                
            info = raw_data['info']
            # Normalize using NSEMapper
            normalized = self.normalizer.normalize_company_data(info, 'nse')
            
            return normalized
        except Exception as e:
            logger.error(f"Error in NseUtilsWrapper.get_company_info for {symbol}: {e}")
            return {}
            
    def get_option_chain(self, symbol: str, indices: bool = False) -> Optional[Any]:
        """Get live option chain."""
        try:
            return self.nse.get_option_chain(symbol, indices=indices)
        except Exception as e:
            logger.error(f"Error in NseUtilsWrapper.get_option_chain for {symbol}: {e}")
            return None

    def get_corporate_actions(self, symbol: Optional[str] = None):
        """Get corporate actions."""
        try:
            df = self.nse.get_corporate_action()
            if symbol and not df.empty:
                return df[df['symbol'] == symbol]
            return df
        except Exception as e:
            logger.error(f"Error in NseUtilsWrapper.get_corporate_actions: {e}")
            return None

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get historical prices. (Note: NseUtils primarily focuses on real-time data)"""
        return None

if __name__ == "__main__":
    import pandas as pd
    wrapper = NseUtilsWrapper()
    print(wrapper.get_price_data('INFY'))

