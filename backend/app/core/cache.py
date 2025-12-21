"""
Intelligent caching system with TTL and persistence
"""

import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-layer cache system with TTL."""
    
    def __init__(self, enabled: bool = True, cache_dir: str = '.cache'):
        self.enabled = enabled
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache
        self.memory_cache = {}
        self.cache_ttl = {}
        
        # Stats
        self.stats = {'hits': 0, 'misses': 0, 'writes': 0}
    
    def _get_cache_key(self, key: str) -> str:
        """Generate safe cache key."""
        if len(key) > 100:
            return hashlib.md5(key.encode()).hexdigest()
        return key.replace('/', '_').replace(':', '_')
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path."""
        safe_key = self._get_cache_key(key)
        return self.cache_dir / f"{safe_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if not self.enabled:
            return None
        
        # Try memory cache
        if key in self.memory_cache:
            if self.cache_ttl[key] > datetime.now():
                self.stats['hits'] += 1
                logger.debug(f"⚡ Memory cache HIT: {key}")
                return self.memory_cache[key]
            else:
                del self.memory_cache[key]
                del self.cache_ttl[key]
        
        # Try disk cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                
                if cached['expires_at'] > datetime.now():
                    self.stats['hits'] += 1
                    logger.debug(f"💾 Disk cache HIT: {key}")
                    
                    # Promote to memory
                    self.memory_cache[key] = cached['value']
                    self.cache_ttl[key] = cached['expires_at']
                    
                    return cached['value']
                else:
                    cache_file.unlink()
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
                cache_file.unlink(missing_ok=True)
        
        self.stats['misses'] += 1
        logger.debug(f"❌ Cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value with TTL."""
        if not self.enabled:
            return
        
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Store in memory
        self.memory_cache[key] = value
        self.cache_ttl[key] = expires_at
        
        # Store on disk
        try:
            cached = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'wb') as f:
                pickle.dump(cached, f)
            
            self.stats['writes'] += 1
            logger.debug(f"💾 Cached: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def clear(self):
        """Clear all cache."""
        self.memory_cache.clear()
        self.cache_ttl.clear()
        
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()
        
        logger.info("🗑️  Cleared all cache")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'writes': self.stats['writes'],
            'hit_rate': f"{hit_rate:.1f}%",
            'memory_entries': len(self.memory_cache),
            'disk_entries': len(list(self.cache_dir.glob('*.cache')))
        }