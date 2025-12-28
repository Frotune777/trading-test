"""
Angel One REST API Client
HTTP client for order placement, positions, and holdings
"""

import logging
import requests
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import pytz

from app.brokers.angelone.angelone_auth import AngelOneAuth
from app.brokers.angelone.angelone_models import (
    AngelOneOrderData,
    AngelOneOrderResponse,
    AngelOnePosition,
    AngelOneHolding
)
from app.brokers.base_broker import (
    OrderRequest,
    OrderResponse,
    OrderStatus,
    Position,
    Holding
)

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class AngelOneREST:
    """Angel One REST API client"""
    
    def __init__(self, auth: AngelOneAuth, base_url: str):
        """
        Initialize REST client
        
        Args:
            auth: Angel One authentication handler
            base_url: Angel One REST API base URL
        """
        self.auth = auth
        self.base_url = base_url
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = datetime.now(IST)
        self.min_request_interval = 0.1  # 100ms = 10 req/sec
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        now = datetime.now(IST)
        elapsed = (now - self.last_request_time).total_seconds()
        
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = datetime.now(IST)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            max_retries: Maximum retry attempts
            
        Returns:
            Response data
        """
        # Ensure authenticated
        if not await self.auth.ensure_authenticated():
            raise Exception("Authentication failed")
        
        # Rate limiting
        await self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = self.auth.get_headers()
        
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = self.session.get(url, headers=headers)
                elif method == "POST":
                    response = self.session.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = self.session.put(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = self.session.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # Token expired, refresh and retry
                    logger.warning("Token expired, refreshing...")
                    if await self.auth.refresh_access_token():
                        headers = self.auth.get_headers()
                        continue
                    else:
                        raise Exception("Token refresh failed")
                
                if attempt == max_retries - 1:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Request error: {e}")
                    raise
                
                await asyncio.sleep(2 ** attempt)
    
    async def place_order(self, order: OrderRequest) -> OrderResponse:
        """
        Place an order
        
        Args:
            order: Order request
            
        Returns:
            Order response
        """
        try:
            # Convert to Angel One format
            angel_order = {
                "variety": "NORMAL",
                "tradingsymbol": order.symbol.split(':')[1] if ':' in order.symbol else order.symbol,
                "symboltoken": "",  # Need to get from symbol master
                "transactiontype": order.transaction_type.value,
                "exchange": order.exchange,
                "ordertype": order.order_type.value,
                "producttype": order.product_type,
                "duration": "DAY",
                "price": str(order.price) if order.price else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(order.quantity)
            }
            
            response = await self._make_request(
                "POST",
                "/rest/secure/angelbroking/order/v1/placeOrder",
                angel_order
            )
            
            if response.get("status"):
                return OrderResponse(
                    order_id=response["data"]["orderid"],
                    status=OrderStatus.PENDING,
                    message="Order placed successfully",
                    timestamp=datetime.now(IST)
                )
            else:
                return OrderResponse(
                    order_id="",
                    status=OrderStatus.REJECTED,
                    message=response.get("message", "Order placement failed"),
                    timestamp=datetime.now(IST)
                )
                
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return OrderResponse(
                order_id="",
                status=OrderStatus.REJECTED,
                message=str(e),
                timestamp=datetime.now(IST)
            )
    
    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any]
    ) -> OrderResponse:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID
            modifications: Fields to modify
            
        Returns:
            Order response
        """
        try:
            modify_data = {
                "variety": "NORMAL",
                "orderid": order_id,
                **modifications
            }
            
            response = await self._make_request(
                "POST",
                "/rest/secure/angelbroking/order/v1/modifyOrder",
                modify_data
            )
            
            if response.get("status"):
                return OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.OPEN,
                    message="Order modified successfully",
                    timestamp=datetime.now(IST)
                )
            else:
                return OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.REJECTED,
                    message=response.get("message", "Order modification failed"),
                    timestamp=datetime.now(IST)
                )
                
        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return OrderResponse(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                message=str(e),
                timestamp=datetime.now(IST)
            )
    
    async def cancel_order(self, order_id: str, variety: str = "NORMAL") -> OrderResponse:
        """
        Cancel an order
        
        Args:
            order_id: Order ID
            variety: Order variety
            
        Returns:
            Order response
        """
        try:
            cancel_data = {
                "variety": variety,
                "orderid": order_id
            }
            
            response = await self._make_request(
                "POST",
                "/rest/secure/angelbroking/order/v1/cancelOrder",
                cancel_data
            )
            
            if response.get("status"):
                return OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.CANCELLED,
                    message="Order cancelled successfully",
                    timestamp=datetime.now(IST)
                )
            else:
                return OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.REJECTED,
                    message=response.get("message", "Order cancellation failed"),
                    timestamp=datetime.now(IST)
                )
                
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return OrderResponse(
                order_id=order_id,
                status=OrderStatus.REJECTED,
                message=str(e),
                timestamp=datetime.now(IST)
            )
    
    async def get_order_book(self) -> List[OrderResponse]:
        """
        Get all orders
        
        Returns:
            List of orders
        """
        try:
            response = await self._make_request(
                "GET",
                "/rest/secure/angelbroking/order/v1/getOrderBook"
            )
            
            orders = []
            if response.get("status") and response.get("data"):
                for order_data in response["data"]:
                    # Map Angel One status to our status
                    status_map = {
                        "open": OrderStatus.OPEN,
                        "complete": OrderStatus.COMPLETE,
                        "cancelled": OrderStatus.CANCELLED,
                        "rejected": OrderStatus.REJECTED,
                    }
                    
                    status = status_map.get(
                        order_data.get("status", "").lower(),
                        OrderStatus.PENDING
                    )
                    
                    orders.append(OrderResponse(
                        order_id=order_data.get("orderid", ""),
                        status=status,
                        message=order_data.get("text", ""),
                        timestamp=datetime.now(IST)
                    ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Get order book error: {e}")
            return []
    
    async def get_positions(self) -> List[Position]:
        """
        Get current positions
        
        Returns:
            List of positions
        """
        try:
            response = await self._make_request(
                "GET",
                "/rest/secure/angelbroking/order/v1/getPosition"
            )
            
            positions = []
            if response.get("status") and response.get("data"):
                for pos_data in response["data"]:
                    # Convert Angel One position to our format
                    quantity = int(pos_data.get("netqty", "0"))
                    avg_price = float(pos_data.get("avgnetprice", "0"))
                    ltp = float(pos_data.get("ltp", "0")) if pos_data.get("ltp") else avg_price
                    
                    pnl = (ltp - avg_price) * quantity
                    
                    positions.append(Position(
                        symbol=pos_data.get("tradingsymbol", ""),
                        exchange=pos_data.get("exchange", ""),
                        quantity=quantity,
                        average_price=avg_price,
                        ltp=ltp,
                        pnl=pnl,
                        product_type=pos_data.get("producttype", "")
                    ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return []
    
    async def get_holdings(self) -> List[Holding]:
        """
        Get holdings
        
        Returns:
            List of holdings
        """
        try:
            response = await self._make_request(
                "GET",
                "/rest/secure/angelbroking/portfolio/v1/getHolding"
            )
            
            holdings = []
            if response.get("status") and response.get("data"):
                for holding_data in response["data"]:
                    quantity = int(holding_data.get("quantity", "0"))
                    avg_price = float(holding_data.get("averageprice", "0"))
                    ltp = float(holding_data.get("ltp", "0"))
                    
                    pnl = (ltp - avg_price) * quantity
                    
                    holdings.append(Holding(
                        symbol=holding_data.get("tradingsymbol", ""),
                        exchange=holding_data.get("exchange", ""),
                        quantity=quantity,
                        average_price=avg_price,
                        ltp=ltp,
                        pnl=pnl
                    ))
            
            return holdings
            
        except Exception as e:
            logger.error(f"Get holdings error: {e}")
            return []
