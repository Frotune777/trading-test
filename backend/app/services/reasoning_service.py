"""
ReasoningService - High-level wrapper for the ReasoningEngine
Provides backwards compatibility with existing API
Updated for TradeIntent v1.0 contract
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from ..reasoning.reasoning_engine import ReasoningEngine
from ..reasoning.snapshot_builder import SnapshotBuilder
from ..reasoning.pillars.trend_pillar import TrendPillar
from ..reasoning.pillars.momentum_pillar import MomentumPillar
from ..reasoning.pillars.volatility_pillar import VolatilityPillar
from ..reasoning.pillars.liquidity_pillar import LiquidityPillar
from ..reasoning.pillars.sentiment_pillar import SentimentPillar
from ..reasoning.pillars.regime_pillar import RegimePillar

logger = logging.getLogger(__name__)

class ReasoningService:
    """
    High-level reasoning service that wraps the ReasoningEngine.
    Provides a simple API for getting trade recommendations.
    
    Output: TradeIntent v1.0.0 contract (frontend-safe)
    """
    
    def __init__(self):
        # Initialize engine
        self.engine = ReasoningEngine()
        
        # Register all pillars
        self.engine.register_pillar('trend', TrendPillar())
        self.engine.register_pillar('momentum', MomentumPillar())
        self.engine.register_pillar('volatility', VolatilityPillar())
        self.engine.register_pillar('liquidity', LiquidityPillar())
        self.engine.register_pillar('sentiment', SentimentPillar())
        self.engine.register_pillar('regime', RegimePillar())
        
        # Snapshot builder
        self.snapshot_builder = SnapshotBuilder()
        
        logger.info("ReasoningService initialized with 6 QUAD pillars")
    
    async def is_execution_safe(self, symbol: str, snapshot: Any) -> tuple[bool, Optional[str]]:
        """
        Multi-point safety gate for automated execution.
        Returns (is_safe, block_reason)
        """
        from app.core.config import settings
        from app.core.openalgo_bridge import openalgo_client, FeedState
        from app.core.redis import redis_client
        
        # 1. Global Kill Switch (Settings + Runtime Override)
        # Check Redis for a dynamic override first
        try:
            runtime_enabled = await redis_client.get("runtime:execution_enabled")
            if runtime_enabled is not None:
                is_enabled = runtime_enabled.decode() == "true"
            else:
                is_enabled = settings.EXECUTION_ENABLED
        except:
            is_enabled = settings.EXECUTION_ENABLED

        if not is_enabled:
            return False, "EXECUTION_DISABLED"

        # 2. Feed Health Check
        status = openalgo_client.get_status()
        state = status.get("feed_state")
        
        if state == FeedState.DOWN.value:
            return False, "FEED_DOWN"
        if state == FeedState.DEGRADED.value:
            return False, "FEED_DEGRADED"
        
        # 3. Redis LTP Existence & Freshness
        if snapshot.ltp_source != "redis_ws":
             return False, "NO_REALTIME_DATA"
             
        if snapshot.ltp_age_ms is None or snapshot.ltp_age_ms > 5000:
            return False, "STALE_LTP"
            
        # 4. Subscription Check
        active_symbols = status.get("active_symbols", [])
        target = symbol if ":" in symbol else f"NSE:{symbol}"
        if target not in active_symbols:
            return False, "SYMBOL_NOT_SUBSCRIBED"
            
        # 5. Mode Check (Returns specific reason if DRY_RUN)
        if settings.EXECUTION_MODE == "DRY_RUN":
            return True, "DRY_RUN_MODE"

        return True, None

    async def can_execute_trade(self, symbol: str, snapshot: Any) -> Dict[str, Any]:
        """
        Final execution safety gate.
        Returns a structured ExecutionDecision (Dict)
        """
        from app.core.config import settings
        from app.core.openalgo_bridge import openalgo_client
        
        is_safe, block_reason = await self.is_execution_safe(symbol, snapshot)
        
        # Special case: Even if safe, if we are in DRY_RUN mode, 
        # the execution service will handle the simulation but
        # we still flag the mode for audit purposes.
        
        return {
            "is_execution_ready": is_safe,
            "execution_mode": settings.EXECUTION_MODE,
            "block_reason": block_reason,
            "feed_state": openalgo_client.feed_state.value,
            "ltp_source": snapshot.ltp_source,
            "ltp_age_ms": snapshot.ltp_age_ms
        }

    async def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze a symbol and return trade recommendation.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dict with v1.0 contract fields (frontend-compatible)
        """
        try:
            # Build snapshot and context
            logger.info(f"Building snapshot for {symbol}")
            snapshot = await self.snapshot_builder.build_snapshot(symbol)
            context = await self.snapshot_builder.build_session_context()
            
            # Run reasoning engine
            logger.info(f"Running reasoning engine for {symbol}")
            intent = self.engine.analyze(snapshot, context)
            
            # Execution Safety Gate
            is_safe, block_reason = await self.is_execution_safe(symbol, snapshot)
            intent.is_execution_ready = is_safe and intent.is_execution_ready
            intent.execution_block_reason = block_reason
            
            # Convert to API response format (v1.0 contract)
            from app.core.trade_decision import TradeDecision
            decision = None
            if intent.is_execution_ready and intent.directional_bias.value in ["BULLISH", "BEARISH"]:
                decision = TradeDecision.create(
                    symbol=symbol,
                    signal=intent.directional_bias.value,
                    confidence=intent.conviction_score,
                    ltp=snapshot.ltp
                )

            return {
                'symbol': symbol,
                'analysis_timestamp': intent.analysis_timestamp.isoformat(),
                'contract_version': intent.contract_version,
                'decision_id': decision.decision_id if decision else None,
                
                # Core reasoning
                'directional_bias': intent.directional_bias.value,
                'conviction_score': intent.conviction_score,
                
                # Explainability
                'reasoning': intent.reasoning_narrative,
                'pillar_scores': {
                    contrib.name: {
                        'score': contrib.score,
                        'bias': contrib.bias.value if hasattr(contrib.bias, 'value') else str(contrib.bias),
                        'is_placeholder': contrib.is_placeholder,
                        'weight': contrib.weight_applied,
                        'metrics': contrib.metrics
                    }
                    for contrib in intent.pillar_contributions
                },
                
                # Legacy FRONTEND COMPATIBILITY (Temporary mapping until frontend uses v1.0 contract fully)
                'pillars': {
                    'quality': {
                        'score': next((p.score for p in intent.pillar_contributions if p.name == 'regime'), 50.0),
                        'reasoning': "Regime and Sentiment used as Quality proxy"
                    },
                    'undervaluation': {
                        'score': next((p.score for p in intent.pillar_contributions if p.name == 'valuation'), 50.0),
                        'reasoning': "Valuation metrics"
                    },
                    'acceleration': {
                        'score': next((p.score for p in intent.pillar_contributions if p.name == 'momentum'), 50.0),
                        'reasoning': "Momentum and Volume acceleration"
                    },
                    'directional': {
                        'score': next((p.score for p in intent.pillar_contributions if p.name == 'trend'), 50.0),
                        'reasoning': "Price trend analysis"
                    }
                },
                'bias': intent.directional_bias.value,
                'conviction': intent.conviction_score,
                
                # Quality metadata (v1.0 + v1.1)
                'quality': {
                    'total_pillars': intent.quality.total_pillars,
                    'active_pillars': intent.quality.active_pillars,
                    'placeholder_pillars': intent.quality.placeholder_pillars,
                    'failed_pillars': intent.quality.failed_pillars,
                    # v1.1 additions
                    'calibration_version': intent.quality.calibration_version,
                    'pillar_weights_snapshot': intent.quality.pillar_weights_snapshot
                },
                
                # Validity flags
                'is_valid': intent.is_analysis_valid,
                'is_execution_ready': intent.is_execution_ready,
                'execution_block_reason': intent.execution_block_reason,
                'warnings': intent.degradation_warnings,
                
                # Market context (for UI display)
                'market_context': {
                    'regime': context.market_regime,
                    'vix_level': context.vix_level
                },
                
                # Technical state (for UI display)
                'technical_state': {
                    'ltp': snapshot.ltp,
                    'sma_50': snapshot.sma_50,
                    'sma_200': snapshot.sma_200,
                    'sma_20_weekly': snapshot.sma_20_weekly,
                    'rsi': snapshot.rsi,
                    'macd': snapshot.macd,
                    'macd_signal': snapshot.macd_signal,
                    'macd_hist': snapshot.macd_hist,
                    'bb_upper': snapshot.bb_upper,
                    'bb_middle': snapshot.bb_middle,
                    'bb_lower': snapshot.bb_lower,
                    'atr_pct': snapshot.atr_pct,
                    'adosc': snapshot.adosc
                },
                
                # v1.1: Include TradeIntent object for history saving
                'trade_intent': intent
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
            return {
                'symbol': symbol,
                'directional_bias': 'INVALID',
                'conviction_score': 0.0,
                'is_valid': False,
                'is_execution_ready': False,
                'error': str(e),
                'contract_version': '1.0.0'
            }
    
    async def get_recommendation_summary(self, symbol: str) -> str:
        """
        Get a human-readable recommendation summary.
        """
        result = await self.analyze_symbol(symbol)
        
        if 'error' in result:
            return f"Unable to analyze {symbol}: {result['error']}"
        
        bias = result['directional_bias']
        conviction = result['conviction_score']
        reasoning = result['reasoning']
        ready = "✓ Execution Ready" if result['is_execution_ready'] else "⚠ NOT Execution Ready"
        
        return f"{symbol}: {bias} (Conviction: {conviction:.0f}/100) {ready} - {reasoning}"
