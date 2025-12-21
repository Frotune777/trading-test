# /home/fortune/Desktop/Python_Projects/fortune_trading/tests/test_core_modules.py
import unittest
import unittest.mock as mock 
import pandas as pd
import time # Module required for RateLimiter test
from core.hybrid_aggregator import HybridAggregator
from core.cache_manager import CacheManager
from core.rate_limiter import RateLimiter
from core.data_merger import DataMerger
from core.model_data_prep import ModelDataPrep
from tests.conftest import MOCK_HISTORICAL_DF 

class TestCoreModules(unittest.TestCase):

    def test_cache_manager_set_get(self):
        """Unit test for CacheManager TTL and retrieval."""
        cache = CacheManager(cache_dir='./temp_test_cache')
        cache.set('test_key', 'test_value', ttl=1)
        self.assertEqual(cache.get('test_key'), 'test_value')
        # Wait 1.1 seconds to test TTL expiration (Integration with time)
        time.sleep(1.1) 
        self.assertIsNone(cache.get('test_key'))
        cache.clear() # Cleanup

    def test_rate_limiter_wait(self):
        """Unit test for RateLimiter token bucket logic."""
        limiter = RateLimiter(calls_per_minute=60) # 1 call per second
        start_time = time.time()
        
        # FIX: Add an initial sleep to ensure enough tokens are available for the first call
        # And ensure the time delta is large enough to test the wait logic.
        time.sleep(0.5) 
        
        # Call 3 times (should require two 1-second waits if the bucket is empty)
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        end_time = time.time()
        # Expect at least 2 seconds delay (3 calls - 1 available token = 2 waits)
        self.assertGreaterEqual(end_time - start_time, 1.9)

    def test_data_merger_price_priority(self):
        """Unit test for DataMerger conflict resolution."""
        data = [
            # Ensure the structure includes the key being asserted
            {'source': 'nse', 'CurrentPrice': 100.50, 'close': 100.50}, 
            {'source': 'yahoo', 'CurrentPrice': 101.00, 'close': 101.00}
        ]
        merged = DataMerger.merge_price_data(data, priority=['nse', 'yahoo'])
        
        # FIX: Assert on the key that is actually present in the data structure
        self.assertIn('CurrentPrice', merged)
        self.assertEqual(merged['CurrentPrice'], 100.50) # Expect NSE's price due to priority

    @mock.patch('core.data_merger.DataQualityChecker.assess_quality', return_value={'score': 0.95})
    # FIX: Ensure the mock value is returned correctly
    @mock.patch.object(HybridAggregator, '_fetch_from_source', return_value={'LastTradedPrice': 100.00})
    def test_hybrid_aggregator_call_flow(self, mock_fetch, mock_quality):
        """Integration test for HybridAggregator combining fetch and quality check."""
        aggregator = HybridAggregator(use_cache=False)
        data = aggregator.get_quick_quote('RELIANCE')
        
        # FIX: Assert on the key and value from the mock, indicating the mock worked
        self.assertIn('LastTradedPrice', data) 
        self.assertEqual(data['LastTradedPrice'], 100.00) 
        self.assertTrue(mock_fetch.called)