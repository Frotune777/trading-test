"""
Fyers Broker Adapter
Implements BrokerAdapter interface using Fyers API v3.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from fyers_apiv3 import fyersModel
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


class FyersAdapter(BrokerAdapter):
    """
    Fyers API v3 broker adapter.
    
    Features:
        - REST API for quotes, historical data, positions, orders
        - WebSocket for real-time market data
        - OAuth-based authentication
        - Redis caching with 5s TTL
    
    Credentials Required:
        - FYERS_APP_ID
        - FYERS_ACCESS_TOKEN
    """
    
    def __init__(self):
        super().__init__(BrokerType.FYERS)
        self.app_id = settings.FYERS_APP_ID if hasattr(settings, 'FYERS_APP_ID') else None
        self.access_token = settings.FYERS_ACCESS_TOKEN if hasattr(settings, 'FYERS_ACCESS_TOKEN') else None
        
        self.fyers: Optional[fyersModel.FyersModel] = None
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("FyersAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Fyers"
    
    async def connect(self) -> bool:
        """Connect to Fyers API"""
        try:
            if not self.app_id or not self.access_token:
                logger.error("Fyers credentials not configured")
                return False
            
            self.fyers = fyersModel.FyersModel(
                client_id=self.app_id,
                token=self.access_token,
                log_path=""
            )
            
            # Test connection by fetching profile
            profile = self.fyers.get_profile()
            
            if profile['s'] == 'ok':
                logger.info(f"Connected to Fyers: {profile['data'].get('name', 'Unknown')}")
                self._connected = True
                self._last_successful_call = datetime.now()
                return True
            else:
                logger.error(f"Fyers connection failed: {profile.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Fyers: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Fyers"""
        self._connected = False
        self.fyers = None
        logger.info("Disconnected from Fyers")
        return True
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price from Fyers.
        
        Compliance:
            - Rule #8-9: Caches in Redis with 5s TTL
        """
        if not self._connected or not self.fyers:
            logger.error("Fyers not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Format symbol for Fyers (e.g., "NSE:RELIANCE-EQ")
            fyers_symbol = f"{exchange}:{symbol}-EQ"
            
            # Fetch quotes
            data = {"symbols": fyers_symbol}
            quotes = self.fyers.quotes(data)
            
            if quotes['s'] == 'ok' and 'd' in quotes:
                quote_data = quotes['d'][0]
                ltp = quote_data['v']['lp']
                
                # Cache in Redis with 5s TTL (Rule #8-9)
                redis_key = f"ltp:fyers:{exchange}:{symbol}"
                cache_payload = {
                    "ltp": ltp,
                    "timestamp": datetime.now().isoformat(),
                    "broker": "fyers"
                }
                await redis_client.setex(redis_key, 5, str(cache_payload))
                
                self._last_successful_call = datetime.now()
                logger.debug(f"Fyers LTP for {symbol}: {ltp}")
                
                return ltp
            else:
                logger.error(f"Fyers LTP fetch failed: {quotes.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting LTP from Fyers for {symbol}: {e}")
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
        """Get historical OHLC data from Fyers"""
        if not self._connected or not self.fyers:
            logger.error("Fyers not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Format symbol
            fyers_symbol = f"{exchange}:{symbol}-EQ"
            
            # Map interval to Fyers format
            interval_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "1d": "D"
            }
            
            fyers_interval = interval_map.get(interval)
            if not fyers_interval:
                logger.error(f"Invalid interval: {interval}")
                return None
            
            # Fetch historical data
            data = {
                "symbol": fyers_symbol,
                "resolution": fyers_interval,
                "date_format": "1",
                "range_from": from_date.strftime("%Y-%m-%d"),
                "range_to": to_date.strftime("%Y-%m-%d"),
                "cont_flag": "1"
            }
            
            hist_data = self.fyers.history(data)
            
            if hist_data['s'] == 'ok' and 'candles' in hist_data:
                candles = hist_data['candles']
                
                if not candles:
                    logger.warning(f"No historical data returned for {symbol}")
                    return None
                
                # Convert to DataFrame
                # Fyers format: [timestamp, open, high, low, close, volume]
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(df)} candles for {symbol} from Fyers")
                
                return df
            else:
                logger.error(f"Fyers historical data fetch failed: {hist_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data from Fyers for {symbol}: {e}")
            self._error_count += 1
            return None
    
    async def get_positions(self) -> Optional[List[Position]]:
        """Get current positions from Fyers"""
        if not self._connected or not self.fyers:
            logger.error("Fyers not connected")
            return None
        
        try:
            self._total_requests += 1
            
            position_data = self.fyers.positions()
            
            if position_data['s'] == 'ok' and 'netPositions' in position_data:
                positions = []
                
                for pos in position_data['netPositions']:
                    if int(pos.get('netQty', 0)) != 0:
                        positions.append(Position(
                            symbol=pos['symbol'].split(':')[1].replace('-EQ', ''),
                            exchange=pos['symbol'].split(':')[0],
                            quantity=int(pos['netQty']),
                            average_price=float(pos['avgPrice']),
                            pnl=float(pos.get('pl', 0)),
                            product=pos['productType']
                        ))
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(positions)} positions from Fyers")
                
                return positions
            else:
                logger.error(f"Fyers positions fetch failed: {position_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting positions from Fyers: {e}")
            self._error_count += 1
            return None
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """Place order with Fyers"""
        if not self._connected or not self.fyers:
            logger.error("Fyers not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Format symbol
            fyers_symbol = f"{order.exchange}:{order.symbol}-EQ"
            
            # Prepare order data
            order_data = {
                "symbol": fyers_symbol,
                "qty": order.quantity,
                "type": 2 if order.order_type == "MARKET" else 1,  # 1=LIMIT, 2=MARKET
                "side": 1 if order.transaction_type == "BUY" else -1,  # 1=BUY, -1=SELL
                "productType": order.product,
                "limitPrice": order.price if order.order_type == "LIMIT" else 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }
            
            # Place order
            order_response = self.fyers.place_order(order_data)
            
            if order_response['s'] == 'ok' and 'id' in order_response:
                order_id = order_response['id']
                
                self._last_successful_call = datetime.now()
                logger.info(f"Order placed with Fyers: {order_id}")
                
                return {
                    "order_id": order_id,
                    "broker": "fyers",
                    "status": "PLACED",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Fyers order placement failed: {order_response.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order with Fyers: {e}")
            self._error_count += 1
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status from Fyers"""
        if not self._connected or not self.fyers:
            logger.error("Fyers not connected")
            return None
        
        try:
            self._total_requests += 1
            
            order_book = self.fyers.orderbook()
            
            if order_book['s'] == 'ok' and 'orderBook' in order_book:
                for order in order_book['orderBook']:
                    if order['id'] == order_id:
                        self._last_successful_call = datetime.now()
                        return {
                            "order_id": order_id,
                            "status": order['status'],
                            "filled_quantity": int(order.get('filledQty', 0)),
                            "pending_quantity": int(order.get('qty', 0)) - int(order.get('filledQty', 0)),
                            "average_price": float(order.get('tradedPrice', 0)),
                            "broker": "fyers"
                        }
                
                logger.warning(f"Order {order_id} not found in Fyers")
                return None
            else:
                logger.error(f"Fyers order book fetch failed: {order_book.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order status from Fyers: {e}")
            self._error_count += 1
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get health status of Fyers adapter"""
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
