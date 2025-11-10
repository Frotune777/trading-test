# /home/fortune/Desktop/Python_Projects/fortune_trading/tests/test_data_sources.py
import unittest
import unittest.mock as mock
import pandas as pd
from data_sources.nse_complete import NSEComplete
from data_sources.screener_enhanced import ScreenerEnhanced
from tests.conftest import MOCK_NSE_PRICE_DATA, MOCK_HISTORICAL_DF, mock_requests_get

class TestDataSources(unittest.TestCase):
    def setUp(self):
        self.nse = NSEComplete()
        self.screener = ScreenerEnhanced()
        self.symbol = 'TCS'

    # NOTE: This test will PASS once the logical error in your data_sources/nse_complete.py is fixed.
    @mock.patch('requests.get', side_effect=mock_requests_get)
    def test_nse_complete_price_data(self, mock_get):
        """Unit test for NSEComplete.get_price_data."""
        data = self.nse.get_price_data(self.symbol)
        self.assertIn('current', data)
        self.assertEqual(data['current'], MOCK_NSE_PRICE_DATA['price']['current'])
        mock_get.assert_called()

    @mock.patch('data_sources.nse_complete.NseUtils.get_index_historic_data', return_value=MOCK_HISTORICAL_DF)
    def test_nse_complete_historical_prices(self, mock_historic):
        """Unit test for NSEComplete.get_historical_prices using internal delegation."""
        df = self.nse.get_historical_prices(self.symbol)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    @mock.patch('data_sources.screener_enhanced.requests.get', return_value=mock.Mock(text='<html>... mock screener data ...</html>'))
    def test_screener_enhanced_fundamental(self, mock_get):
        """Unit test for ScreenerEnhanced parsing logic."""
        # FIX: Correct method name
        data = self.screener.get_company_info(self.symbol)
        self.assertIn('company_name', data) 
        # Assertion based on debug output from earlier, checking for both keys
        self.assertTrue('Market Cap' in data and 'Stock P/E' in data)