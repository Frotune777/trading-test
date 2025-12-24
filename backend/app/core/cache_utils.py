from functools import wraps
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """
    A simple thread-safe in-memory cache with TTL support.
    """
    def __init__(self, default_ttl_seconds: int = 300):
        self.data = {}
        self.ttl = default_ttl_seconds
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key in self.data:
                value, expiry = self.data[key]
                if datetime.now() < expiry:
                    return value
                else:
                    del self.data[key]
            return None

    def set(self, key, value, ttl=None):
        ttl = ttl or self.ttl
        with self.lock:
            self.data[key] = (value, datetime.now() + timedelta(seconds=ttl))

_global_cache = SimpleCache()

def cache_response(ttl_seconds: int = 300):
    """
    Decorator for caching function results.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a simple key based on function name and args
            key = f"{func.__name__}:{str(args[1:] if len(args) > 0 else args)}:{str(kwargs)}"
            
            cached_val = _global_cache.get(key)
            if cached_val is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_val
            
            result = func(*args, **kwargs)
            if result is not None:
                _global_cache.set(key, result, ttl=ttl_seconds)
            
            return result
        return wrapper
    return decorator
