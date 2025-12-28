"""
Intelligent Authentication Caching Module
Implements TTL-based caching with session-aware expiry.
Adopted from OpenAlgo's caching strategy.
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from cachetools import TTLCache
import pytz

logger = logging.getLogger(__name__)

def get_session_based_cache_ttl() -> int:
    """
    Calculate cache TTL based on daily session expiry time.
    
    For Indian markets, sessions typically end at 3:30 PM IST.
    We add a buffer and expire caches at the configured time (default 3:00 AM IST).
    
    Returns:
        int: TTL in seconds until next session expiry
    """
    try:
        # Get session expiry time from environment (default 3 AM IST)
        expiry_time = os.getenv('SESSION_EXPIRY_TIME', '03:00')
        hour, minute = map(int, expiry_time.split(':'))
        
        # Calculate time until next session expiry
        now_utc = datetime.now(pytz.timezone('UTC'))
        now_ist = now_utc.astimezone(pytz.timezone('Asia/Kolkata'))
        
        # Today's expiry time
        today_expiry = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If we've passed today's expiry, use tomorrow's expiry
        if now_ist >= today_expiry:
            today_expiry += timedelta(days=1)
        
        # Calculate seconds until expiry
        time_until_expiry = (today_expiry - now_ist).total_seconds()
        
        # Use time until session expiry, with reasonable bounds
        # Minimum 5 minutes, maximum 24 hours
        ttl_seconds = max(300, min(time_until_expiry, 24 * 3600))
        
        logger.debug(f"Auth cache TTL set to {ttl_seconds} seconds until session expiry at {today_expiry.strftime('%H:%M IST')}")
        return int(ttl_seconds)
        
    except Exception as e:
        logger.warning(f"Could not calculate session-based cache TTL, using 5-minute default: {e}")
        return 300  # Fallback to 5 minutes

# Initialize caches with session-based TTL
# These are module-level singletons

# Auth token cache: Maps user_id -> auth data
# TTL: Until session expiry (typically 12-24 hours)
auth_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())

# Feed token cache: Maps user_id -> feed token
# TTL: Until session expiry
feed_token_cache = TTLCache(maxsize=1024, ttl=get_session_based_cache_ttl())

# Broker cache: Maps user_id -> broker_name
# TTL: 5 minutes (broker rarely changes, but keep it fresh)
broker_cache = TTLCache(maxsize=1024, ttl=300)

# Verified API key cache: Maps SHA256(api_key) -> user_id
# TTL: 10 hours (long TTL is safe because cache is invalidated on key regeneration)
# Security: Only caches user_id (not sensitive), never stores plaintext API key
verified_api_key_cache = TTLCache(maxsize=1024, ttl=36000)

# Invalid API key cache: Maps SHA256(api_key) -> True
# TTL: 5 minutes (prevents brute force, but doesn't permanently block)
# Security: Short TTL prevents cache poisoning
invalid_api_key_cache = TTLCache(maxsize=512, ttl=300)

def get_cache_key(api_key: str) -> str:
    """
    Generate a secure cache key from an API key.
    
    Uses SHA256 to ensure plaintext API keys are never stored in cache.
    
    Args:
        api_key: The API key to hash
        
    Returns:
        str: SHA256 hash of the API key (hex format)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def cache_verified_api_key(api_key: str, user_id: str) -> None:
    """
    Cache a verified API key.
    
    Args:
        api_key: The API key (will be hashed for storage)
        user_id: The user ID associated with this key
    """
    cache_key = get_cache_key(api_key)
    verified_api_key_cache[cache_key] = user_id
    logger.debug(f"Cached verified API key for user_id: {user_id}")

def get_cached_user_id(api_key: str) -> Optional[str]:
    """
    Get user ID from verified API key cache.
    
    Args:
        api_key: The API key to look up
        
    Returns:
        str: User ID if found in cache, None otherwise
    """
    cache_key = get_cache_key(api_key)
    user_id = verified_api_key_cache.get(cache_key)
    if user_id:
        logger.debug(f"Cache hit for verified API key: user_id={user_id}")
    return user_id

def cache_invalid_api_key(api_key: str) -> None:
    """
    Cache an invalid API key to prevent repeated expensive verifications.
    
    Args:
        api_key: The invalid API key (will be hashed for storage)
    """
    cache_key = get_cache_key(api_key)
    invalid_api_key_cache[cache_key] = True
    logger.debug("Cached invalid API key")

def is_cached_invalid(api_key: str) -> bool:
    """
    Check if an API key is in the invalid cache.
    
    Args:
        api_key: The API key to check
        
    Returns:
        bool: True if key is known to be invalid
    """
    cache_key = get_cache_key(api_key)
    is_invalid = cache_key in invalid_api_key_cache
    if is_invalid:
        logger.debug("Cache hit for invalid API key")
    return is_invalid

def invalidate_user_cache(user_id: str) -> None:
    """
    Invalidate all cached data for a user when their credentials change.
    
    Security: Ensures old API keys/tokens are not usable after regeneration.
    
    Args:
        user_id: User identifier
    """
    # Clear all caches that might contain this user's data
    auth_cache.clear()
    broker_cache.clear()
    feed_token_cache.clear()
    verified_api_key_cache.clear()
    invalid_api_key_cache.clear()
    logger.info(f"Cleared all caches for user_id: {user_id}")

def get_cache_stats() -> dict:
    """
    Get statistics about cache usage.
    
    Returns:
        dict: Cache statistics
    """
    return {
        'auth_cache': {
            'size': len(auth_cache),
            'maxsize': auth_cache.maxsize,
            'ttl': auth_cache.ttl
        },
        'verified_api_key_cache': {
            'size': len(verified_api_key_cache),
            'maxsize': verified_api_key_cache.maxsize,
            'ttl': verified_api_key_cache.ttl
        },
        'invalid_api_key_cache': {
            'size': len(invalid_api_key_cache),
            'maxsize': invalid_api_key_cache.maxsize,
            'ttl': invalid_api_key_cache.ttl
        }
    }
