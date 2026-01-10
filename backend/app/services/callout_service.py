import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import statistics

from app.core.trade_intent import TradeIntent
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class CalloutService:
    """
    Predictive Alerting Service.
    Monitors TradeIntent streams for significant intra-day drifts in conviction.
    
    Logic:
    - Maintains a short-term history of conviction scores (e.g., last 5 mins).
    - Triggers "Pre-Signal" alerts if conviction rises rapidly (>15% delta).
    - Triggers "Validation Warning" if conviction drops significantly after being high.
    """
    
    # Configuration
    HISTORY_WINDOW_SECONDS = 300  # 5 minutes
    DRIFT_THRESHOLD_POSITIVE = 15.0  # +15 points
    DRIFT_THRESHOLD_NEGATIVE = -15.0 # -15 points
    MIN_SCORE_FOR_DRIFT = 30.0    # Ignore drift if score is very low
    
    def __init__(self, alert_service: AlertService):
        self.alert_service = alert_service
        # Store history as: {symbol: deque([(timestamp, score), ...])}
        self.history: Dict[str, deque] = {}
        
    async def process_intent(self, intent: TradeIntent):
        """
        Process a new TradeIntent and check for drift.
        """
        symbol = intent.symbol
        current_score = intent.conviction_score
        now = datetime.now()
        
        # 1. Initialize history for symbol if needed
        if symbol not in self.history:
            self.history[symbol] = deque()
            
        # 2. Add current data point
        self.history[symbol].append((now, current_score))
        
        # 3. Prune old history
        self._prune_history(symbol, now)
        
        # 4. Check for Drift
        await self._check_drift(symbol, current_score, intent)
        
    def _prune_history(self, symbol: str, now: datetime):
        """Remove entries older than the window."""
        cutoff = now - timedelta(seconds=self.HISTORY_WINDOW_SECONDS)
        history = self.history[symbol]
        
        while history and history[0][0] < cutoff:
            history.popleft()
            
    async def _check_drift(self, symbol: str, current_score: float, intent: TradeIntent):
        """
        Compare current score vs average/start of window.
        """
        history = self.history[symbol]
        if not history or len(history) < 2:
            return
            
        # Compare against the oldest point in our current window (start of the 5 mins)
        start_time, start_score = history[0]
        
        delta = current_score - start_score
        
        # Ignore noise at low levels
        if current_score < self.MIN_SCORE_FOR_DRIFT and start_score < self.MIN_SCORE_FOR_DRIFT:
            return

        # Positive Drift (Acceleration)
        if delta >= self.DRIFT_THRESHOLD_POSITIVE:
            await self.alert_service.emit(
                alert_type="CALLOUT_ACCELERATION",
                message=f"🚀 {symbol} conviction surging! +{delta:.1f} pts in last 5m (Current: {current_score:.1f})",
                level="INFO",
                symbol=symbol,
                metadata={
                    "delta": delta,
                    "start_score": start_score,
                    "current_score": current_score,
                    "bias": intent.directional_bias.value
                },
                intent=intent
            )
            # Reset history to prevent spamming the same drift multiple times? 
            # Ideally we'd have a cool-down, but for now let AlertService throttle.

        # Negative Drift (Deterioration)
        elif delta <= self.DRIFT_THRESHOLD_NEGATIVE:
             await self.alert_service.emit(
                alert_type="CALLOUT_DETERIORATION",
                message=f"⚠️ {symbol} conviction dropping fast. {delta:.1f} pts in last 5m (Current: {current_score:.1f})",
                level="WARNING",
                symbol=symbol,
                metadata={
                    "delta": delta,
                    "start_score": start_score,
                    "current_score": current_score
                },
                intent=intent
            )
