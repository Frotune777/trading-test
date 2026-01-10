import asyncio
import logging
import json
import time
from datetime import datetime, timezone
from app.core.openalgo_bridge import openalgo_client
from app.core.redis import redis_client
from app.core.config import settings
from app.services.alert_service import AlertService

from app.services.consistency_service import DataConsistencyCheck
from app.services.reasoning_service import ReasoningService
from app.services.execution_service import ExecutionService
from app.core.database import SessionLocal
from app.database.models_historical import HistoricalOHLC

logger = logging.getLogger(__name__)

async def realtime_worker():
    """
    Main worker for OpenAlgo bridge.
    Enforces single-instance using Redis lock.
    """
    alerts = AlertService()
    consistency = DataConsistencyCheck()
    
    # Initialize Core Services
    reasoning_service = ReasoningService()
    execution_service = ExecutionService()
    
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
                    
                    await process_candle_close(
                        symbol=symbol,
                        exchange=exchange,
                        clean_symbol=clean_symbol,
                        closed_minute=closed_minute,
                        state=state,
                        candle_volume=candle_volume,
                        alerts=alerts,
                        consistency=consistency,
                        reasoning_service=reasoning_service,
                        execution_service=execution_service
                    )
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

async def process_candle_close(
    symbol: str, 
    exchange: str, 
    clean_symbol: str, 
    closed_minute: int, 
    state: dict, 
    candle_volume: int,
    alerts: AlertService,
    consistency: DataConsistencyCheck,
    reasoning_service: ReasoningService,
    execution_service: ExecutionService
):
    """
    Handles the sequence of events after a candle close:
    1. Persist to DB/Redis
    2. Data Integrity Checks
    3. Trigger Analysis (Brain)
    4. Trigger Execution (Hand)
    """
    now = time.time()
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
    
    # 3. Trigger Analysis & Execution (The "Brain")
    try:
        # Create a fresh DB session for this analysis cycle
        async with SessionLocal() as db:
            # A. Analyze
            logger.info(f"Triggering Analysis for {symbol}")
            analysis_result = await reasoning_service.analyze_symbol(clean_symbol, db)
            
            if analysis_result.get("is_execution_ready", False):
                decision_bias = analysis_result.get("directional_bias")
                conviction = analysis_result.get("conviction_score", 0)
                intent = analysis_result.get("trade_intent")
                
                logger.info(f"Exec Ready for {symbol}: {decision_bias} ({conviction}%)")
                
                decision_id = analysis_result.get("decision_id")
                if decision_id:
                    from app.core.trade_decision import TradeDecision
                    decision_obj = TradeDecision.get(decision_id)
                    
                    if decision_obj:
                        order_action = "BUY" if decision_bias == "BULLISH" else "SELL"
                        
                        order_payload = {
                            "action": order_action,
                            "quantity": 1, 
                            "order_type": "MARKET",
                            "exchange": exchange,
                            "product": "MIS"
                        }
                        
                        logger.info(f"Executing {order_action} for {symbol}")
                        exec_result = await execution_service.execute_order(
                            symbol=clean_symbol,
                            order_payload=order_payload,
                            snapshot=analysis_result.get("market_snapshot"), 
                            db=db,
                            user_id=1, 
                            decision=decision_obj
                        )
                        logger.info(f"Execution Result: {exec_result.get('status')}")
                    else:
                        logger.error(f"Decision object not found for ID {decision_id}")
                else:
                        logger.warning(f"Execution Ready but no Decision ID for {symbol}")
            else:
                logger.debug(f"Analysis complete for {clean_symbol}: Wait ({analysis_result.get('conviction_score', 0)}%)")

    except Exception as analysis_err:
        logger.error(f"Error in Analysis/Execution Loop for {symbol}: {analysis_err}")

    # 4. Periodic Consistency Check
    if (closed_minute // 60) % 5 == 0:
        asyncio.create_task(consistency.validate_data_integrity(clean_symbol))

if __name__ == "__main__":
    asyncio.run(realtime_worker())
