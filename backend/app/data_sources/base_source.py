"""
Abstract base class for all data sources
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Base class for all data sources."""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = True
        self.last_error = None
        
    @abstractmethod
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic company information."""
        pass
    
    @abstractmethod
    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price and market data."""
        pass
    
    @abstractmethod
    def get_historical_prices(self, symbol: str, period: str = '1y',
                            interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get historical price data."""
        pass
    
    def test_connection(self) -> bool:
        """Test if the data source is accessible."""
        try:
            result = self.get_price_data('TCS')
            self.is_available = result is not None
            return self.is_available
        except Exception as e:
            self.is_available = False
            self.last_error = str(e)
            logger.warning(f"{self.name} unavailable: {e}")
            return False
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """Standardized error handling."""
        self.last_error = f"{context}: {str(error)}"
        logger.error(f"{self.name} - {self.last_error}")
        return None