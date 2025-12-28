"""
WebSocket Server for Real-Time Market Data Streaming
Handles client connections, authentication, and subscription management
"""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from app.services.user_auth_service import UserAuthService
from app.websocket.subscription_manager import SubscriptionManager
from app.websocket.zmq_publisher import ZMQPublisher
from app.core.database import SessionLocalSync

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time market data"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.subscription_manager = SubscriptionManager()
        self.zmq_publisher = ZMQPublisher()
        self.authenticated_clients: Dict[WebSocketServerProtocol, int] = {}  # ws -> user_id
        
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start ZMQ publisher
        await self.zmq_publisher.start()
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"✅ WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new client connection"""
        client_id = id(websocket)
        logger.info(f"New client connected: {client_id}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            await self.cleanup_client(websocket)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "auth":
                await self.handle_auth(websocket, data)
            elif msg_type == "subscribe":
                await self.handle_subscribe(websocket, data)
            elif msg_type == "unsubscribe":
                await self.handle_unsubscribe(websocket, data)
            elif msg_type == "ping":
                await self.handle_ping(websocket)
            else:
                await self.send_error(websocket, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, str(e))
    
    async def handle_auth(self, websocket: WebSocketServerProtocol, data: Dict):
        """Authenticate client with API key"""
        api_key = data.get("api_key")
        
        if not api_key:
            await self.send_error(websocket, "API key required")
            return
        
        # Verify API key
        db = SessionLocalSync()
        try:
            auth_service = UserAuthService(db)
            user = auth_service.verify_api_key(api_key)
            
            if user:
                self.authenticated_clients[websocket] = user.id
                await websocket.send(json.dumps({
                    "type": "authenticated",
                    "status": "success",
                    "user_id": user.id,
                    "username": user.username
                }))
                logger.info(f"Client authenticated: user_id={user.id}")
            else:
                await self.send_error(websocket, "Invalid API key")
        finally:
            db.close()
    
    async def handle_subscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """Subscribe client to symbols"""
        if websocket not in self.authenticated_clients:
            await self.send_error(websocket, "Not authenticated")
            return
        
        symbols = data.get("symbols", [])
        mode = data.get("mode", "ltp")  # ltp, quote, full
        
        if not symbols:
            await self.send_error(websocket, "No symbols provided")
            return
        
        # Add subscriptions
        for symbol in symbols:
            self.subscription_manager.add_subscription(symbol, mode, websocket)
        
        await websocket.send(json.dumps({
            "type": "subscribed",
            "symbols": symbols,
            "mode": mode,
            "count": len(symbols)
        }))
        
        logger.info(f"Client subscribed to {len(symbols)} symbols in {mode} mode")
    
    async def handle_unsubscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """Unsubscribe client from symbols"""
        if websocket not in self.authenticated_clients:
            await self.send_error(websocket, "Not authenticated")
            return
        
        symbols = data.get("symbols", [])
        
        # Remove subscriptions
        for symbol in symbols:
            self.subscription_manager.remove_subscription(symbol, websocket)
        
        await websocket.send(json.dumps({
            "type": "unsubscribed",
            "symbols": symbols
        }))
        
        logger.info(f"Client unsubscribed from {len(symbols)} symbols")
    
    async def handle_ping(self, websocket: WebSocketServerProtocol):
        """Handle ping (keepalive)"""
        await websocket.send(json.dumps({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    async def send_error(self, websocket: WebSocketServerProtocol, error: str):
        """Send error message to client"""
        await websocket.send(json.dumps({
            "type": "error",
            "error": error
        }))
    
    async def cleanup_client(self, websocket: WebSocketServerProtocol):
        """Clean up client on disconnect"""
        # Remove from authenticated clients
        if websocket in self.authenticated_clients:
            user_id = self.authenticated_clients.pop(websocket)
            logger.info(f"Removed authenticated client: user_id={user_id}")
        
        # Remove all subscriptions
        self.subscription_manager.remove_all_subscriptions(websocket)
    
    async def broadcast_tick(self, symbol: str, data: Dict):
        """Broadcast market tick to subscribed clients"""
        # Get all clients subscribed to this symbol
        clients = self.subscription_manager.get_subscribers(symbol)
        
        if not clients:
            return
        
        # Prepare message
        message = json.dumps({
            "type": "tick",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send to all subscribed clients
        disconnected = []
        for client in clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            await self.cleanup_client(client)


async def main():
    """Main entry point"""
    server = WebSocketServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
