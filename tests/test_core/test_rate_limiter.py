import unittest
import time
from core.rate_limiter import RateLimiter

class TestRateLimiter(unittest.TestCase):
    def test_wait_if_needed(self):
        rl = RateLimiter(calls_per_minute=2)
        start = time.time()
        rl.wait_if_needed(); rl.wait_if_needed(); rl.wait_if_needed()
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 20)  # at least 3 calls with 2/min -> wait
