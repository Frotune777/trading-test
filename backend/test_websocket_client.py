"""
WebSocket Client Test
Tests WebSocket server functionality
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket connection and subscription"""
    
    print("🧪 Testing WebSocket Server")
    print("=" * 60)
    
    try:
        # Connect
        print("\n1. Connecting to ws://localhost:8765...")
        async with websockets.connect('ws://localhost:8765') as ws:
            print("✅ Connected!")
            
            # Authenticate
            print("\n2. Authenticating...")
            await ws.send(json.dumps({
                'type': 'auth',
                'api_key': 'test_api_key_123'
            }))
            
            response = await ws.recv()
            auth_data = json.loads(response)
            print(f"Response: {auth_data}")
            
            if auth_data.get('type') == 'authenticated':
                print("✅ Authenticated!")
            elif auth_data.get('type') == 'error':
                print(f"⚠️  Auth failed (expected if no user): {auth_data.get('error')}")
                print("   This is normal - create a user first")
                return
            
            # Subscribe
            print("\n3. Subscribing to symbols...")
            await ws.send(json.dumps({
                'type': 'subscribe',
                'symbols': ['NSE:RELIANCE', 'NSE:TCS'],
                'mode': 'ltp'
            }))
            
            response = await ws.recv()
            sub_data = json.loads(response)
            print(f"Response: {sub_data}")
            
            if sub_data.get('type') == 'subscribed':
                print(f"✅ Subscribed to {sub_data.get('count')} symbols!")
            
            # Receive ticks
            print("\n4. Waiting for market data ticks (5 seconds)...")
            print("   (Note: Ticks will only arrive if OpenAlgo is connected)")
            
            try:
                for i in range(5):
                    tick = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    tick_data = json.loads(tick)
                    if tick_data.get('type') == 'tick':
                        print(f"   📊 {tick_data.get('symbol')}: {tick_data.get('data', {}).get('ltp')}")
            except asyncio.TimeoutError:
                print("   ⏱️  No ticks received (OpenAlgo may not be connected)")
            
            # Ping
            print("\n5. Testing ping/pong...")
            await ws.send(json.dumps({'type': 'ping'}))
            response = await ws.recv()
            pong_data = json.loads(response)
            if pong_data.get('type') == 'pong':
                print(f"✅ Pong received: {pong_data.get('timestamp')}")
            
            print("\n" + "=" * 60)
            print("✅ WebSocket test complete!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - WebSocket server not running")
        print("\nStart the server with:")
        print("  python run_websocket.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_websocket())
