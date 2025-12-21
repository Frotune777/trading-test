from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd

class DataSource(ABC):
    """
    Abstract base class for all data sources (NSE, Yahoo, Screener, etc.)
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = "1d", 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch historical price data"""
        pass

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> dict:
        """Fetch company fundamental data"""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> dict:
        """Fetch real-time price quote"""
        pass
