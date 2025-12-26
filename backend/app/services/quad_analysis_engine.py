"""
QUAD Analysis Engine
Orchestrates QUAD analysis, integrates with ReasoningEngine, and persists results.

ARCHITECTURAL COMPLIANCE:
- This is the ONLY component that writes to quad_decisions table
- Analysis is triggered by schedule or manual API call
- UI/Analytics APIs are strictly read-only
- No analysis logic in API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.reasoning_service import ReasoningService
from app.database.models_quad import QUADDecision
from app.core.config import settings

logger = logging.getLogger(__name__)


class QUADAnalysisEngine:
    """
    Core QUAD Analysis Engine
    
    Responsibilities:
    1. Fetch market data (via ReasoningService)
    2. Compute pillar scores (via ReasoningEngine)
    3. Calculate conviction
    4. Generate signals
    5. Persist to database
    
    This is the WRITE-HEAVY component. Analytics APIs are READ-ONLY.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize QUAD Analysis Engine
        
        Args:
            db: Database session for persistence
        """
        self.db = db
        self.reasoning_service = ReasoningService()
        logger.info("QUADAnalysisEngine initialized")
    
    async def analyze_symbol(self, symbol: str) -> QUADDecision:
        """
        Analyze a single symbol and persist results
        
        This is the main entry point for QUAD analysis.
        
        Args:
            symbol: Stock symbol to analyze (e.g., "RELIANCE")
            
        Returns:
            QUADDecision: Persisted decision record
            
        Raises:
            Exception: If analysis or persistence fails
        """
        logger.info(f"Starting QUAD analysis for {symbol}")
        
        try:
            # Step 1: Run reasoning engine (fetches data + computes pillars)
            analysis_result = await self.reasoning_service.analyze_symbol(symbol)
            
            # Step 2: Extract pillar scores
            pillar_scores = self._extract_pillar_scores(analysis_result)
            
            # Step 3: Map to QUAD decision
            decision = self._create_quad_decision(symbol, analysis_result, pillar_scores)
            
            # Step 4: Check for duplicates (same symbol + timestamp within 1 minute)
            existing = await self._check_duplicate(symbol, decision.timestamp)
            if existing:
                logger.warning(f"Duplicate decision found for {symbol} at {decision.timestamp}, skipping")
                return existing
            
            # Step 5: Persist to database
            persisted_decision = await self._persist_decision(decision)
            
            logger.info(f"QUAD analysis complete for {symbol}: conviction={persisted_decision.conviction}, signal={persisted_decision.signal}")
            return persisted_decision
            
        except Exception as e:
            logger.error(f"QUAD analysis failed for {symbol}: {e}", exc_info=True)
            raise
    
    async def analyze_watchlist(self, symbols: List[str]) -> List[QUADDecision]:
        """
        Batch analyze multiple symbols
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            List of persisted QUADDecision records
        """
        logger.info(f"Starting batch QUAD analysis for {len(symbols)} symbols")
        
        decisions = []
        for symbol in symbols:
            try:
                decision = await self.analyze_symbol(symbol)
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                # Continue with other symbols
                continue
        
        logger.info(f"Batch analysis complete: {len(decisions)}/{len(symbols)} successful")
        return decisions
    
    def _extract_pillar_scores(self, analysis_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract pillar scores from reasoning service result
        
        Args:
            analysis_result: Result from ReasoningService.analyze_symbol()
            
        Returns:
            Dict mapping pillar names to scores (0-100)
        """
        pillar_scores_raw = analysis_result.get('pillar_scores', {})
        
        # Map pillar names to QUAD schema
        pillar_mapping = {
            'trend': 'trend_score',
            'momentum': 'momentum_score',
            'volatility': 'volatility_score',
            'liquidity': 'liquidity_score',
            'sentiment': 'sentiment_score',
            'regime': 'regime_score'
        }
        
        scores = {}
        for pillar_name, score_key in pillar_mapping.items():
            pillar_data = pillar_scores_raw.get(pillar_name, {})
            score = pillar_data.get('score', 50)  # Default to neutral if missing
            
            # Ensure score is in valid range
            score = max(0, min(100, int(score)))
            scores[score_key] = score
        
        return scores
    
    def _create_quad_decision(
        self, 
        symbol: str, 
        analysis_result: Dict[str, Any],
        pillar_scores: Dict[str, int]
    ) -> QUADDecision:
        """
        Create QUADDecision object from analysis results
        
        Args:
            symbol: Stock symbol
            analysis_result: Result from ReasoningService
            pillar_scores: Extracted pillar scores
            
        Returns:
            QUADDecision object (not yet persisted)
        """
        # Extract core fields
        conviction = int(analysis_result.get('conviction_score', 0))
        directional_bias = analysis_result.get('directional_bias', 'NEUTRAL')
        
        # Map directional bias to signal
        signal_mapping = {
            'BULLISH': 'BUY',
            'BEARISH': 'SELL',
            'NEUTRAL': 'HOLD'
        }
        signal = signal_mapping.get(directional_bias, 'HOLD')
        
        # Extract technical state
        technical_state = analysis_result.get('technical_state', {})
        current_price = technical_state.get('ltp', 0.0)
        volume = technical_state.get('volume', 0)
        
        # Extract reasoning narrative
        reasoning_summary = analysis_result.get('reasoning', 'QUAD analysis completed')
        
        # Create decision object
        decision = QUADDecision(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            conviction=conviction,
            signal=signal,
            
            # Pillar scores
            trend_score=pillar_scores.get('trend_score', 50),
            momentum_score=pillar_scores.get('momentum_score', 50),
            volatility_score=pillar_scores.get('volatility_score', 50),
            liquidity_score=pillar_scores.get('liquidity_score', 50),
            sentiment_score=pillar_scores.get('sentiment_score', 50),
            regime_score=pillar_scores.get('regime_score', 50),
            
            # Additional context
            reasoning_summary=reasoning_summary[:500],  # Truncate if too long
            current_price=current_price,
            volume=volume,
            meta_data=None  # Can store additional JSON metadata if needed
        )
        
        return decision
    
    async def _check_duplicate(self, symbol: str, timestamp: datetime) -> Optional[QUADDecision]:
        """
        Check if a decision already exists for this symbol near this timestamp
        
        Args:
            symbol: Stock symbol
            timestamp: Decision timestamp
            
        Returns:
            Existing decision if found, None otherwise
        """
        from datetime import timedelta
        
        # Check for decisions within 1 minute
        time_window_start = timestamp - timedelta(minutes=1)
        time_window_end = timestamp + timedelta(minutes=1)
        
        stmt = select(QUADDecision).where(
            QUADDecision.symbol == symbol,
            QUADDecision.timestamp >= time_window_start,
            QUADDecision.timestamp <= time_window_end
        )
        
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        
        return existing
    
    async def _persist_decision(self, decision: QUADDecision) -> QUADDecision:
        """
        Persist decision to database
        
        Args:
            decision: QUADDecision object to persist
            
        Returns:
            Persisted decision with ID
        """
        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)
        
        logger.info(f"Persisted QUAD decision: id={decision.id}, symbol={decision.symbol}")
        return decision
