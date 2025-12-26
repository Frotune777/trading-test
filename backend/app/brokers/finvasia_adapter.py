"""
Finvasia (Shoonya) Broker Adapter
Implements BrokerAdapter interface for Finvasia Shoonya API.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import hashlib

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


class FinvasiaAdapter(BrokerAdapter):
    """
    Finvasia (Shoonya) API Adapter
    
    Features:
        - Session-based authentication
        - REST API for orders and data
        - WebSocket for real-time streaming
        - Zero brokerage for equity delivery
        - Rate limit: Unlimited (but recommended 10/sec)
    
    Environment Variables:
        - FINVASIA_USER_ID: User ID
        - FINVASIA_PASSWORD: Password
        - FINVASIA_VENDOR_CODE: Vendor code
        - FINVASIA_API_SECRET: API secret
        - FINVASIA_IMEI: IMEI (optional)
    
    Symbol Format: RELIANCE-EQ (for NSE equity)
    """
    
    def __init__(self):
        super().__init__(BrokerType.FINVASIA)
        
        self.user_id = os.getenv("FINVASIA_USER_ID")
        self.password = os.getenv("FINVASIA_PASSWORD")
        self.vendor_code = os.getenv("FINVASIA_VENDOR_CODE")
        self.api_secret = os.getenv("FINVASIA_API_SECRET")
        self.imei = os.getenv("FINVASIA_IMEI", "abc1234")
        
        self.base_url = "https://api.shoonya.com/NorenWClientTP"
        self._client = http_client_pool.get_client()
        self._session_token: Optional[str] = None
        
        # Health tracking
        self._last_successful_call: Optional[datetime] = None
        self._error_count = 0
        self._total_calls = 0
        
        logger.info("FinvasiaAdapter initialized")
    
    @property
    def broker_name(self) -> str:
        return "Finvasia"
    
    async def connect(self) -> bool:
        """
        Connect to Finvasia and get session token.
        
        Returns:
            True if connected successfully
        """
        try:
            if not all([self.user_id, self.password, self.vendor_code, self.api_secret]):
                logger.error("Finvasia credentials not configured")
                return False
            
            # Generate password hash
            pwd_hash = hashlib.sha256(self.password.encode()).hexdigest()
            
            # Login payload
            payload = {
                "source": "API",
                "apkversion": "1.0.0",
                "uid": self.user_id,
                "pwd": pwd_hash,
                "factor2": "second_factor",  # TOTP if enabled
                "vc": self.vendor_code,
                "appkey": hashlib.sha256(f"{self.user_id}|{self.api_secret}".encode()).hexdigest(),
                "imei": self.imei
            }
            
            response = await self._client.post(
                f"{self.base_url}/QuickAuth",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("stat") == "Ok":
                    self._session_token = data.get("susertoken")
                    logger.info(f"Connected to Finvasia: {self.user_id}")
                    self._last_successful_call = datetime.now()
                    return True
                else:
                    logger.error(f"Finvasia login failed: {data.get('emsg', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Finvasia connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Finvasia: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Logout from Finvasia"""
        try:
            if not self._session_token:
                return True
            
            payload = {
                "uid": self.user_id,
                "token": self._session_token
            }
            
            response = await self._client.post(
                f"{self.base_url}/Logout",
                data=payload
            )
            
            self._session_token = None
            logger.info("Disconnected from Finvasia")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from Finvasia: {e}")
            return False
    
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
            cache_key = f"finvasia:ltp:{exchange}:{symbol}"
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Finvasia LTP cache hit: {symbol}")
                return float(cached)
            
            # Ensure connected
            if not self._session_token:
                await self.connect()
            
            # Get token for symbol
            token = await self._get_token(symbol, exchange)
            if not token:
                logger.warning(f"Token not found for {symbol}")
                self._error_count += 1
                return None
            
            # Fetch quotes
            payload = {
                "uid": self.user_id,
                "token": self._session_token,
                "exch": exchange,
                "token": token
            }
            
            response = await self._client.post(
                f"{self.base_url}/GetQuotes",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("stat") == "Ok":
                    ltp = float(data.get("lp", 0))
                    
                    if ltp > 0:
                        # Cache for 5 seconds
                        await redis_client.setex(cache_key, 5, str(ltp))
                        self._last_successful_call = datetime.now()
                        logger.debug(f"Finvasia LTP for {symbol}: {ltp}")
                        return ltp
            
            logger.warning(f"Failed to get Finvasia LTP for {symbol}")
            self._error_count += 1
            return None
            
        except Exception as e:
            logger.error(f"Error getting Finvasia LTP for {symbol}: {e}")
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
            interval: Candle interval (1, 5, 15, 30, 60, D)
            from_date: Start date
            to_date: End date
            exchange: Exchange
            
        Returns:
            DataFrame with OHLC data or None
        """
        try:
            # Ensure connected
            if not self._session_token:
                await self.connect()
            
            # Get token
            token = await self._get_token(symbol, exchange)
            if not token:
                return None
            
            # Map interval
            interval_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "1d": "D"
            }
            finvasia_interval = interval_map.get(interval, "D")
            
            payload = {
                "uid": self.user_id,
                "token": self._session_token,
                "exch": exchange,
                "token": token,
                "st": from_date.strftime("%d-%m-%Y"),
                "et": to_date.strftime("%d-%m-%Y"),
                "intrv": finvasia_interval
            }
            
            response = await self._client.post(
                f"{self.base_url}/TPSeries",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    df["timestamp"] = pd.to_datetime(df["time"], format="%d-%m-%Y %H:%M:%S")
                    df = df.rename(columns={
                        "into": "open",
                        "inth": "high",
                        "intl": "low",
                        "intc": "close",
                        "v": "volume"
                    })
                    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
                    df = df.sort_values("timestamp")
                    
                    logger.info(f"Fetched {len(df)} candles for {symbol} from Finvasia")
                    return df
            
            logger.warning(f"No historical data from Finvasia for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Finvasia historical data for {symbol}: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            # Ensure connected
            if not self._session_token:
                await self.connect()
            
            payload = {
                "uid": self.user_id,
                "token": self._session_token,
                "actid": self.user_id
            }
            
            response = await self._client.post(
                f"{self.base_url}/PositionBook",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    positions = []
                    for pos in data:
                        positions.append(Position(
                            symbol=pos.get("tsym", ""),
                            exchange=pos.get("exch", ""),
                            quantity=int(pos.get("netqty", 0)),
                            average_price=float(pos.get("netavgprc", 0)),
                            pnl=float(pos.get("rpnl", 0))
                        ))
                    
                    logger.info(f"Fetched {len(positions)} positions from Finvasia")
                    return positions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting Finvasia positions: {e}")
            return []
    
    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Place order via Finvasia.
        
        Args:
            order: Order object
            
        Returns:
            Order response or None
        """
        try:
            # Ensure connected
            if not self._session_token:
                await self.connect()
            
            # Get token
            token = await self._get_token(order.symbol, order.exchange)
            if not token:
                logger.error(f"Cannot place order: token not found for {order.symbol}")
                return None
            
            # Map order type
            order_type_map = {
                "MARKET": "MKT",
                "LIMIT": "LMT",
                "SL": "SL-LMT",
                "SL-M": "SL-MKT"
            }
            
            # Prepare order payload
            payload = {
                "uid": self.user_id,
                "actid": self.user_id,
                "token": self._session_token,
                "exch": order.exchange,
                "tsym": f"{order.symbol}-EQ",
                "qty": str(order.quantity),
                "prc": str(order.price) if order.price else "0",
                "trgprc": str(order.trigger_price) if order.trigger_price else "0",
                "prd": order.product_type,
                "trantype": order.action,
                "prctyp": order_type_map.get(order.order_type, "MKT"),
                "ret": "DAY",
                "remarks": "FortuneQUAD"
            }
            
            response = await self._client.post(
                f"{self.base_url}/PlaceOrder",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("stat") == "Ok":
                    order_id = data.get("norenordno")
                    
                    logger.info(f"Finvasia order placed: {order.symbol} {order.action} {order.quantity} - Order ID: {order_id}")
                    
                    return {
                        "order_id": order_id,
                        "status": "PLACED",
                        "broker": "finvasia"
                    }
                else:
                    logger.error(f"Finvasia order placement failed: {data.get('emsg', 'Unknown error')}")
                    return None
            else:
                logger.error(f"Finvasia order placement failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing Finvasia order: {e}")
            return None
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status"""
        try:
            # Ensure connected
            if not self._session_token:
                await self.connect()
            
            payload = {
                "uid": self.user_id,
                "token": self._session_token,
                "norenordno": order_id
            }
            
            response = await self._client.post(
                f"{self.base_url}/SingleOrdHist",
                data=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    order_data = data[0]
                    
                    return {
                        "order_id": order_id,
                        "status": order_data.get("status", "UNKNOWN"),
                        "filled_quantity": int(order_data.get("fillshares", 0)),
                        "average_price": float(order_data.get("avgprc", 0))
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Finvasia order status: {e}")
            return None
    
    async def get_health_status(self) -> BrokerHealth:
        """Get broker health status"""
        error_rate = (self._error_count / self._total_calls * 100) if self._total_calls > 0 else 0
        
        # Determine status
        if not self._session_token:
            status = HealthStatus.UNHEALTHY
            message = "Not connected"
        elif error_rate > 50:
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
    
    async def _get_token(self, symbol: str, exchange: str) -> Optional[str]:
        """
        Get Finvasia token for symbol.
        
        Returns:
            Token or None
        """
        try:
            # Check cache
            cache_key = f"finvasia:token:{exchange}:{symbol}"
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
            
            # For now, return symbol as token
            # In production, should fetch from scrip master
            token = symbol
            
            # Cache for 24 hours
            await redis_client.setex(cache_key, 86400, token)
            
            return token
            
        except Exception as e:
            logger.error(f"Error getting Finvasia token: {e}")
            return None
