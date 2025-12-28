# WebSocket Message Format Specification

## Overview

Our WebSocket implementation uses **OpenAlgo's native message format** as the standard. This ensures compatibility with OpenAlgo SDK and reduces transformation overhead.

---

## Message Types

### 1. Authentication

**Client → Server:**
```json
{
  "type": "auth",
  "api_key": "your_api_key_here"
}
```

**Server → Client:**
```json
{
  "type": "authenticated",
  "status": "success",
  "user_id": 123,
  "username": "trader1"
}
```

---

### 2. Subscription

**Client → Server:**
```json
{
  "type": "subscribe",
  "symbols": ["NSE:RELIANCE", "NSE:TCS", "NFO:NIFTY24JAN20000CE"],
  "mode": "ltp"
}
```

**Modes:**
- `ltp` - Last Traded Price only
- `quote` - OHLC + Volume
- `full` - Complete market depth

**Server → Client:**
```json
{
  "type": "subscribed",
  "symbols": ["NSE:RELIANCE", "NSE:TCS"],
  "mode": "ltp",
  "count": 2
}
```

---

### 3. Market Data Tick (OpenAlgo Format)

**Server → Client:**

#### LTP Mode
```json
{
  "type": "tick",
  "symbol": "NSE:RELIANCE",
  "exchange": "NSE",
  "ltp": 2500.50,
  "timestamp": "2024-01-01T10:00:00+05:30"
}
```

#### Quote Mode
```json
{
  "type": "tick",
  "symbol": "NSE:RELIANCE",
  "exchange": "NSE",
  "ltp": 2500.50,
  "open": 2480.00,
  "high": 2510.00,
  "low": 2475.00,
  "close": 2495.00,
  "volume": 1000000,
  "timestamp": "2024-01-01T10:00:00+05:30"
}
```

#### Full Mode (with Market Depth)
```json
{
  "type": "tick",
  "symbol": "NSE:RELIANCE",
  "exchange": "NSE",
  "ltp": 2500.50,
  "open": 2480.00,
  "high": 2510.00,
  "low": 2475.00,
  "close": 2495.00,
  "volume": 1000000,
  "oi": 50000,
  "bid": 2500.25,
  "ask": 2500.75,
  "bid_qty": 100,
  "ask_qty": 150,
  "depth": {
    "buy": [
      {"price": 2500.25, "quantity": 100, "orders": 5},
      {"price": 2500.00, "quantity": 200, "orders": 8}
    ],
    "sell": [
      {"price": 2500.75, "quantity": 150, "orders": 6},
      {"price": 2501.00, "quantity": 250, "orders": 10}
    ]
  },
  "timestamp": "2024-01-01T10:00:00+05:30"
}
```

---

### 4. Unsubscribe

**Client → Server:**
```json
{
  "type": "unsubscribe",
  "symbols": ["NSE:RELIANCE"]
}
```

**Server → Client:**
```json
{
  "type": "unsubscribed",
  "symbols": ["NSE:RELIANCE"]
}
```

---

### 5. Error

**Server → Client:**
```json
{
  "type": "error",
  "error": "Invalid API key",
  "code": "AUTH_FAILED"
}
```

---

### 6. Ping/Pong (Keepalive)

**Client → Server:**
```json
{
  "type": "ping"
}
```

**Server → Client:**
```json
{
  "type": "pong",
  "timestamp": "2024-01-01T10:00:00+05:30"
}
```

---

## Symbol Format

All symbols follow OpenAlgo's format:

```
{EXCHANGE}:{SYMBOL}
```

**Examples:**
- `NSE:RELIANCE` - Equity
- `NSE:TCS` - Equity
- `NFO:NIFTY24JAN20000CE` - Options
- `NFO:NIFTY24JANFUT` - Futures
- `MCX:GOLD24FEBFUT` - Commodities

---

## Timestamp Format

All timestamps are in **ISO 8601 format with IST timezone**:

```
2024-01-01T10:00:00+05:30
```

This ensures:
- Compliance with institutional audit requirements
- Consistent timezone handling (IST)
- Easy parsing in all languages

---

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Symbol in `EXCHANGE:SYMBOL` format |
| `exchange` | string | Exchange code (NSE, BSE, NFO, MCX, etc.) |
| `ltp` | float | Last Traded Price |
| `open` | float | Opening price |
| `high` | float | Day's high |
| `low` | float | Day's low |
| `close` | float | Previous day's close |
| `volume` | integer | Total volume traded |
| `oi` | integer | Open Interest (F&O only) |
| `bid` | float | Best bid price |
| `ask` | float | Best ask price |
| `bid_qty` | integer | Best bid quantity |
| `ask_qty` | integer | Best ask quantity |
| `timestamp` | string | ISO 8601 timestamp with timezone |

---

## Compliance Notes

### Rule #8-9: Freshness Tracking ✅
- Every tick includes explicit `timestamp`
- Feed health monitor tracks message age
- Stale data (>5s) flagged immediately

### Rule #11: Feed Health ✅
- Circuit breaker on feed degradation
- Status exposed via `/api/v1/websocket/health`

### Rule #33-37: Audit Trail ✅
- All subscriptions logged
- Message delivery tracked
- IST timestamps for compliance

---

## Client Examples

### JavaScript/TypeScript
```typescript
const ws = new WebSocket('ws://localhost:8765');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  api_key: 'your_api_key'
}));

// Subscribe
ws.send(JSON.stringify({
  type: 'subscribe',
  symbols: ['NSE:RELIANCE', 'NSE:TCS'],
  mode: 'quote'
}));

// Handle ticks
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'tick') {
    console.log(`${data.symbol}: ${data.ltp}`);
  }
};
```

### Python
```python
import asyncio
import websockets
import json

async def subscribe():
    async with websockets.connect('ws://localhost:8765') as ws:
        # Authenticate
        await ws.send(json.dumps({
            'type': 'auth',
            'api_key': 'your_api_key'
        }))
        
        # Subscribe
        await ws.send(json.dumps({
            'type': 'subscribe',
            'symbols': ['NSE:RELIANCE'],
            'mode': 'ltp'
        }))
        
        # Receive ticks
        async for message in ws:
            data = json.loads(message)
            if data['type'] == 'tick':
                print(f"{data['symbol']}: {data['ltp']}")

asyncio.run(subscribe())
```

---

## Migration from REST API

**Before (REST polling):**
```javascript
setInterval(async () => {
  const response = await fetch('/api/v1/market/ltp?symbol=NSE:RELIANCE');
  const data = await response.json();
  updateUI(data.ltp);
}, 1000);  // Poll every second
```

**After (WebSocket streaming):**
```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'tick') {
    updateUI(data.ltp);  // Real-time updates
  }
};
```

**Benefits:**
- ✅ Lower latency (<50ms vs 1000ms)
- ✅ Reduced server load (no polling)
- ✅ Real-time updates (not delayed)
- ✅ Lower bandwidth usage
