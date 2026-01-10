import asyncio
import traceback
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from collections import deque
from app.services.callout_service import CalloutService
from app.services.alert_service import AlertService
from app.core.trade_intent import TradeIntent, DirectionalBias, AnalysisQuality

def create_intent(symbol="RELIANCE", score=50.0):
    return TradeIntent(
        symbol=symbol,
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=score,
        is_execution_ready=False,
        is_analysis_valid=True,
        pillar_contributions=[],
        reasoning_narrative="Test",
        quality=AnalysisQuality(
            total_pillars=6, 
            active_pillars=6, 
            placeholder_pillars=0, 
            failed_pillars=[],
            data_age_seconds=0
        )
    )

async def debug_test():
    try:
        mock_alert = AsyncMock(spec=AlertService)
        service = CalloutService(mock_alert)
        
        symbol = "RELIANCE"
        old_time = datetime.now() - timedelta(minutes=5)
        service.history[symbol] = deque([(old_time, 40.0)])
        
        intent = create_intent(symbol, score=60.0)
        
        await service.process_intent(intent)
        
        if mock_alert.emit.call_count == 0:
            print("Emit NOT called!")
        else:
            print("Emit called:")
            print(mock_alert.emit.call_args)
            args, kwargs = mock_alert.emit.call_args
            print("Kwargs:", kwargs.keys())
            
        mock_alert.emit.assert_called_once()
        print("Assert called once passed.")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_test())
