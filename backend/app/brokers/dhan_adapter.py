"""
Dhan Broker Adapter
Implements BrokerAdapter interface using Dhan HQ API.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from dhanhq import dhanhq
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


class DhanAdapter(BrokerAdapter):
    """
    Dhan HQ broker adapter.
    
    Features:
        - REST API for quotes, historical data, positions, orders
        - WebSocket for real-time market data
        - Token-based authentication
        - Redis caching with 5s TTL
    
    Credentials Required:
        - DHAN_CLIENT_ID
        - DHAN_ACCESS_TOKEN
    """
    
    def __init__(self):
        super().__init__(BrokerType.DHAN)
        self.client_id = settings.DHAN_CLIENT_ID if hasattr(settings, 'DHAN_CLIENT_ID') else None
        self.access_token = settings.DHAN_ACCESS_TOKEN if hasattr(settings, 'DHAN_ACCESS_TOKEN') else None
        
        self.dhan: Optional[dhanhq] = None
        self._security_ids: Dict[str, str] = {}  # symbol -> security_id mapping
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("DhanAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Dhan"
    
    async def connect(self) -> bool:
        """Connect to Dhan API"""
        try:
            if not self.client_id or not self.access_token:
                logger.error("Dhan credentials not configured")
                return False
            
            self.dhan = dhanhq(
                client_id=self.client_id,
                access_token=self.access_token
            )
            
            # Test connection by fetching fund limits
            funds = self.dhan.get_fund_limits()
            
            if funds['status'] == 'success':
                logger.info(f"Connected to Dhan: Client {self.client_id}")
                self._connected = True
                self._last_successful_call = datetime.now()
                return True
            else:
                logger.error(f"Dhan connection failed: {funds.get('remarks', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Dhan: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Dhan"""
        self._connected = False
        self.dhan = None
        logger.info("Disconnected from Dhan")
        return True
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price from Dhan.
        
        Compliance:
            - Rule #8-9: Caches in Redis with 5s TTL
        """
        if not self._connected or not self.dhan:
            logger.error("Dhan not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get security ID
            security_id = await self._get_security_id(symbol, exchange)
            if not security_id:
                logger.error(f"Could not find security ID for {symbol}")
                return None
            
            # Fetch LTP
            exchange_segment = self.dhan.NSE if exchange == "NSE" else self.dhan.BSE
            
            ltp_data = self.dhan.get_ltp_data(
                exchange_segment=exchange_segment,
                security_id=security_id
            )
            
            if ltp_data['status'] == 'success' and 'data' in ltp_data:
                ltp = float(ltp_data['data']['LTP'])
                
                # Cache in Redis with 5s TTL (Rule #8-9)
                redis_key = f"ltp:dhan:{exchange}:{symbol}"
                cache_payload = {
                    "ltp": ltp,
                    "timestamp": datetime.now().isoformat(),
                    "broker": "dhan"
                }
                await redis_client.setex(redis_key, 5, str(cache_payload))
                
                self._last_successful_call = datetime.now()
                logger.debug(f"Dhan LTP for {symbol}: {ltp}")
                
                return ltp
            else:
                logger.error(f"Dhan LTP fetch failed: {ltp_data.get('remarks', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting LTP from Dhan for {symbol}: {e}")
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
        """Get historical OHLC data from Dhan"""
        if not self._connected or not self.dhan:
            logger.error("Dhan not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get security ID
            security_id = await self._get_security_id(symbol, exchange)
            if not security_id:
                logger.error(f"Could not find security ID for {symbol}")
                return None
            
            # Map interval to Dhan format
            interval_map = {
                "1m": self.dhan.MINUTE,
                "5m": self.dhan.MINUTE_5,
                "15m": self.dhan.MINUTE_15,
                "30m": self.dhan.MINUTE_30,
                "1h": self.dhan.HOUR,
                "1d": self.dhan.DAY
            }
            
            dhan_interval = interval_map.get(interval)
            if not dhan_interval:
                logger.error(f"Invalid interval: {interval}")
                return None
            
            # Fetch historical data
            exchange_segment = self.dhan.NSE if exchange == "NSE" else self.dhan.BSE
            
            hist_data = self.dhan.historical_data(
                security_id=security_id,
                exchange_segment=exchange_segment,
                instrument_type=self.dhan.EQUITY,
                expiry_code=0,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                interval=dhan_interval
            )
            
            if hist_data['status'] == 'success' and 'data' in hist_data:
                data = hist_data['data']
                
                if not data:
                    logger.warning(f"No historical data returned for {symbol}")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                
                # Rename columns to standard format
                df = df.rename(columns={
                    'start_Time': 'timestamp',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                
                # Convert timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Select required columns
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(df)} candles for {symbol} from Dhan")
                
                return df
            else:
                logger.error(f"Dhan historical data fetch failed: {hist_data.get('remarks', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data from Dhan for {symbol}: {e}")
            self._error_count += 1
            return None
    
    async def get_positions(self) -> Optional[List[Position]]:
        """Get current positions from Dhan"""
        if not self._connected or not self.dhan:
            logger.error("Dhan not connected")
            return None
        
        try:
            self._total_requests += 1
            
            position_data = self.dhan.get_positions()
            
            if position_data['status'] == 'success' and 'data' in position_data:
                positions = []
                
                for pos in position_data['data']:
                    if int(pos.get('netQty', 0)) != 0:
                        positions.append(Position(
                            symbol=pos['tradingSymbol'],
                            exchange=pos['exchangeSegment'],
                            quantity=int(pos['netQty']),
                            average_price=float(pos['avgPrice']),
                            pnl=float(pos.get('realizedProfit', 0)),
                            product=pos['productType']
                        ))
                
                self._last_successful_call = datetime.now()
                logger.info(f"Fetched {len(positions)} positions from Dhan")
                
                return positions
            else:
                logger.error(f"Dhan positions fetch failed: {position_data.get('remarks', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting positions from Dhan: {e}")
            self._error_count += 1
            return None
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """Place order with Dhan"""
        if not self._connected or not self.dhan:
            logger.error("Dhan not connected")
            return None
        
        try:
            self._total_requests += 1
            
            # Get security ID
            security_id = await self._get_security_id(order.symbol, order.exchange)
            if not security_id:
                logger.error(f"Could not find security ID for {order.symbol}")
                return None
            
            # Prepare order parameters
            exchange_segment = self.dhan.NSE if order.exchange == "NSE" else self.dhan.BSE
            transaction_type = self.dhan.BUY if order.transaction_type == "BUY" else self.dhan.SELL
            order_type = self.dhan.MARKET if order.order_type == "MARKET" else self.dhan.LIMIT
            product_type = self.dhan.INTRA if order.product == "MIS" else self.dhan.CNC
            
            # Place order
            order_response = self.dhan.place_order(
                security_id=security_id,
                exchange_segment=exchange_segment,
                transaction_type=transaction_type,
                quantity=order.quantity,
                order_type=order_type,
                product_type=product_type,
                price=order.price if order.order_type == "LIMIT" else 0
            )
            
            if order_response['status'] == 'success' and 'data' in order_response:
                order_id = order_response['data']['orderId']
                
                self._last_successful_call = datetime.now()
                logger.info(f"Order placed with Dhan: {order_id}")
                
                return {
                    "order_id": order_id,
                    "broker": "dhan",
                    "status": "PLACED",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Dhan order placement failed: {order_response.get('remarks', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order with Dhan: {e}")
            self._error_count += 1
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status from Dhan"""
        if not self._connected or not self.dhan:
            logger.error("Dhan not connected")
            return None
        
        try:
            self._total_requests += 1
            
            order_status = self.dhan.get_order_by_id(order_id)
            
            if order_status['status'] == 'success' and 'data' in order_status:
                order = order_status['data']
                
                self._last_successful_call = datetime.now()
                return {
                    "order_id": order_id,
                    "status": order['orderStatus'],
                    "filled_quantity": int(order.get('filledQty', 0)),
                    "pending_quantity": int(order.get('quantity', 0)) - int(order.get('filledQty', 0)),
                    "average_price": float(order.get('price', 0)),
                    "broker": "dhan"
                }
            else:
                logger.error(f"Dhan order status fetch failed: {order_status.get('remarks', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order status from Dhan: {e}")
            self._error_count += 1
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get health status of Dhan adapter"""
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
    
    async def _get_security_id(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get security ID for a symbol.
        Caches IDs in memory and Redis.
        """
        cache_key = f"{exchange}:{symbol}"
        
        # Check memory cache
        if cache_key in self._security_ids:
            return self._security_ids[cache_key]
        
        # Check Redis cache
        redis_key = f"security_id:dhan:{cache_key}"
        cached_id = await redis_client.get(redis_key)
        if cached_id:
            self._security_ids[cache_key] = cached_id
            return cached_id
        
        # Fetch from API (would need security master file)
        # For now, return None - in production, implement security master lookup
        logger.warning(f"Security ID lookup not implemented for {symbol}")
        return None
