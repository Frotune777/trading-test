# /home/fortune/Desktop/Python_Projects/fortune_trading/tests/test_database_mtf.py
import unittest
import pandas as pd
from database import db_manager 
from core.mtf_manager import MTFDataManager, TimeFrame
from tests.conftest import MOCK_HISTORICAL_DF

class TestDatabaseAndMTF(unittest.TestCase):
    def setUp(self):
        # Initialize an in-memory database for testing
        self.db_manager = db_manager.DBManager(db_path=':memory:') 
        self.symbol = 'TESTSTOCK'

    def test_db_manager_add_and_get_company(self):
        """Integration test for basic DB CRUD operations."""
        initial_count = len(self.db_manager.get_all_companies())
        self.db_manager.add_company(self.symbol, 'Test Corp')
        updated_count = len(self.db_manager.get_all_companies())
        self.assertEqual(updated_count, initial_count + 1)
        self.assertIsNotNone(self.db_manager.get_company_info(self.symbol))
        
    def test_db_manager_save_and_load_price_data(self):
        """Integration test for saving and loading historical data."""
        self.db_manager.save_historical_data(self.symbol, MOCK_HISTORICAL_DF)
        loaded_df = self.db_manager.get_historical_data(self.symbol)
        self.assertFalse(loaded_df.empty)
        self.assertTrue(loaded_df['Close'].equals(MOCK_HISTORICAL_DF['Close']))

    def test_timeframe_resample_ohlcv(self):
        """Unit test for MTFDataManager._resample_ohlcv (aggregation logic)."""
        mtf_manager = MTFDataManager(self.db_manager, nse_source=None)
        # Mock high-frequency data for resampling
        # FIX: Indentation corrected here
        df_1m = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [100.5, 101.5, 102.5, 103.5, 104.5],
            'Low': [99.5, 100.5, 101.5, 102.5, 103.5],
            'Close': [101, 102, 103, 104, 105]
        }, index=pd.to_datetime(['2025-01-01 09:15', '2025-01-01 09:16', '2025-01-01 09:17', '2025-01-01 09:18', '2025-01-01 09:19']))
        
        df_5m = mtf_manager._resample_ohlcv(df_1m, '5T')
        
        self.assertEqual(len(df_5m), 1)
        self.assertEqual(df_5m['Open'].iloc[0], 100) 
        self.assertEqual(df_5m['Close'].iloc[0], 105) 
        
    def test_mtf_manager_timeframe_conversions(self):
        """Unit test for TimeFrame helper functions."""
        self.assertEqual(TimeFrame.get_minutes('1h'), 60)
        self.assertEqual(TimeFrame.get_higher_timeframe('1d'), '1w')
        self.assertEqual(TimeFrame.get_lower_timeframe('1h'), '30m')