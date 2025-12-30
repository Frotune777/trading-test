import asyncio
import logging
import json
import time
from datetime import datetime
from app.core.openalgo_bridge import openalgo_client
from app.core.redis import redis_client
from app.core.config import settings
from app.services.alert_service import AlertService
from app.services.consistency_service import DataConsistencyCheck

logger = logging.getLogger(__name__)

async def realtime_worker():
    """
    Main worker for OpenAlgo bridge.
    Enforces single-instance using Redis lock.
    """
    alerts = AlertService()
    consistency = DataConsistencyCheck()
    lock_key = "openalgo_worker_lock"
    # Acquire lock for 60s, with 10s auto-renewal in the loop
    lock = await redis_client.set(lock_key, "worker_1", ex=60, nx=True)
    
    if not lock:
        logger.warning("Another OpenAlgo worker instance is already running. Exiting.")
        return

    logger.info("OpenAlgo Realtime Worker started.")
    
    try:
        # Define initial symbols to subscribe to
        initial_symbols = ["NSE:RELIANCE", "NSE_INDEX:NIFTY 50", "NSE_INDEX:NIFTY BANK"]
        await openalgo_client.subscribe(initial_symbols)
        
        # Start connection loop
        worker_task = asyncio.create_task(openalgo_client.connect())
        
        # Candle State Tracking (Deterministic)
        # ohlc_state = { symbol: { minute, open, high, low, close, start_volume, last_volume } }
        ohlc_state = {} 
        
        while True:
            # 1. Maintain lock
            await redis_client.expire(lock_key, 60)
            
            # 2. Deterministic Candle Logic
            now = time.time()
            for symbol in list(openalgo_client.subscribed_symbols):
                exchange = symbol.split(":")[0] if ":" in symbol else "NSE"
                clean_symbol = symbol.split(":")[1] if ":" in symbol else symbol
                
                # Get latest tick from Redis
                redis_key = f"market:ltp:{exchange}:{clean_symbol}"
                tick_raw = await redis_client.get(redis_key)
                if not tick_raw:
                    continue
                
                tick = json.loads(tick_raw)
                tick_ts = tick["ts"]
                ltp = tick["ltp"]
                current_vol = tick.get("volume", 0) or 0
                
                current_minute_ts = int(tick_ts // 60) * 60
                
                if symbol not in ohlc_state:
                    ohlc_state[symbol] = {
                        "minute": current_minute_ts,
                        "open": ltp,
                        "high": ltp,
                        "low": ltp,
                        "close": ltp,
                        "start_volume": current_vol,
                        "last_volume": current_vol
                    }
                    continue
                
                state = ohlc_state[symbol]
                
                # Check for candle boundary
                if current_minute_ts > state["minute"]:
                    # Candle Closed!
                    closed_minute = state["minute"]
                    
                    # Calculate candle volume (using the last volume of the closed candle)
                    candle_volume = state["last_volume"] - state["start_volume"] if state["last_volume"] >= state["start_volume"] else 0
                    
                    event = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "timestamp": closed_minute,
                        "open": state["open"],
                        "high": state["high"],
                        "low": state["low"],
                        "close": state["close"],
                        "volume": candle_volume,
                        "source": "openalgo_ws",
                        "closed_at": now
                    }
                    
                    # 1. Persist to PostgreSQL
                    async with SessionLocal() as db:
                        try:
                            ohlc_record = HistoricalOHLC(
                                symbol=clean_symbol,
                                exchange=exchange,
                                interval="1m",
                                timestamp=datetime.fromtimestamp(closed_minute, tz=timezone.utc),
                                open=state["open"],
                                high=state["high"],
                                low=state["low"],
                                close=state["close"],
                                volume=candle_volume,
                                source="openalgo_ws"
                            )
                            db.add(ohlc_record)
                            await db.commit()
                        except Exception as db_err:
                            logger.error(f"Database error saving candle for {symbol}: {db_err}")
                    
                    # 2. Update Redis & Pub/Sub
                    redis_candle_key = f"market:candle_close:{exchange}:{clean_symbol}:1m"
                    await redis_client.set(redis_candle_key, json.dumps(event), ex=3600)
                    await redis_client.publish("candle_events", json.dumps(event))
                    
                    await alerts.emit(
                        alert_type="CANDLE_CLOSE",
                        message=f"1-minute candle closed for {symbol} at {datetime.fromtimestamp(closed_minute).strftime('%H:%M')}",
                        level="INFO",
                        symbol=symbol,
                        metadata=event
                    )
                    
                    logger.info(f"CANDLE_CLOSE: {symbol} at {datetime.fromtimestamp(closed_minute).strftime('%H:%M')} (Open: {state['open']}, Close: {state['close']})")
                    
                    # Reset state for new candle
                    ohlc_state[symbol] = {
                        "minute": current_minute_ts,
                        "open": ltp,
                        "high": ltp,
                        "low": ltp,
                        "close": ltp,
                        "start_volume": current_vol,
                        "last_volume": current_vol
                    }
                    
                    # 3. Periodic Consistency Check (e.g., every 5 candles)
                    if (current_minute_ts // 60) % 5 == 0:
                        asyncio.create_task(consistency.detect_ohlc_gaps(clean_symbol))
                        asyncio.create_task(consistency.validate_data_integrity(clean_symbol))
                else:
                    # Update current candle state
                    state["high"] = max(state["high"], ltp)
                    state["low"] = min(state["low"], ltp)
                    state["close"] = ltp
                    state["last_volume"] = current_vol
            
            await asyncio.sleep(1) # Faster poll for deterministic logic
            
            if worker_task.done():
                logger.error("Worker task finished unexpectedly. Restarting...")
                worker_task = asyncio.create_task(openalgo_client.connect())
                
    except asyncio.CancelledError:
        logger.info("Realtime worker shutting down...")
        openalgo_client.stop()
        await redis_client.delete(lock_key)
    except Exception as e:
        logger.error(f"Unexpected error in Realtime Worker: {e:.100s}")
        await redis_client.delete(lock_key)

if __name__ == "__main__":
    asyncio.run(realtime_worker())
