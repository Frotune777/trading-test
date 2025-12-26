"""
HTTP Client Pool for Broker Adapters
Provides shared httpx client with connection pooling for performance.
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HTTPClientPool:
    """
    Singleton HTTP client pool for all broker adapters.
    
    Features:
        - Connection pooling (max 100 connections)
        - Keep-alive connections (max 20)
        - 30s timeout
        - Automatic retry on connection errors
    
    Usage:
        http_pool = HTTPClientPool()
        response = await http_pool.client.get(url, headers=headers)
    """
    
    _instance: Optional['HTTPClientPool'] = None
    _client: Optional[httpx.AsyncClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize the shared httpx client with connection pooling"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0
                ),
                timeout=httpx.Timeout(30.0),
                follow_redirects=True
            )
            logger.info("HTTP client pool initialized (max_connections=100, keepalive=20)")
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get the shared httpx client"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    async def close(self):
        """Close the HTTP client pool"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client pool closed")


# Global singleton instance
http_pool = HTTPClientPool()
