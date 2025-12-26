"""
Angel One Broker Adapter
Implements BrokerAdapter interface using SmartAPI.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from SmartApi import SmartConnect
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


class AngelOneAdapter(BrokerAdapter):
    """
    Angel One (SmartAPI) broker adapter.
    
    Features:
        - REST API for LTP, historical data, positions, orders
        - WebSocket for real-time market data
        - Token-based authentication
        - Redis caching with 5s TTL
    
    Credentials Required:
        - ANGELONE_API_KEY
        - ANGELONE_CLIENT_ID
        - ANGELONE_PASSWORD (or ACCESS_TOKEN)
    """
    
    def __init__(self):
        super().__init__(BrokerType.ANGELONE)
        self.api_key = settings.ANGELONE_API_KEY if hasattr(settings, 'ANGELONE_API_KEY') else None
        self.client_id = settings.ANGELONE_CLIENT_ID if hasattr(settings, 'ANGELONE_CLIENT_ID') else None
        self.password = settings.ANGELONE_PASSWORD if hasattr(settings, 'ANGELONE_PASSWORD') else None
        
        self.smart_api: Optional[SmartConnect] = None
        self._session_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._symbol_tokens: Dict[str, str] = {}  # symbol -> token mapping
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("AngelOneAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Angel One (SmartAPI)"
    
    async def connect(self) -> bool:
        """
        Connect to Angel One SmartAPI.
        
        Returns:
            True if connection successful
        """
        try:
            if not self.api_key or not self.client_id or not self.password:
                logger.error("Angel One credentials not configured")
                return False
            
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate session
            data = self.smart_api.generateSession(
                clientCode=self.client_id,
                password=self.password
            )
            
            if data['status']:
                self._session_token = data['data']['jwtToken']
                self._refresh_token = data['data']['refreshToken']
                
                # Set session token
                self.smart_api.setSessionExpiryHook(self._session_expiry_hook)
                
                # Get profile to verify connection
                profile = self.smart_api.getProfile(self._refresh_token)
                logger.info(f"Connected to Angel One: {profile['data'].get('name', 'Unknown')}")
                
                self._connected = True
                self._last_successful_call = datetime.now()
                return True
            else:
                logger.error(f"Angel One login failed: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Angel One: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Angel One"""
        try:
            if self.smart_api:
                self.smart_api.terminateSession(self.client_id)
            self._connected = False
            self.smart_api = None
            logger.info("Disconnected from Angel One")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Angel One: {e}")
            return False
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price from Angel One.
        
        Compliance:
            - Rule #8-9: Caches in Redis with 5s TTL
        """
        if not self._connected or not self.smart_api:
            logger.error("Angel One not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get symbol token
            symbol_token = await self._get_symbol_token(symbol, exchange)
            if not symbol_token:
                logger.error(f"Could not find symbol token for {symbol}")
                return None
            
            # Fetch LTP using ltpData
            ltp_data = self.smart_api.ltpData(
                exchange=exchange,
                tradingsymbol=symbol,
                symboltoken=symbol_token
            )
            
            if ltp_data['status'] and 'data' in ltp_data:
                ltp = float(ltp_data['data']['ltp'])
                
                # Cache in Redis with 5s TTL (Rule #8-9)
                redis_key = f"ltp:angelone:{exchange}:{symbol}"
                cache_payload = {
                    "ltp": ltp,
                    "timestamp": datetime.now().isoformat(),
                    "broker": "angelone"
                }
                await redis_client.setex(redis_key, 5, str(cache_payload))
                
                self._last_successful_call = datetime.now()
                logger.debug(f"Angel One LTP for {symbol}: {ltp}")
                
                return ltp
            else:
                logger.error(f"Angel One LTP fetch failed: {ltp_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting LTP from Angel One for {symbol}: {e}")
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
        Get historical OHLC data from Angel One.
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 1d)
            from_date: Start date
            to_date: End date
            exchange: Exchange name
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self._connected or not self.smart_api:
            logger.error("Angel One not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get symbol token
            symbol_token = await self._get_symbol_token(symbol, exchange)
            if not symbol_token:
                logger.error(f"Could not find symbol token for {symbol}")
                return None
            
            # Map interval to Angel One format
            interval_map = {
                "1m": "ONE_MINUTE",
                "5m": "FIVE_MINUTE",
                "15m": "FIFTEEN_MINUTE",
                "30m": "THIRTY_MINUTE",
                "1h": "ONE_HOUR",
                "1d": "ONE_DAY"
            }
            
            angel_interval = interval_map.get(interval)
            if not angel_interval:
                logger.error(f"Invalid interval: {interval}")
                return None
            
            # Fetch historical data
            params = {
                "exchange": exchange,
                "symboltoken": symbol_token,
                "interval": angel_interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            hist_data = self.smart_api.getCandleData(params)
            
            if hist_data['status'] and 'data' in hist_data:
                data = hist_data['data']
                
                if not data:
                    logger.warning(f"No historical data returned for {symbol}")
                    return None
                
                # Convert to DataFrame
                # Angel One format: [timestamp, open, high, low, close, volume]
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Ensure numeric types
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(df)} candles for {symbol} from Angel One")
                
                return df
            else:
                logger.error(f"Angel One historical data fetch failed: {hist_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data from Angel One for {symbol}: {e}")
            self._error_count += 1
            return None
    
    async def get_positions(self) -> Optional[List[Position]]:
        """Get current positions from Angel One"""
        if not self._connected or not self.smart_api:
            logger.error("Angel One not connected")
            return None
        
        try:
            self._total_requests += 1
            
            position_data = self.smart_api.position()
            
            if position_data['status'] and 'data' in position_data:
                positions = []
                
                for pos in position_data['data']:
                    if int(pos.get('netqty', 0)) != 0:  # Only include open positions
                        positions.append(Position(
                            symbol=pos['tradingsymbol'],
                            exchange=pos['exchange'],
                            quantity=int(pos['netqty']),
                            average_price=float(pos['netavgprice']),
                            pnl=float(pos.get('pnl', 0)),
                            product=pos['producttype']
                        ))
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(positions)} positions from Angel One")
                
                return positions
            else:
                logger.error(f"Angel One positions fetch failed: {position_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting positions from Angel One: {e}")
            self._error_count += 1
            return None
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Place order with Angel One.
        
        Compliance:
            - Rule #1-3: Must check execution gate (handled by caller)
            - Rule #34: Every execution attempt logged
        """
        if not self._connected or not self.smart_api:
            logger.error("Angel One not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get symbol token
            symbol_token = await self._get_symbol_token(order.symbol, order.exchange)
            if not symbol_token:
                logger.error(f"Could not find symbol token for {order.symbol}")
                return None
            
            # Prepare order parameters
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": order.symbol,
                "symboltoken": symbol_token,
                "transactiontype": order.transaction_type,
                "exchange": order.exchange,
                "ordertype": order.order_type,
                "producttype": order.product,
                "duration": "DAY",
                "quantity": str(order.quantity)
            }
            
            if order.order_type == "LIMIT" and order.price:
                order_params["price"] = str(order.price)
            
            # Place order
            order_response = self.smart_api.placeOrder(order_params)
            
            if order_response['status'] and 'data' in order_response:
                order_id = order_response['data']['orderid']
                
                self._last_successful_call = datetime.now()
                logger.info(f"Order placed with Angel One: {order_id}")
                
                return {
                    "order_id": order_id,
                    "broker": "angelone",
                    "status": "PLACED",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Angel One order placement failed: {order_response.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order with Angel One: {e}")
            self._error_count += 1
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status from Angel One"""
        if not self._connected or not self.smart_api:
            logger.error("Angel One not connected")
            return None
        
        try:
            self._total_requests += 1
            
            order_book = self.smart_api.orderBook()
            
            if order_book['status'] and 'data' in order_book:
                for order in order_book['data']:
                    if order['orderid'] == order_id:
                        self._last_successful_call = datetime.now()
                        return {
                            "order_id": order_id,
                            "status": order['orderstatus'],
                            "filled_quantity": int(order.get('filledshares', 0)),
                            "pending_quantity": int(order.get('unfilledshares', 0)),
                            "average_price": float(order.get('averageprice', 0)),
                            "broker": "angelone"
                        }
                
                logger.warning(f"Order {order_id} not found in Angel One")
                return None
            else:
                logger.error(f"Angel One order book fetch failed: {order_book.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order status from Angel One: {e}")
            self._error_count += 1
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get health status of Angel One adapter"""
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
    
    async def _get_symbol_token(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get symbol token for a symbol.
        Caches tokens in memory and Redis.
        """
        cache_key = f"{exchange}:{symbol}"
        
        # Check memory cache
        if cache_key in self._symbol_tokens:
            return self._symbol_tokens[cache_key]
        
        # Check Redis cache
        redis_key = f"symbol_token:angelone:{cache_key}"
        cached_token = await redis_client.get(redis_key)
        if cached_token:
            self._symbol_tokens[cache_key] = cached_token
            return cached_token
        
        # Fetch from API
        try:
            # Search for symbol
            search_result = self.smart_api.searchScrip(exchange, symbol)
            
            if search_result['status'] and 'data' in search_result:
                for scrip in search_result['data']:
                    if scrip['symbol'] == symbol:
                        token = scrip['symboltoken']
                        
                        # Cache in memory and Redis (24h TTL)
                        self._symbol_tokens[cache_key] = token
                        await redis_client.setex(redis_key, 86400, token)
                        
                        return token
            
            logger.error(f"Symbol token not found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching symbol token: {e}")
            return None
    
    def _session_expiry_hook(self):
        """Hook called when session expires"""
        logger.warning("Angel One session expired, attempting to refresh...")
        try:
            if self._refresh_token:
                new_token = self.smart_api.generateToken(self._refresh_token)
                if new_token['status']:
                    self._session_token = new_token['data']['jwtToken']
                    logger.info("Angel One session refreshed successfully")
                else:
                    logger.error("Failed to refresh Angel One session")
                    self._connected = False
        except Exception as e:
            logger.error(f"Error refreshing Angel One session: {e}")
            self._connected = False
