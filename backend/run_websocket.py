#!/usr/bin/env python3
"""
WebSocket Server Launcher
Starts the WebSocket server for real-time market data streaming
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.websocket.websocket_server import WebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Fortune Trading QUAD - WebSocket Server")
    logger.info("=" * 60)
    
    # Create and start server
    server = WebSocketServer(host="0.0.0.0", port=8765)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down WebSocket server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
