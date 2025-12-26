import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded Redis client (optional service)
_redis_client = None
_redis_unavailable = False

def get_redis_client():
    """
    Get Redis client (lazy-loaded, optional)
    Returns None if Redis is unavailable
    """
    global _redis_client, _redis_unavailable
    
    if _redis_unavailable:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URI,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1  # Fast fail
            )
        except Exception as e:
            logger.warning(f"Redis unavailable (optional service): {e}")
            _redis_unavailable = True
            return None
    
    return _redis_client

# For backwards compatibility
redis_client = get_redis_client()

async def get_redis():
    """Async getter for dependency injection"""
    return get_redis_client()
