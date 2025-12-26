"""
Zerodha Broker Adapter
Implements BrokerAdapter interface using Kite Connect API.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from kiteconnect import KiteConnect, KiteTicker
from app.brokers.base_adapter import (
    BrokerAdapter,
    BrokerType,
    HealthStatus,
    Order,
    Position,
    BrokerHealth
)
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class ZerodhaAdapter(BrokerAdapter):
    """
    Zerodha (Kite Connect) broker adapter.
    
    Features:
        - REST API for LTP, historical data, positions, orders
        - WebSocket (KiteTicker) for real-time ticks
        - Automatic token refresh
        - Redis caching with 5s TTL
    
    Credentials Required:
        - ZERODHA_API_KEY
        - ZERODHA_ACCESS_TOKEN
    """
    
    def __init__(self):
        super().__init__(BrokerType.ZERODHA)
        self.api_key = settings.ZERODHA_API_KEY if hasattr(settings, 'ZERODHA_API_KEY') else None
        self.access_token = settings.ZERODHA_ACCESS_TOKEN if hasattr(settings, 'ZERODHA_ACCESS_TOKEN') else None
        
        self.kite: Optional[KiteConnect] = None
        self.ticker: Optional[KiteTicker] = None
        self._instrument_tokens: Dict[str, int] = {}  # symbol -> token mapping
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("ZerodhaAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Zerodha (Kite Connect)"
    
    async def connect(self) -> bool:
        """
        Connect to Zerodha Kite Connect API.
        
        Returns:
            True if connection successful
        """
        try:
            if not self.api_key or not self.access_token:
                logger.error("Zerodha credentials not configured")
                return False
            
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            
            # Test connection by fetching profile
            profile = self.kite.profile()
            logger.info(f"Connected to Zerodha: {profile.get('user_name', 'Unknown')}")
            
            self._connected = True
            self._last_successful_call = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Zerodha: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Zerodha"""
        self._connected = False
        self.kite = None
        logger.info("Disconnected from Zerodha")
        return True
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price from Zerodha.
        
        Compliance:
            - Rule #8-9: Caches in Redis with 5s TTL
        """
        if not self._connected or not self.kite:
            logger.error("Zerodha not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Format symbol for Zerodha (e.g., "NSE:RELIANCE")
            instrument = f"{exchange}:{symbol}"
            
            # Fetch LTP
            quote = self.kite.ltp(instrument)
            ltp = quote[instrument]["last_price"]
            
            # Cache in Redis with 5s TTL (Rule #8-9)
            redis_key = f"ltp:zerodha:{exchange}:{symbol}"
            cache_payload = {
                "ltp": ltp,
                "timestamp": datetime.now().isoformat(),
                "broker": "zerodha"
            }
            await redis_client.setex(redis_key, 5, str(cache_payload))
            
            self._last_successful_call = datetime.now()
            logger.debug(f"Zerodha LTP for {symbol}: {ltp}")
            
            return ltp
            
        except Exception as e:
            logger.error(f"Error getting LTP from Zerodha for {symbol}: {e}")
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
        Get historical OHLC data from Zerodha.
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 1d)
            from_date: Start date
            to_date: End date
            exchange: Exchange name
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self._connected or not self.kite:
            logger.error("Zerodha not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get instrument token
            instrument_token = await self._get_instrument_token(symbol, exchange)
            if not instrument_token:
                logger.error(f"Could not find instrument token for {symbol}")
                return None
            
            # Map interval to Zerodha format
            interval_map = {
                "1m": "minute",
                "5m": "5minute",
                "15m": "15minute",
                "30m": "30minute",
                "1h": "60minute",
                "1d": "day"
            }
            
            kite_interval = interval_map.get(interval)
            if not kite_interval:
                logger.error(f"Invalid interval: {interval}")
                return None
            
            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=kite_interval
            )
            
            if not data:
                logger.warning(f"No historical data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df = df.rename(columns={"date": "timestamp"})
            
            # Ensure required columns
            required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in Zerodha data")
                return None
            
            df = df[required_cols]
            
            self._last_successful_call = datetime.now()
            logger.info(f"Fetched {len(df)} candles for {symbol} from Zerodha")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data from Zerodha for {symbol}: {e}")
            self._error_count += 1
            return None
    
    async def get_positions(self) -> Optional[List[Position]]:
        """Get current positions from Zerodha"""
        if not self._connected or not self.kite:
            logger.error("Zerodha not connected")
            return None
        
        try:
            self._total_requests += 1
            
            positions_data = self.kite.positions()
            net_positions = positions_data.get("net", [])
            
            positions = []
            for pos in net_positions:
                if pos["quantity"] != 0:  # Only include open positions
                    positions.append(Position(
                        symbol=pos["tradingsymbol"],
                        exchange=pos["exchange"],
                        quantity=pos["quantity"],
                        average_price=pos["average_price"],
                        pnl=pos["pnl"],
                        product=pos["product"]
                    ))
            
            self._last_successful_call = datetime.now()
            logger.info(f"Fetched {len(positions)} positions from Zerodha")
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions from Zerodha: {e}")
            self._error_count += 1
            return None
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Place order with Zerodha.
        
        Compliance:
            - Rule #1-3: Must check execution gate (handled by caller)
            - Rule #34: Every execution attempt logged
        """
        if not self._connected or not self.kite:
            logger.error("Zerodha not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Map order type
            order_type_map = {
                "MARKET": self.kite.ORDER_TYPE_MARKET,
                "LIMIT": self.kite.ORDER_TYPE_LIMIT
            }
            
            transaction_type_map = {
                "BUY": self.kite.TRANSACTION_TYPE_BUY,
                "SELL": self.kite.TRANSACTION_TYPE_SELL
            }
            
            # Place order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=order.exchange,
                tradingsymbol=order.symbol,
                transaction_type=transaction_type_map[order.transaction_type],
                quantity=order.quantity,
                order_type=order_type_map[order.order_type],
                product=order.product,
                price=order.price,
                validity=order.validity
            )
            
            self._last_successful_call = datetime.now()
            logger.info(f"Order placed with Zerodha: {order_id}")
            
            return {
                "order_id": order_id,
                "broker": "zerodha",
                "status": "PLACED",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error placing order with Zerodha: {e}")
            self._error_count += 1
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status from Zerodha"""
        if not self._connected or not self.kite:
            logger.error("Zerodha not connected")
            return None
        
        try:
            self._total_requests += 1
            
            orders = self.kite.orders()
            
            for order in orders:
                if order["order_id"] == order_id:
                    self._last_successful_call = datetime.now()
                    return {
                        "order_id": order_id,
                        "status": order["status"],
                        "filled_quantity": order["filled_quantity"],
                        "pending_quantity": order["pending_quantity"],
                        "average_price": order["average_price"],
                        "broker": "zerodha"
                    }
            
            logger.warning(f"Order {order_id} not found in Zerodha")
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status from Zerodha: {e}")
            self._error_count += 1
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get health status of Zerodha adapter"""
        if not self._connected:
            return BrokerHealth(
                broker_name=self.broker_name,
                status=HealthStatus.UNHEALTHY,
                message="Not connected"
            )
        
        # Calculate error rate
        error_rate = (self._error_count / self._total_requests * 100) if self._total_requests > 0 else 0
        
        # Determine status
        if error_rate > 50:
            status = HealthStatus.UNHEALTHY
        elif error_rate > 20:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return BrokerHealth(
            broker_name=self.broker_name,
            status=status,
            error_rate=error_rate,
            last_successful_call=self._last_successful_call,
            message=f"Error rate: {error_rate:.2f}%"
        )
    
    async def _get_instrument_token(self, symbol: str, exchange: str) -> Optional[int]:
        """
        Get instrument token for a symbol.
        Caches tokens in memory and Redis.
        """
        cache_key = f"{exchange}:{symbol}"
        
        # Check memory cache
        if cache_key in self._instrument_tokens:
            return self._instrument_tokens[cache_key]
        
        # Check Redis cache
        redis_key = f"instrument_token:zerodha:{cache_key}"
        cached_token = await redis_client.get(redis_key)
        if cached_token:
            token = int(cached_token)
            self._instrument_tokens[cache_key] = token
            return token
        
        # Fetch from API
        try:
            instruments = self.kite.instruments(exchange)
            for inst in instruments:
                if inst["tradingsymbol"] == symbol:
                    token = inst["instrument_token"]
                    
                    # Cache in memory and Redis (24h TTL)
                    self._instrument_tokens[cache_key] = token
                    await redis_client.setex(redis_key, 86400, str(token))
                    
                    return token
            
            logger.error(f"Instrument token not found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching instrument token: {e}")
            return None
