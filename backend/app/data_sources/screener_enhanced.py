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
from ..core.data_normalizer import DataNormalizer
import logging

logger = logging.getLogger(__name__)

class ScreenerEnhanced(DataSource):
    """Enhanced Screener.in scraper with complete data extraction."""
    
    def __init__(self):
        super().__init__("Screener_Enhanced")
        self.base_url = "https://www.screener.in"
        self.normalizer = DataNormalizer()
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

    def _get_warehouse_id(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract warehouse_id from company page (required for peers API)."""
        try:
            # Look for data-warehouse-id attribute
            company_info = soup.find('div', id='company-info')
            if company_info and company_info.get('data-warehouse-id'):
                return company_info.get('data-warehouse-id')
            
            # Fallback: search in page HTML for warehouse_id
            page_html = str(soup)
            import re
            match = re.search(r'data-warehouse-id="(\d+)"', page_html)
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting warehouse_id: {e}")
            return None

    def get_complete_data(self, symbol: str) -> Dict[str, Any]:
        """Get ALL available data from Screener with normalized field names."""
        soup = self._get_company_page(symbol)
        if not soup:
            return {}
        
        # Extract warehouse_id for peer API
        warehouse_id = self._get_warehouse_id(soup)
        
        # Extract raw data
        raw_company_info = self._extract_company_info(soup, symbol)
        raw_key_metrics = self._extract_key_metrics(soup)
        
        # Normalize company info and metrics using DataNormalizer
        normalized_company = self.normalizer.normalize_company_data(raw_company_info, 'screener')
        normalized_metrics = self.normalizer.normalize_fundamental_data(raw_key_metrics, 'screener')
        
        # Merge price data from metrics into normalized format
        price_data = {
            'Current Price': raw_key_metrics.get('Current Price'),
            'Market Cap': raw_key_metrics.get('Market Cap'),
            'High': raw_key_metrics.get('High'),
            'Low': raw_key_metrics.get('Low')
        }
        normalized_price = self.normalizer.normalize_price_data(price_data, 'screener')
        
        return {
            'company_info': normalized_company,
            'key_metrics': normalized_metrics,
            'price_data': normalized_price,  # Add normalized price data
            'quarterly_results': self._extract_table(soup, 'quarters'),
            'profit_loss': self._extract_table(soup, 'profit-loss'),
            'balance_sheet': self._extract_table(soup, 'balance-sheet'),
            'cash_flow': self._extract_table(soup, 'cash-flow'),
            'ratios': self._extract_table(soup, 'ratios'),
            'shareholding': self._extract_table(soup, 'shareholding'),
            'peer_comparison': self._extract_peers_via_api(warehouse_id) if warehouse_id else None
        }

    def _extract_company_info(self, soup: BeautifulSoup, symbol: str) -> Dict:
        info = {'symbol': symbol}
        try:
            h1 = soup.find('h1', class_='margin-0')
            info['Name'] = h1.text.strip() if h1 else symbol # Use 'Name' for mapper
            sector_link = soup.find('a', href=re.compile(r'/sector/'))
            if sector_link: info['Sector'] = sector_link.text.strip() # Use 'Sector' for mapper
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
            
            df = df.map(lambda x: str(x).replace('+', '').strip() if isinstance(x, str) else x)
            return df
        except Exception as e:
            logger.error(f"Error extracting table '{table_id}': {e}")
            return None
    
    def _extract_peers_via_api(self, warehouse_id: str) -> Optional[pd.DataFrame]:
        """
        Extract peer comparison data using Screener's AJAX API.
        
        Args:
            warehouse_id: Company's internal warehouse ID from Screener
            
        Returns:
            DataFrame with peer comparison data or None if unavailable
        """
        try:
            # Construct API endpoint
            url = f"{self.base_url}/api/company/{warehouse_id}/peers/"
            
            # Fetch peer data HTML
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')
            
            if not table:
                logger.warning(f"No peer table found in API response for warehouse_id {warehouse_id}")
                return None
            
            # Convert to DataFrame
            df = pd.read_html(StringIO(str(table)))[0]
            
            # Clean column names
            df.columns = [re.sub(r'[\s\.]+', ' ', str(col)).strip() for col in df.columns]
            
            # Clean data
            df = df.map(lambda x: str(x).replace('+', '').strip() if isinstance(x, str) else x)
            
            logger.info(f"Successfully extracted {len(df)} peer companies")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching peer data from API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing peer data: {e}")
            return None

    # Base class methods
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        soup = self._get_company_page(symbol)
        if not soup: return None
        raw_info = self._extract_company_info(soup, symbol)
        # raw_info usually has 'Name', 'Sector' which maps to 'company_name', 'sector'
        return self.normalizer.normalize_company_data(raw_info, 'screener')

    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        soup = self._get_company_page(symbol)
        if not soup: return None
        metrics = self._extract_key_metrics(soup)
        price_data = {
            'Current Price': metrics.get('Current Price'),
            'Market Cap': metrics.get('Market Cap')
        }
        return self.normalizer.normalize_price_data(price_data, 'screener')

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        # Screener doesn't provide historical data in a format we can easily parse
        return pd.DataFrame()