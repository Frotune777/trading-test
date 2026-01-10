import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from datetime import datetime, timezone
import websockets
import httpx
import sys
import os

from app.core.config import settings
from app.core.redis import redis_client
from app.services.alert_service import AlertService
from app.core.database import SessionLocal
from app.database.models_historical import MarketTick

# Configure logger
logger = logging.getLogger(__name__)

class OpenAlgoServiceBridge:
    """
    Bridge to interact with OpenAlgo services via HTTP API.
    Bypasses direct Python imports to avoid Flask/SocketIO context issues.
    """
    
    @staticmethod
    async def get_execution_mode() -> str:
        """
        Determines the execution mode by querying OpenAlgo's Analyzer API.
        Returns: 'DRY_RUN' or 'LIVE'
        """
        try:
            url = f"{settings.OPENALGO_API_URL}/analyzer/"
            # Payload matching AnalyzerSchema (apikey required)
            payload = {"apikey": settings.OPENALGO_API_KEY}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                
            if response.status_code == 200:
                data = response.json()
                # data response from get_analyzer_status usually contains 'data': {'mode': bool}
                # We need to parse correctly based on standard OpenAlgo response format
                # Assuming response is: {'status': 'success', 'data': {'mode': True/False, ...}}
                
                result_data = data.get('data', {})
                is_analyzer_on = result_data.get('mode', False)
                return "DRY_RUN" if is_analyzer_on else "LIVE"
            else:
                logger.error(f"Failed to query OpenAlgo Analyzer: {response.text}")
                return "DRY_RUN" # Fail-safe default
                
        except Exception as e:
            logger.error(f"Error bridging to OpenAlgo Analyzer: {e}")
            return "DRY_RUN" # Fail-safe default

    @staticmethod
    async def send_alert(message: str, telegram_id: Optional[str] = None) -> bool:
        """
        Sends a Telegram alert via OpenAlgo's Broadcast API.
        """
        try:
            # Use Broadcast to reach subscribed admin
            # Path: /api/v1/telegram/broadcast
            url = f"{settings.OPENALGO_API_URL}/telegram/broadcast"
            payload = {
                "apikey": settings.OPENALGO_API_KEY,
                "message": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to send OpenAlgo Alert: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error bridging to OpenAlgo Alerts: {e}")
            return False

    @staticmethod
    async def place_smart_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Places a Smart Order via OpenAlgo API.
        Handles netting and routing automatically.
        Endpoint: /api/v1/placesmartorder/
        """
        try:
            url = f"{settings.OPENALGO_API_URL}/placesmartorder/"
            # Inject API Key if not present
            if "apikey" not in order_data:
                order_data["apikey"] = settings.OPENALGO_API_KEY
                
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=order_data, timeout=10.0)
                
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"OpenAlgo Smart Order Failed: {response.text}")
                try:
                    return response.json() # Return error details if JSON
                except:
                    return {"status": "error", "message": response.text}
                
        except Exception as e:
            logger.error(f"Error placing Smart Order: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def get_open_position(symbol: str, exchange: str = "NSE", product: str = "MIS", strategy: str = "QUAD_STRAT") -> int:
        """
        Get current open position quantity for a symbol.
        Endpoint: /api/v1/openposition/
        """
        try:
            url = f"{settings.OPENALGO_API_URL}/openposition/"
            payload = {
                "apikey": settings.OPENALGO_API_KEY,
                "symbol": symbol,
                "exchange": exchange,
                "product": product,
                "strategy": strategy
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                
            if response.status_code == 200:
                data = response.json()
                # Expected response: {'status': 'success', 'data': {'quantity': 50, ...}}
                return int(data.get('data', {}).get('quantity', 0))
            else:
                logger.error(f"Failed to get Open Position: {response.text}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting Open Position: {e}")
            return 0

# Global instance
openalgo_bridge = OpenAlgoServiceBridge()


class FeedState(Enum):
    HEALTHY = "HEALTHY"   # All symbols active within 15s
    DEGRADED = "DEGRADED" # At least one symbol missing ticks > 15s
    DOWN = "DOWN"         # Disconnected or max retries or circuit breaker

class OpenAlgoWSClient:
    """
    Robust WebSocket client for OpenAlgo streaming API.
    Implements hybrid Redis pattern, Feed Maturity monitoring, and hardened reconnection.
    """
    def __init__(self):
        self.url = settings.OPENALGO_WS_URL
        self.api_key = settings.OPENALGO_API_KEY
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_symbols: Set[str] = set()
        self.reconnect_count = 0
        self.is_running = False
        self.last_tick_time: Dict[str, float] = {}
        self.last_tick_timestamp: Dict[str, int] = {} # For monotonic checks
        self.last_message_time: Optional[float] = None
        self.feed_state = FeedState.DOWN
        self._alerts = AlertService()
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = 0
        self.CIRCUIT_BREAKER_THRESHOLD = 5
        self.CIRCUIT_BREAKER_RESET_TIME = 300 # 5 minutes
        
        # Tick buffering for persistent storage
        self.tick_buffer: asyncio.Queue = asyncio.Queue()
        self.MAX_BATCH_SIZE = 500
        self.FLUSH_INTERVAL = 5 # seconds

    async def connect(self):
        """Main loop for connection and subscription management."""
        self.is_running = True
        
        # Start the maturity monitor loop
        asyncio.create_task(self._maturity_monitor())
        
        # Start the tick flusher loop
        asyncio.create_task(self._flush_ticks_loop())
        
        while self.is_running:
            try:
                # Check circuit breaker
                if self.failure_count >= self.CIRCUIT_BREAKER_THRESHOLD:
                    if time.time() - self.last_failure_time < self.CIRCUIT_BREAKER_RESET_TIME:
                        logger.error("Circuit breaker ACTIVE. Waiting...")
                        self.feed_state = FeedState.DOWN
                        await asyncio.sleep(60)
                        continue
                    else:
                        logger.info("Circuit breaker RESETting.")
                        self.failure_count = 0

                async with websockets.connect(
                    self.url,
                    ping_interval=settings.OPENALGO_HEARTBEAT_INTERVAL,
                    ping_timeout=10
                ) as self.ws:
                    logger.info(f"Connected to OpenAlgo at {self.url}")
                    self.reconnect_count = 0
                    self.failure_count = 0
                    
                    await self._update_feed_state(
                        FeedState.HEALTHY, # Initially assume healthy until monitor kicks in
                        "Successfully connected to OpenAlgo WebSocket."
                    )
                    
                    await self._authenticate()
                    
                    if self.subscribed_symbols:
                        await self.subscribe(list(self.subscribed_symbols))
                    
                    async for message in self.ws:
                        self.last_message_time = time.time()
                        await self._on_message(message)
                        
            except (websockets.ConnectionClosed, Exception) as e:
                logger.error(f"WebSocket error: {e}")
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                await self._update_feed_state(
                    FeedState.DOWN,
                    f"OpenAlgo WebSocket disconnected due to error: {e}",
                    level="ERROR"
                )
                await self._handle_reconnect()

    async def _maturity_monitor(self):
        """Periodically re-evaluate feed health based on tick latency."""
        while self.is_running:
            raw_now = time.time()
            
            if not self.ws or not self.ws.open:
                self.feed_state = FeedState.DOWN
            elif not self.subscribed_symbols:
                # Connected but nothing to do
                self.feed_state = FeedState.HEALTHY 
            else:
                # Check latency for all symbols
                max_allowable_age = 15.0
                is_any_stale = False
                
                for symbol in self.subscribed_symbols:
                    # Construct matching key for internal tracking
                    # Note: We rely on standard exchange:symbol format
                    key = symbol if ":" in symbol else f"NSE:{symbol}"
                    last_t = self.last_tick_time.get(key, 0)
                    if (raw_now - last_t) > max_allowable_age:
                        is_any_stale = True
                        break
                
                if is_any_stale:
                    await self._update_feed_state(FeedState.DEGRADED, "At least one symbol has stale data (>15s)", level="WARNING")
                else:
                    current_state = self.feed_state
                    if current_state != FeedState.HEALTHY:
                         await self._update_feed_state(FeedState.HEALTHY, "All symbols receiving live ticks.")

            await asyncio.sleep(5)

    async def _authenticate(self):
        """Handle authentication logic."""
        auth_msg = {
            "action": "auth",
            "key": self.api_key
        }
        await self.ws.send(json.dumps(auth_msg))
        logger.debug("Sent authentication message")

    async def subscribe(self, symbols: List[str]):
        """Subscribe to a list of symbols."""
        if not self.ws or not self.ws.open:
            logger.warning("WebSocket not connected. Storing symbols for later subscription.")
            self.subscribed_symbols.update(symbols)
            return

        sub_msg = {
            "action": "subscribe",
            "symbols": symbols,
            "mode": "ltp"
        }
        await self.ws.send(json.dumps(sub_msg))
        self.subscribed_symbols.update(symbols)
        
        await self._alerts.emit(
            alert_type="SYMBOL_SUBSCRIBED",
            message=f"Subscribed to new symbols: {symbols}",
            level="INFO"
        )
        
        logger.info(f"Subscribed to symbols: {symbols}")

    async def _update_feed_state(self, new_state: FeedState, message: str, level: str = "INFO"):
        """Centralized feed state management with alerting."""
        if self.feed_state != new_state:
            old_state = self.feed_state
            self.feed_state = new_state
            await self._alerts.emit(
                alert_type=f"FEED_STATE_{new_state.value}",
                message=message,
                level=level,
                metadata={"old_state": old_state.value, "new_state": new_state.value}
            )
            logger.info(f"Feed state changed: {old_state.value} -> {new_state.value}")

    async def _on_message(self, message: str):
        """Handle incoming ticks from OpenAlgo."""
        try:
            data = json.loads(message)
            
            symbol = data.get("symbol")
            exchange = data.get("exchange", "NSE")
            ltp = data.get("ltp")
            ts = data.get("ts") # Timestamp in seconds
            
            if not symbol or ltp is None:
                return

            # Validation: Monotonic Timestamps
            key = f"{exchange}:{symbol}"
            last_ts = self.last_tick_timestamp.get(key, 0)
            if ts and ts < last_ts:
                logger.warning(f"Discarding stale tick for {symbol} (TS: {ts} < {last_ts})")
                return
            
            if ts:
                self.last_tick_timestamp[key] = ts
            
            self.last_tick_time[key] = time.time()

            # Hybrid Storage Pattern
            tick_payload = {
                "ltp": float(ltp),
                "volume": data.get("volume"),
                "oi": data.get("oi"),
                "ts": ts or int(time.time()),
                "source": "openalgo_ws",
                "received_at": time.time()
            }
            
            # KV Authoritative Cache with TTL
            redis_key = f"market:ltp:{exchange}:{symbol}"
            # Redis usage requires async call, assumed working in async context
            if redis_client:
                 await redis_client.set(
                    redis_key, 
                    json.dumps(tick_payload), 
                    ex=settings.REDIS_TICK_TTL
                )
                 # Pub/Sub Notification
                 publish_channel = f"market_ticks:{exchange}:{symbol}"
                 await redis_client.publish(publish_channel, json.dumps(tick_payload))
            
            # Persistent Storage Buffer
            await self.tick_buffer.put({
                "symbol": symbol,
                "exchange": exchange,
                "ltp": float(ltp),
                "volume": data.get("volume"),
                "oi": data.get("oi"),
                "timestamp": ts or int(time.time())
            })
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_reconnect(self):
        """Exponential backoff with jitter."""
        self.reconnect_count += 1
        if self.reconnect_count > settings.OPENALGO_RECONNECT_ATTEMPTS:
            logger.critical("Max reconnection attempts reached. OpenAlgo feed DOWN.")
            self.feed_state = FeedState.DOWN
            await asyncio.sleep(300) 
            return

        # Cap retries for DOWN state per rules ( > 5)
        if self.reconnect_count > 5:
            self.feed_state = FeedState.DOWN

        wait_time = min(2 ** self.reconnect_count + random.uniform(0, 1), 60)
        logger.info(f"Reconnecting in {wait_time:.2f}s (Attempt {self.reconnect_count})")
        await asyncio.sleep(wait_time)

    async def _flush_ticks_loop(self):
        """Periodically flush buffered ticks to PostgreSQL in batches."""
        while self.is_running:
            try:
                ticks_to_save = []
                # Collect ticks from queue
                while not self.tick_buffer.empty() and len(ticks_to_save) < self.MAX_BATCH_SIZE:
                    ticks_to_save.append(await self.tick_buffer.get())
                
                if ticks_to_save:
                    await self._save_ticks_batch(ticks_to_save)
                    for _ in range(len(ticks_to_save)):
                        self.tick_buffer.task_done()
                
                # Wait for next flush interval or until buffer is large
                await asyncio.sleep(self.FLUSH_INTERVAL)
            except Exception as e:
                logger.error(f"Error in tick flusher loop: {e}")
                await asyncio.sleep(self.FLUSH_INTERVAL)

    async def _save_ticks_batch(self, ticks: List[Dict[str, Any]]):
        """Save a batch of ticks to the database."""
        async with SessionLocal() as db:
            try:
                tick_objects = [
                    MarketTick(
                        symbol=t["symbol"],
                        exchange=t["exchange"],
                        ltp=t["ltp"],
                        volume=t["volume"],
                        oi=t["oi"],
                        timestamp=datetime.fromtimestamp(t["timestamp"], tz=timezone.utc)
                    )
                    for t in ticks
                ]
                db.add_all(tick_objects)
                await db.commit()
                logger.debug(f"Successfully saved {len(ticks)} ticks to database.")
            except Exception as e:
                await db.rollback()
                logger.error(f"Database error saving ticks: {e}")

    def stop(self):
        """Stop the client."""
        self.is_running = False
        if self.ws:
            asyncio.create_task(self.ws.close())

    def get_status(self) -> Dict[str, Any]:
        """Return extended status for health checks."""
        now = time.time()
        return {
            "feed_state": self.feed_state.value,
            "connected": self.ws.open if self.ws else False,
            "reconnect_attempts": self.reconnect_count,
            "active_symbols": list(self.subscribed_symbols),
            "last_message_timestamp": datetime.fromtimestamp(
                self.last_message_time, tz=timezone.utc
            ).isoformat() if self.last_message_time else None,
            "per_symbol_ltp_age_ms": {
                s: int((now - t) * 1000) 
                for s, t in self.last_tick_time.items()
            }
        }

# Global instance for the worker to use
openalgo_client = OpenAlgoWSClient()
