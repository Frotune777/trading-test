"""
Upstox Broker Adapter
Implements BrokerAdapter interface for Upstox API v2.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from app.brokers.base_adapter import (
    BrokerAdapter,
    BrokerType,
    Order,
    Position,
    BrokerHealth,
    HealthStatus
)
from app.core.redis import redis_client
from app.core.http_client import http_client_pool

logger = logging.getLogger(__name__)


class UpstoxAdapter(BrokerAdapter):
    """
    Upstox API v2 Adapter
    
    Features:
        - OAuth 2.0 authentication
        - REST API for orders and data
        - WebSocket for real-time streaming
        - Rate limit: 25 requests/second
    
    Environment Variables:
        - UPSTOX_API_KEY: API key
        - UPSTOX_API_SECRET: API secret
        - UPSTOX_ACCESS_TOKEN: Access token (from OAuth flow)
    
    Symbol Format: NSE_EQ|INE002A01018 (exchange_segment|instrument_key)
    """
    
    def __init__(self):
        super().__init__(BrokerType.UPSTOX)
        
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        
        self.base_url = "https://api.upstox.com/v2"
        self._client = http_client_pool.get_client()
        
        # Health tracking
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_calls = 0
        
        logger.info("UpstoxAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Upstox"
    
    async def connect(self) -> bool:
        """
        Verify Upstox connection.
        
        Returns:
            True if connected successfully
        """
        try:
            if not self.access_token:
                logger.error("Upstox access token not configured")
                return False
            
            # Verify token by fetching user profile
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                f"{self.base_url}/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Connected to Upstox: {data.get('data', {}).get('user_name', 'Unknown')}")
                self._last_successful_call = datetime.now()
                return True
            else:
                logger.error(f"Upstox connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Upstox: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Upstox (no-op for REST API)"""
        logger.info("Disconnected from Upstox")
        return True
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price for symbol.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange (NSE, BSE, NFO, etc.)
            
        Returns:
            LTP or None if failed
        """
        try:
            self._total_calls += 1
            
            # Check Redis cache first
            cache_key = f"upstox:ltp:{exchange}:{symbol}"
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Upstox LTP cache hit: {symbol}")
                return float(cached)
            
            # Get instrument key
            instrument_key = await self._get_instrument_key(symbol, exchange)
            if not instrument_key:
                logger.warning(f"Instrument key not found for {symbol}")
                self._error_count += 1
                return None
            
            # Fetch LTP
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                f"{self.base_url}/market-quote/ltp",
                params={"instrument_key": instrument_key},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                ltp = data.get("data", {}).get(instrument_key, {}).get("last_price")
                
                if ltp:
                    # Cache for 5 seconds
                    await redis_client.setex(cache_key, 5, str(ltp))
                    self._last_successful_call = datetime.now()
                    logger.debug(f"Upstox LTP for {symbol}: {ltp}")
                    return float(ltp)
            
            logger.warning(f"Failed to get Upstox LTP for {symbol}: {response.status_code}")
            self._error_count += 1
            return None
            
        except Exception as e:
            logger.error(f"Error getting Upstox LTP for {symbol}: {e}")
            self._error_count += 1
            return None
    
    async def get_historical_data(
        self,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        exchange: str = "NSE"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLC data.
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (1minute, 30minute, day, week, month)
            from_date: Start date
            to_date: End date
            exchange: Exchange
            
        Returns:
            DataFrame with OHLC data or None
        """
        try:
            # Get instrument key
            instrument_key = await self._get_instrument_key(symbol, exchange)
            if not instrument_key:
                return None
            
            # Map interval
            interval_map = {
                "1m": "1minute",
                "5m": "5minute",
                "15m": "15minute",
                "30m": "30minute",
                "1h": "60minute",
                "1d": "day"
            }
            upstox_interval = interval_map.get(interval, "day")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                f"{self.base_url}/historical-candle/{instrument_key}/{upstox_interval}/{to_date.strftime('%Y-%m-%d')}/{from_date.strftime('%Y-%m-%d')}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get("data", {}).get("candles", [])
                
                if candles:
                    # Convert to DataFrame
                    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df = df.sort_values("timestamp")
                    
                    logger.info(f"Fetched {len(df)} candles for {symbol} from Upstox")
                    return df
            
            logger.warning(f"No historical data from Upstox for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Upstox historical data for {symbol}: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                f"{self.base_url}/portfolio/short-term-positions",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                positions_data = data.get("data", [])
                
                positions = []
                for pos in positions_data:
                    positions.append(Position(
                        symbol=pos.get("trading_symbol", ""),
                        exchange=pos.get("exchange", ""),
                        quantity=int(pos.get("quantity", 0)),
                        average_price=float(pos.get("average_price", 0)),
                        pnl=float(pos.get("unrealised_profit", 0))
                    ))
                
                logger.info(f"Fetched {len(positions)} positions from Upstox")
                return positions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting Upstox positions: {e}")
            return []
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Place order via Upstox.
        
        Args:
            order: Order object
            
        Returns:
            Order response or None
        """
        try:
            # Get instrument key
            instrument_key = await self._get_instrument_key(order.symbol, order.exchange)
            if not instrument_key:
                logger.error(f"Cannot place order: instrument key not found for {order.symbol}")
                return None
            
            # Prepare order payload
            payload = {
                "quantity": order.quantity,
                "product": order.product_type,
                "validity": "DAY",
                "price": order.price if order.order_type != "MARKET" else 0,
                "tag": "FortuneQUAD",
                "instrument_token": instrument_key,
                "order_type": order.order_type,
                "transaction_type": order.action,
                "disclosed_quantity": 0,
                "trigger_price": order.trigger_price if order.trigger_price else 0,
                "is_amo": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = await self._client.post(
                f"{self.base_url}/order/place",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get("data", {}).get("order_id")
                
                logger.info(f"Upstox order placed: {order.symbol} {order.action} {order.quantity} - Order ID: {order_id}")
                
                return {
                    "order_id": order_id,
                    "status": "PLACED",
                    "broker": "upstox"
                }
            else:
                logger.error(f"Upstox order placement failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing Upstox order: {e}")
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            response = await self._client.get(
                f"{self.base_url}/order/details",
                params={"order_id": order_id},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                order_data = data.get("data", [{}])[0]
                
                return {
                    "order_id": order_id,
                    "status": order_data.get("status", "UNKNOWN"),
                    "filled_quantity": order_data.get("filled_quantity", 0),
                    "average_price": order_data.get("average_price", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Upstox order status: {e}")
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get broker health status"""
        error_rate = (self._error_count / self._total_calls * 100) if self._total_calls > 0 else 0
        
        # Determine status
        if error_rate > 50:
            status = HealthStatus.UNHEALTHY
            message = f"High error rate: {error_rate:.1f}%"
        elif error_rate > 20:
            status = HealthStatus.DEGRADED
            message = f"Elevated error rate: {error_rate:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = "OK"
        
        return BrokerHealth(
            broker_name=self.broker_name,
            status=status,
            error_rate=error_rate,
            last_successful_call=self._last_successful_call,
            message=message
        )
    
    async def _get_instrument_key(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get Upstox instrument key for symbol.
        
        Upstox uses format: NSE_EQ|INE002A01018
        
        Returns:
            Instrument key or None
        """
        try:
            # Check cache
            cache_key = f"upstox:instrument:{exchange}:{symbol}"
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
            
            # Map exchange to Upstox format
            exchange_map = {
                "NSE": "NSE_EQ",
                "BSE": "BSE_EQ",
                "NFO": "NSE_FO",
                "MCX": "MCX_FO"
            }
            upstox_exchange = exchange_map.get(exchange, "NSE_EQ")
            
            # For now, construct basic instrument key
            # In production, should fetch from instrument master
            instrument_key = f"{upstox_exchange}|{symbol}"
            
            # Cache for 24 hours
            await redis_client.setex(cache_key, 86400, instrument_key)
            
            return instrument_key
            
        except Exception as e:
            logger.error(f"Error getting Upstox instrument key: {e}")
            return None
