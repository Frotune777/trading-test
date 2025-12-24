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
        
        # Candle Awareness Tracking
        last_candle_minute = {} # track_key -> minute_timestamp
        
        while True:
            # 1. Maintain lock
            await redis_client.expire(lock_key, 60)
            
            # 2. Candle Awareness Logic
            now = time.time()
            current_minute_ts = int(now // 60) * 60
            
            for symbol in list(openalgo_client.subscribed_symbols):
                track_key = symbol if ":" in symbol else f"NSE:{symbol}"
                
                if track_key not in last_candle_minute:
                    last_candle_minute[track_key] = current_minute_ts
                    continue
                
                if current_minute_ts > last_candle_minute[track_key]:
                    # Candle Closed!
                    closed_minute = last_candle_minute[track_key]
                    last_candle_minute[track_key] = current_minute_ts
                    
                    # Update Redis
                    exchange = track_key.split(":")[0] if ":" in track_key else "NSE"
                    clean_symbol = track_key.split(":")[1] if ":" in track_key else track_key
                    redis_key = f"market:candle_close:{exchange}:{clean_symbol}:1m"
                    
                    event = {
                        "symbol": track_key,
                        "timestamp": closed_minute,
                        "source": "openalgo_ws",
                        "closed_at": now
                    }
                    
                    await redis_client.set(redis_key, json.dumps(event), ex=3600)
                    await redis_client.publish("candle_events", json.dumps(event))
                    
                    await alerts.emit(
                        alert_type="CANDLE_CLOSE",
                        message=f"1-minute candle closed for {track_key} at {datetime.fromtimestamp(closed_minute).strftime('%H:%M')}",
                        level="INFO",
                        symbol=track_key,
                        metadata=event
                    )
                    
                    logger.info(f"CANDLE_CLOSE: {track_key} at {datetime.fromtimestamp(closed_minute).strftime('%H:%M')}")
                    
                    # 3. Periodic Consistency Check (e.g., every 5 candles)
                    if (current_minute_ts // 60) % 5 == 0:
                        clean_sym = track_key.split(":")[1] if ":" in track_key else track_key
                        asyncio.create_task(consistency.detect_ohlc_gaps(clean_sym))
                        asyncio.create_task(consistency.validate_data_integrity(clean_sym))
            
            await asyncio.sleep(5) # Check every 5s
            
            if worker_task.done():
                logger.error("Worker task finished unexpectedly. Restarting...")
                worker_task = asyncio.create_task(openalgo_client.connect())
                
    except asyncio.CancelledError:
        logger.info("Realtime worker shutting down...")
        openalgo_client.stop()
        await redis_client.delete(lock_key)
    except Exception as e:
        logger.error(f"Unexpected error in Realtime Worker: {e}")
        await redis_client.delete(lock_key)

if __name__ == "__main__":
    asyncio.run(realtime_worker())
