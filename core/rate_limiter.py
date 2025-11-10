"""
Rate limiting to prevent API throttling
"""

import time
from threading import Lock
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = deque()
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self.lock:
            now = time.time()
            
            # Remove calls older than 1 minute
            while self.calls and now - self.calls[0] > 60:
                self.calls.popleft()
            
            # Check if we're at the limit
            if len(self.calls) >= self.calls_per_minute:
                # Calculate wait time
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    logger.info(f"⏳ Rate limit reached. Waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    # Remove old calls after waiting
                    now = time.time()
                    while self.calls and now - self.calls[0] > 60:
                        self.calls.popleft()
            
            # Record this call
            self.calls.append(time.time())