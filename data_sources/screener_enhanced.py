"""
data_sources/screener_enhanced.py
Enhanced Screener.in scraper - Gets ALL available data
Production version - Optimized, robust, and clean
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, Any, Optional
import re
from io import StringIO
from .base_source import DataSource
import logging

logger = logging.getLogger(__name__)

class ScreenerEnhanced(DataSource):
    """Enhanced Screener.in scraper with complete data extraction."""
    
    def __init__(self):
        super().__init__("Screener_Enhanced")
        self.base_url = "https://www.screener.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Safely parse a string into a float, handling commas and symbols."""
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols, commas, spaces, and percentage signs
        cleaned = re.sub(r'[₹,%\s]', '', str(value))
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _get_company_page(self, symbol: str) -> Optional[BeautifulSoup]:
        """Fetch and parse company page using requests."""
        try:
            url = f"{self.base_url}/company/{symbol}/"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.handle_error(e, f"_get_company_page({symbol})")
            return None

    def get_complete_data(self, symbol: str) -> Dict[str, Any]:
        """Get ALL available data from Screener."""
        soup = self._get_company_page(symbol)
        if not soup:
            return {}
        
        return {
            'company_info': self._extract_company_info(soup, symbol),
            'key_metrics': self._extract_key_metrics(soup),
            'quarterly_results': self._extract_table(soup, 'quarters'),
            'profit_loss': self._extract_table(soup, 'profit-loss'),
            'balance_sheet': self._extract_table(soup, 'balance-sheet'),
            'cash_flow': self._extract_table(soup, 'cash-flow'),
            'ratios': self._extract_table(soup, 'ratios'),
            'shareholding': self._extract_table(soup, 'shareholding'),
            'peer_comparison': self._extract_table(soup, 'peers', is_peers=True)
        }

    def _extract_company_info(self, soup: BeautifulSoup, symbol: str) -> Dict:
        info = {'symbol': symbol}
        try:
            h1 = soup.find('h1', class_='margin-0')
            info['company_name'] = h1.text.strip() if h1 else symbol
            sector_link = soup.find('a', href=re.compile(r'/sector/'))
            if sector_link: info['sector'] = sector_link.text.strip()
        except Exception: pass
        return info

    def _extract_key_metrics(self, soup: BeautifulSoup) -> Dict:
        metrics = {}
        try:
            for li in soup.select('#top-ratios li'):
                name = li.find('span', class_='name').text.strip()
                value = li.find('span', class_='number').text.strip()
                # Parse numbers right at the source
                parsed_value = self._parse_number(value)
                metrics[name] = parsed_value if parsed_value is not None else value
        except Exception: pass
        return metrics

    def _extract_table(self, soup: BeautifulSoup, table_id: str, is_peers: bool = False) -> Optional[pd.DataFrame]:
        try:
            section = soup.find('section', id=table_id)
            if not section: return None
            table = section.find('table')
            if not table: return None
            
            df = pd.read_html(StringIO(str(table)))[0]
            df.columns = [re.sub(r'[\s\.]+', ' ', str(col)).strip() for col in df.columns]

            if not is_peers:
                df = df.rename(columns={df.columns[0]: 'Metric'})
                df = df.set_index('Metric')
            
            df = df.applymap(lambda x: str(x).replace('+', '').strip() if isinstance(x, str) else x)
            return df
        except Exception as e:
            logger.error(f"Error extracting table '{table_id}': {e}")
            return None

    # Base class methods
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        soup = self._get_company_page(symbol)
        if not soup: return None
        return self._extract_company_info(soup, symbol)

    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        soup = self._get_company_page(symbol)
        if not soup: return None
        metrics = self._extract_key_metrics(soup)
        return {'last_price': metrics.get('Current Price')}

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d') -> None:
        return None