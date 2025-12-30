import logging
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.redis import redis_client
from app.services.feed_health_monitor import feed_health_monitor, FeedStatus
from app.database.models_monitoring import TradePerformance
from app.database.models_position import PositionSnapshot
from app.brokers.base_adapter import BrokerType

logger = logging.getLogger(__name__)

class MarketDepthLevel(BaseModel):
    price: float
    quantity: int
    orders: Optional[int] = None

class MarketDepth(BaseModel):
    bids: List[MarketDepthLevel] = []
    asks: List[MarketDepthLevel] = []
    total_buy_qty: int = 0
    total_sell_qty: int = 0
    spread: float = 0.0

class UserSymbolState(BaseModel):
    symbol: str
    active_trades_count: int = 0
    total_quantity: int = 0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    pending_orders_count: int = 0

class MarketStateSnapshot(BaseModel):
    symbol: str
    ltp: float = 0.0
    prev_close: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    high: float = 0.0
    low: float = 0.0
    volume: int = 0
    vwap: Optional[float] = None
    depth: MarketDepth = Field(default_factory=MarketDepth)
    feed_status: str = "UNKNOWN"
    data_freshness_ms: int = 0
    is_fresh: bool = False
    timestamp: float = 0.0
    user_state: Optional[UserSymbolState] = None

class MarketStateService:
    """
    Unified Market State Service
    Single source of truth for market and user state for a given symbol.
    Complies with Rules #7-11, #38.
    """
    
    def __init__(self):
        pass
        
    async def get_market_state(
        self, 
        symbol: str, 
        exchange: str = "NSE",
        user_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> MarketStateSnapshot:
        """
        Get unified market state snapshot for a symbol.
        """
        start_time = time.time()
        
        # 1. Fetch Market Data from Redis (Authoritative source)
        market_data = await self._get_redis_market_data(symbol, exchange)
        
        # 2. Fetch Feed Health
        health = await feed_health_monitor.check_health()
        feed_status = health.get("status", "UNKNOWN")
        
        # 3. Calculate Freshness
        ltp_timestamp = market_data.get("timestamp", 0)
        now = time.time()
        freshness_ms = int((now - ltp_timestamp) * 1000) if ltp_timestamp > 0 else 0
        is_fresh = freshness_ms < 5000 if ltp_timestamp > 0 else False # Rule #8
        
        # 4. Fetch User State if user_id provided
        user_state = None
        if user_id and db:
            user_state = await self._get_user_symbol_state(symbol, user_id, db)
            
        # 5. Assemble Snapshot
        snapshot = MarketStateSnapshot(
            symbol=symbol,
            ltp=float(market_data.get("ltp", 0.0)),
            prev_close=float(market_data.get("prev_close", 0.0)),
            change=float(market_data.get("change", 0.0)),
            change_percent=float(market_data.get("change_percent", 0.0)),
            high=float(market_data.get("high", 0.0)),
            low=float(market_data.get("low", 0.0)),
            volume=int(market_data.get("volume", 0)),
            vwap=market_data.get("vwap"),
            depth=self._parse_depth(market_data.get("depth")),
            feed_status=feed_status,
            data_freshness_ms=freshness_ms,
            is_fresh=is_fresh,
            timestamp=ltp_timestamp or now,
            user_state=user_state
        )
        
        execution_time = (time.time() - start_time) * 1000
        logger.debug(f"Market state for {symbol} fetched in {execution_time:.2f}ms")
        
        return snapshot

    async def _get_redis_market_data(self, symbol: str, exchange: str) -> Dict[str, Any]:
        """Fetch real-time data from Redis"""
        try:
            if not redis_client:
                return {}
                
            # Try to get specific key for symbol
            # Conventional key format: ltp:NSE:RELIANCE
            data = await redis_client.get(f"ltp:{exchange}:{symbol}")
            if data:
                return json.loads(data)
            
            # Fallback to general market data if available
            return {}
        except Exception as e:
            logger.error(f"Error fetching market data from Redis for {symbol}: {e}")
            return {}

    async def _get_user_symbol_state(self, symbol: str, user_id: int, db: AsyncSession) -> UserSymbolState:
        """Fetch user-specific symbol state from DB"""
        state = UserSymbolState(symbol=symbol)
        
        try:
            # Fetch active trades
            stmt = select(TradePerformance).where(
                TradePerformance.user_id == user_id,
                TradePerformance.symbol == symbol,
                TradePerformance.status == "OPEN"
            )
            result = await db.execute(stmt)
            trades = result.scalars().all()
            
            state.active_trades_count = len(trades)
            if trades:
                total_qty = sum(t.quantity for t in trades)
                if total_qty > 0:
                    avg_price = sum(t.entry_price * t.quantity for t in trades) / total_qty
                    state.total_quantity = total_qty
                    state.avg_price = avg_price
                    
            # Fetch pending orders (Mocking for now as we need order table)
            # TODO: Integrate with Order table when available
            
            return state
        except Exception as e:
            logger.error(f"Error fetching user symbol state for {symbol}: {e}")
            return state

    def _parse_depth(self, depth_data: Optional[Any]) -> MarketDepth:
        """Parse depth data from Redis JSON"""
        if not depth_data:
            return MarketDepth()
            
        try:
            if isinstance(depth_data, str):
                depth_data = json.loads(depth_data)
                
            bids = [MarketDepthLevel(**b) for b in depth_data.get("bids", [])]
            asks = [MarketDepthLevel(**a) for a in depth_data.get("asks", [])]
            
            return MarketDepth(
                bids=bids,
                asks=asks,
                total_buy_qty=depth_data.get("total_buy_qty", 0),
                total_sell_qty=depth_data.get("total_sell_qty", 0),
                spread=depth_data.get("spread", 0.0)
            )
        except Exception as e:
            logger.warning(f"Error parsing market depth: {e}")
            return MarketDepth()

# Global instance
market_state_service = MarketStateService()
