import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import json
from app.workers.realtime_worker import process_candle_close
from app.services.reasoning_service import ReasoningService
from app.services.execution_service import ExecutionService
from app.services.alert_service import AlertService
from app.services.consistency_service import DataConsistencyCheck
from app.database.models_historical import HistoricalOHLC
from app.core.trade_decision import TradeDecision
from app.core.trade_intent import TradeIntent

@pytest.mark.asyncio
async def test_full_automation_loop():
    # 1. Setup Mocks
    mock_alerts = AsyncMock(spec=AlertService)
    mock_consistency = AsyncMock(spec=DataConsistencyCheck)
    
    # Mock Reasoning Service
    # We want it to return a "BUY" signal
    mock_reasoning = MagicMock(spec=ReasoningService)
    
    
    # Mock Intent and Result
    fake_intent = MagicMock(spec=TradeIntent)
    fake_snapshot = MagicMock()
    fake_snapshot.ltp = 1005.0
    
    # We need to simulate the dictionary return from analyze_symbol
    decision_id = "DEC_TEST_123"
    fake_result = {
        "is_execution_ready": True,
        "directional_bias": "BULLISH",
        "conviction_score": 85.0,
        "trade_intent": fake_intent,
        "market_snapshot": fake_snapshot,
        "decision_id": decision_id
    }
    mock_reasoning.analyze_symbol = AsyncMock(return_value=fake_result)

    # Mock Execution Service
    mock_execution = MagicMock(spec=ExecutionService)
    mock_execution.execute_order = AsyncMock(return_value={"status": "SUCCESS", "order_id": "ORD_999"})

    # Mock TradeDecision.get
    mock_decision_obj = MagicMock(spec=TradeDecision)
    mock_decision_obj.decision_id = decision_id
    
    with patch("app.core.trade_decision.TradeDecision.get", return_value=mock_decision_obj) as mock_get_decision:
        
        # Mock Redis (for process_candle_close internal calls)
        with patch("app.workers.realtime_worker.redis_client", new_callable=AsyncMock) as mock_redis, \
             patch("app.workers.realtime_worker.SessionLocal") as mock_session_cls:
            
            # Mock DB Session
            mock_db = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_db
            
            # 2. Prepare Input Data (Candle Close Event)
            symbol = "NSE:RELIANCE"
            exchange = "NSE"
            clean_symbol = "RELIANCE"
            closed_minute = int(datetime.now(timezone.utc).timestamp())
            state = {
                "open": 1000.0,
                "high": 1010.0,
                "low": 995.0,
                "close": 1005.0,
                "minute": closed_minute
            }
            candle_volume = 5000
            
            # 3. Trigger Function (The "System Under Test")
            await process_candle_close(
                symbol=symbol,
                exchange=exchange,
                clean_symbol=clean_symbol,
                closed_minute=closed_minute,
                state=state,
                candle_volume=candle_volume,
                alerts=mock_alerts,
                consistency=mock_consistency,
                reasoning_service=mock_reasoning,
                execution_service=mock_execution
            )
            
            # 4. Verify DB Persistence (Candle Saved?)
            # ohlc_record = HistoricalOHLC(...)
            # Verify db.add was called with an HistoricalOHLC object
            assert mock_db.add.called
            args, _ = mock_db.add.call_args
            assert isinstance(args[0], HistoricalOHLC)
            assert args[0].symbol == "RELIANCE"
            assert args[0].close == 1005.0
            
            # 5. Verify Analysis Triggered
            mock_reasoning.analyze_symbol.assert_awaited_once()
            call_args = mock_reasoning.analyze_symbol.call_args
            assert call_args[0][0] == "RELIANCE"
            
            # 6. Verify Execution Triggered
            mock_execution.execute_order.assert_awaited_once()
            exec_args = mock_execution.execute_order.call_args[1]
            assert exec_args["symbol"] == "RELIANCE"
            assert exec_args["order_payload"]["action"] == "BUY"
            assert exec_args["decision"] == mock_decision_obj
            
            # 7. Verify Alerts
            # Alert for Candle Close
            # Alert for Execution (inside ExecutionService usually, but maybe process_candle logs ready?)
            # process_candle calls logger.info "Exec Ready..."
            mock_alerts.emit.assert_awaited()
            
            print("Full Automation Loop Test Passed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_automation_loop())
