import asyncio
import json
import logging
from typing import Dict, List, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages active WebSocket connections and their subscriptions."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(symbols)
            logger.info(f"Client subscribed to: {symbols}")

    async def broadcast_tick(self, symbol: str, tick_data: Dict[str, Any]):
        """Sends a tick to all clients subscribed to a specific symbol."""
        disconnected = set()
        for connection, subs in self.subscriptions.items():
            # If "ALL" is in subs or the specific symbol/exchange:symbol is there
            if "ALL" in subs or symbol in subs or any(s == symbol for s in subs):
                try:
                    await connection.send_json({
                        "type": "tick",
                        "symbol": symbol,
                        "data": tick_data
                    })
                except Exception:
                    disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

async def redis_listener():
    """Listens to Redis Pub/Sub and broadcasts ticks through ConnectionManager."""
    pubsub = redis_client.pubsub()
    # Subscribe to all market tick channels
    await pubsub.psubscribe("market_ticks:*")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"]
                # Extract symbol from channel 'market_ticks:NSE:RELIANCE' or 'market_ticks:RELIANCE'
                parts = channel.split(":")
                symbol = ":".join(parts[1:]) if len(parts) > 1 else parts[0]
                
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast_tick(symbol, data)
                except Exception as e:
                    logger.error(f"Error broadcasting tick from Redis: {e}")
    finally:
        await pubsub.punsubscribe("market_ticks:*")
        await pubsub.close()

# Start Redis listener as a background task when the app starts
# Note: In a real FastAPI app, this might be handled by Lifespan events
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive subscription messages from the frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            if action == "subscribe":
                symbols = message.get("symbols", [])
                await manager.subscribe(websocket, symbols)
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        manager.disconnect(websocket)
