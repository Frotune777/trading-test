import asyncio
import websockets
import json
import sys

async def test_websocket(uri):
    print(f"Connecting to {uri}...")
    try:
        # Simulate a browser request from localhost:3000
        async with websockets.connect(uri, extra_headers={"Origin": "http://localhost:3000"}) as websocket:
            print(f"✅ Connected to {uri} with Origin: http://localhost:3000")
            
            # Send a subscribe message (simulating frontend)
            subscribe_msg = {
                "action": "subscribe",
                "symbols": ["NSE:RELIANCE"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"Sent subscription: {subscribe_msg}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received within timeout (expected if no ticks generated yet)")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Failed to connect to {uri}: STATUS CODE {e.status_code}")
        print(f"Headers: {e.headers}")
    except Exception as e:
        print(f"❌ Failed to connect to {uri}: {type(e).__name__}: {e}")
        return False
    return True

async def main():
    base_url = "ws://localhost:8000"
    
    # Test Market WS
    print("\nTesting Market WebSocket...")
    market_uri = f"{base_url}/api/v1/ws"
    await test_websocket(market_uri)
    
    # Test Alerts WS
    print("\nTesting Alerts WebSocket...")
    alerts_uri = f"{base_url}/api/v1/ws/alerts"
    await test_websocket(alerts_uri)

if __name__ == "__main__":
    asyncio.run(main())
