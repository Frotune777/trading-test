import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

class AlertConnectionManager:
    """Manages active WebSocket connections for alerts."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.user_subscriptions[websocket] = set()
        logger.info(f"New alert client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.user_subscriptions:
            del self.user_subscriptions[websocket]
        logger.info(f"Alert client disconnected. Total clients: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, user_ids: list[str]):
        if websocket in self.user_subscriptions:
            self.user_subscriptions[websocket].update(user_ids)
            logger.info(f"Client subscribed to alerts for users: {user_ids}")

    async def broadcast_alert(self, target_user_id: str, alert_data: Dict[str, Any]):
        """Sends an alert to all clients subscribed to the target user_id."""
        disconnected = set()
        for connection, subs in self.user_subscriptions.items():
            if target_user_id in subs or "ALL" in subs:
                try:
                    await connection.send_json({
                        "type": "alert",
                        "user_id": target_user_id,
                        "data": alert_data
                    })
                except Exception:
                    disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = AlertConnectionManager()

async def redis_listener():
    """Listens to Redis Pub/Sub and broadcasts alerts."""
    if not redis_client:
        logger.warning("Redis unavailable, alert broadcasting disabled")
        return

    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("alerts:*")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"]
                # Channel format: alerts:{user_id}
                parts = channel.split(":")
                if len(parts) > 1:
                    user_id = parts[1]
                    try:
                        data = json.loads(message["data"])
                        await manager.broadcast_alert(user_id, data)
                    except Exception as e:
                        logger.error(f"Error broadcasting alert from Redis: {e}")
    except Exception as e:
        logger.error(f"Redis listener error: {e}")
    finally:
        await pubsub.punsubscribe("alerts:*")
        await pubsub.close()

@router.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simple protocol: {"action": "subscribe", "user_id": "user123"}
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    user_id = message.get("user_id")
                    if user_id:
                        await manager.subscribe(websocket, [user_id])
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Alert WebSocket endpoint error: {e}")
        manager.disconnect(websocket)
