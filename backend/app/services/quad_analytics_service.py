"""
QUAD Analytics Service
Manages QUAD decision history, drift analysis, and performance tracking
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, text
from sqlalchemy.orm import selectinload

from app.database.models_quad import (
    QUADDecision, QUADPrediction, QUADPillarCorrelation, QUADSignalAccuracy,
    QUADDecisionCreate, QUADDecisionResponse, ConvictionTimeline, ConvictionTimelinePoint,
    PillarDrift, PillarDriftAnalysis, CorrelationMatrix, CorrelationPair,
    SignalAccuracyMetrics, PillarScores
)
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

# 🔒 ARCHITECTURAL GUARDRAILS
# This is a READ-ONLY analytics service.
# It must NEVER trigger analysis, fetch market data, or recompute pillars.
#
# Forbidden imports (will cause runtime error):
_FORBIDDEN_IMPORTS = [
    'ReasoningService',
    'ReasoningEngine', 
    'LiveDecisionSnapshot',
    'SessionContext',
    'OpenAlgoAdapter',
    'BrokerService'
]

for forbidden in _FORBIDDEN_IMPORTS:
    if forbidden in dir():
        raise ImportError(
            f"🚫 ARCHITECTURAL VIOLATION: {forbidden} imported in analytics service. "
            f"Analytics APIs are READ-ONLY. Analysis logic belongs in QUADAnalysisEngine only."
        )


class QUADAnalyticsService:
    """Service for QUAD analytics and decision tracking"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def store_decision(
        self,
        decision_data: QUADDecisionCreate
    ) -> QUADDecisionResponse:
        """
        Store a QUAD decision in the database (UPSERT by symbol and minute)
        """
        try:
            # Floor timestamp to minutes for consistent uniqueness
            # Use provided stock timestamp if available, otherwise fallback to UTC now
            base_timestamp = decision_data.timestamp or datetime.utcnow()
            floored_timestamp = base_timestamp.replace(second=0, microsecond=0)
            
            # Check for existing decision for the same symbol and minute
            stmt = select(QUADDecision).where(
                and_(
                    QUADDecision.symbol == decision_data.symbol,
                    QUADDecision.timestamp == floored_timestamp
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing record (UPSERT)
                existing.conviction = decision_data.conviction
                existing.signal = decision_data.signal.value
                existing.trend_score = decision_data.pillars.trend
                existing.momentum_score = decision_data.pillars.momentum
                existing.volatility_score = decision_data.pillars.volatility
                existing.liquidity_score = decision_data.pillars.liquidity
                existing.sentiment_score = decision_data.pillars.sentiment
                existing.regime_score = decision_data.pillars.regime
                existing.reasoning_summary = decision_data.reasoning_summary
                existing.current_price = decision_data.current_price
                existing.volume = decision_data.volume
                existing.meta_data = decision_data.meta_data
                
                decision = existing
                logger.info(f"Updated QUAD decision for {decision_data.symbol} at {floored_timestamp}")
            else:
                # Create new decision record
                decision = QUADDecision(
                    symbol=decision_data.symbol,
                    timestamp=floored_timestamp,
                    conviction=decision_data.conviction,
                    signal=decision_data.signal.value,
                    trend_score=decision_data.pillars.trend,
                    momentum_score=decision_data.pillars.momentum,
                    volatility_score=decision_data.pillars.volatility,
                    liquidity_score=decision_data.pillars.liquidity,
                    sentiment_score=decision_data.pillars.sentiment,
                    regime_score=decision_data.pillars.regime,
                    reasoning_summary=decision_data.reasoning_summary,
                    current_price=decision_data.current_price,
                    volume=decision_data.volume,
                    meta_data=decision_data.meta_data
                )
                self.db.add(decision)
                logger.info(f"Created new QUAD decision for {decision_data.symbol} at {floored_timestamp}")
            
            await self.db.commit()
            await self.db.refresh(decision)
            
            # Log decision storage
            logger.info(
                f"Stored QUAD decision for {decision_data.symbol}: "
                f"{decision_data.signal.value} (conviction: {decision_data.conviction})"
            )
            
            return QUADDecisionResponse(
                id=decision.id,
                symbol=decision.symbol,
                timestamp=decision.timestamp,
                conviction=decision.conviction,
                signal=decision.signal,
                pillars=PillarScores(
                    trend=decision.trend_score,
                    momentum=decision.momentum_score,
                    volatility=decision.volatility_score,
                    liquidity=decision.liquidity_score,
                    sentiment=decision.sentiment_score,
                    regime=decision.regime_score
                ),
                reasoning_summary=decision.reasoning_summary,
                current_price=float(decision.current_price) if decision.current_price else None,
                volume=decision.volume,
                created_at=decision.created_at
            )
            
        except Exception as e:
            logger.error(f"Error storing QUAD decision: {e}")
            await self.db.rollback()
            raise
    
    async def get_conviction_timeline(
        self,
        symbol: str,
        days: int = 30
    ) -> ConvictionTimeline:
        """
        Get conviction timeline for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            Conviction timeline with historical data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query historical decisions
            stmt = select(QUADDecision).where(
                and_(
                    QUADDecision.symbol == symbol,
                    QUADDecision.timestamp >= cutoff_date
                )
            ).order_by(QUADDecision.timestamp.asc())
            
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
            
            if not decisions:
                return ConvictionTimeline(
                    symbol=symbol,
                    historical=[],
                    predicted=None,
                    volatility=None
                )
            
            # Build timeline points
            historical = [
                ConvictionTimelinePoint(
                    timestamp=d.timestamp,
                    conviction=d.conviction,
                    signal=d.signal,
                    regime=d.meta_data.get('market_regime') if d.meta_data else None,
                    pillar_scores={
                        'trend': d.trend_score,
                        'momentum': d.momentum_score,
                        'volatility': d.volatility_score,
                        'liquidity': d.liquidity_score,
                        'sentiment': d.sentiment_score,
                        'regime': d.regime_score
                    }
                )
                for d in decisions
            ]
            
            # Calculate volatility
            convictions = [d.conviction for d in decisions]
            volatility = float(np.std(convictions)) if len(convictions) > 1 else 0.0
            
            return ConvictionTimeline(
                symbol=symbol,
                historical=historical,
                predicted=None,  # Will be filled by ML service
                volatility=volatility
            )
            
        except Exception as e:
            logger.error(f"Error getting conviction timeline: {e}")
            raise
    
    async def calculate_pillar_drift(
        self,
        symbol: str,
        current_pillars: PillarScores
    ) -> Optional[PillarDriftAnalysis]:
        """
        Calculate pillar drift from previous analysis
        
        Args:
            symbol: Stock symbol
            current_pillars: Current pillar scores
            
        Returns:
            Pillar drift analysis or None if no previous data
        """
        try:
            # Get most recent previous decision
            stmt = select(QUADDecision).where(
                QUADDecision.symbol == symbol
            ).order_by(desc(QUADDecision.timestamp)).limit(1)
            
            result = await self.db.execute(stmt)
            previous = result.scalar_one_or_none()
            
            if not previous:
                return None
            
            # Calculate drifts for each pillar
            pillars = [
                ("trend", previous.trend_score, current_pillars.trend),
                ("momentum", previous.momentum_score, current_pillars.momentum),
                ("volatility", previous.volatility_score, current_pillars.volatility),
                ("liquidity", previous.liquidity_score, current_pillars.liquidity),
                ("sentiment", previous.sentiment_score, current_pillars.sentiment),
                ("regime", previous.regime_score, current_pillars.regime)
            ]
            
            drifts = []
            total_drift = 0
            
            for pillar_name, prev_score, curr_score in pillars:
                delta = curr_score - prev_score
                percent_change = (delta / prev_score * 100) if prev_score > 0 else 0
                
                # Determine bias
                prev_bias = self._get_bias(prev_score)
                curr_bias = self._get_bias(curr_score)
                
                # Check if significant (>15 point change)
                significant = abs(delta) > 15
                
                drifts.append(PillarDrift(
                    pillar=pillar_name,
                    previous_score=prev_score,
                    current_score=curr_score,
                    delta=delta,
                    percent_change=percent_change,
                    previous_bias=prev_bias,
                    current_bias=curr_bias,
                    significant=significant
                ))
                
                total_drift += abs(delta)
            
            return PillarDriftAnalysis(
                symbol=symbol,
                current_timestamp=datetime.utcnow(),
                previous_timestamp=previous.timestamp,
                drifts=drifts,
                total_drift=total_drift
            )
            
        except Exception as e:
            logger.error(f"Error calculating pillar drift: {e}")
            raise
    
    def _get_bias(self, score: int) -> str:
        """Get bias label from score"""
        if score >= 70:
            return "BULLISH"
        elif score >= 40:
            return "NEUTRAL"
        else:
            return "BEARISH"
    
    async def get_decision_history(
        self,
        symbol: str,
        limit: int = 50,
        signal_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[QUADDecisionResponse]:
        """
        Get decision history for a symbol
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records
            signal_filter: Filter by signal type
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of historical decisions
        """
        try:
            conditions = [QUADDecision.symbol == symbol]
            
            if signal_filter:
                conditions.append(QUADDecision.signal == signal_filter)
            if start_date:
                conditions.append(QUADDecision.timestamp >= start_date)
            if end_date:
                conditions.append(QUADDecision.timestamp <= end_date)
            
            stmt = select(QUADDecision).where(
                and_(*conditions)
            ).order_by(desc(QUADDecision.timestamp)).limit(limit)
            
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
            
            return [
                QUADDecisionResponse(
                    id=d.id,
                    symbol=d.symbol,
                    timestamp=d.timestamp,
                    conviction=d.conviction,
                    signal=d.signal,
                    pillars=PillarScores(
                        trend=d.trend_score,
                        momentum=d.momentum_score,
                        volatility=d.volatility_score,
                        liquidity=d.liquidity_score,
                        sentiment=d.sentiment_score,
                        regime=d.regime_score
                    ),
                    reasoning_summary=d.reasoning_summary,
                    current_price=float(d.current_price) if d.current_price else None,
                    volume=d.volume,
                    created_at=d.created_at
                )
                for d in decisions
            ]
            
        except Exception as e:
            logger.error(f"Error getting decision history: {e}")
            raise
    
    async def calculate_pillar_correlations(
        self,
        symbol: str,
        days: int = 90
    ) -> Optional[CorrelationMatrix]:
        """
        Calculate correlations between pillars
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            Correlation matrix or None if insufficient data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get historical decisions
            stmt = select(QUADDecision).where(
                and_(
                    QUADDecision.symbol == symbol,
                    QUADDecision.timestamp >= cutoff_date
                )
            ).order_by(QUADDecision.timestamp.asc())
            
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
            
            if len(decisions) < 10:  # Need at least 10 data points
                return None
            
            # Extract pillar scores
            pillars_data = {
                'trend': [d.trend_score for d in decisions],
                'momentum': [d.momentum_score for d in decisions],
                'volatility': [d.volatility_score for d in decisions],
                'liquidity': [d.liquidity_score for d in decisions],
                'sentiment': [d.sentiment_score for d in decisions],
                'regime': [d.regime_score for d in decisions]
            }
            
            # Calculate correlations
            pillar_names = list(pillars_data.keys())
            correlations = []
            
            for i, pillar1 in enumerate(pillar_names):
                for j, pillar2 in enumerate(pillar_names):
                    if i < j:  # Only upper triangle
                        corr, p_value = stats.pearsonr(
                            pillars_data[pillar1],
                            pillars_data[pillar2]
                        )
                        
                        # Determine significance
                        if abs(corr) > 0.7:
                            significance = "strong"
                        elif abs(corr) > 0.4:
                            significance = "moderate"
                        else:
                            significance = "weak"
                        
                        correlations.append(CorrelationPair(
                            pillar1=pillar1,
                            pillar2=pillar2,
                            correlation=float(corr),
                            p_value=float(p_value),
                            significance=significance
                        ))
            
            # Store in database
            for corr in correlations:
                db_corr = QUADPillarCorrelation(
                    symbol=symbol,
                    pillar1=corr.pillar1,
                    pillar2=corr.pillar2,
                    correlation=corr.correlation,
                    p_value=corr.p_value,
                    sample_size=len(decisions),
                    days_analyzed=days
                )
                self.db.add(db_corr)
            
            await self.db.commit()
            
            return CorrelationMatrix(
                symbol=symbol,
                calculated_at=datetime.utcnow(),
                correlations=correlations,
                sample_size=len(decisions),
                days_analyzed=days
            )
            
        except Exception as e:
            logger.error(f"Error calculating pillar correlations: {e}")
            raise
    
    async def get_signal_accuracy(
        self,
        symbol: str,
        days: int = 90
    ) -> SignalAccuracyMetrics:
        """
        Calculate signal accuracy metrics
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            Signal accuracy metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query accuracy records
            stmt = select(QUADSignalAccuracy).where(
                and_(
                    QUADSignalAccuracy.symbol == symbol,
                    QUADSignalAccuracy.signal_date >= cutoff_date,
                    QUADSignalAccuracy.correct.isnot(None)  # Only evaluated signals
                )
            )
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            if not records:
                return SignalAccuracyMetrics(
                    symbol=symbol,
                    total_signals=0,
                    correct_signals=0,
                    win_rate=0.0,
                    avg_conviction_winning=0.0,
                    avg_conviction_losing=0.0,
                    total_profit_loss=0.0,
                    best_signal=None,
                    worst_signal=None
                )
            
            # Calculate metrics
            total_signals = len(records)
            correct_signals = sum(1 for r in records if r.correct)
            win_rate = (correct_signals / total_signals * 100) if total_signals > 0 else 0.0
            
            winning_records = [r for r in records if r.correct]
            losing_records = [r for r in records if not r.correct]
            
            avg_conviction_winning = (
                sum(r.conviction for r in winning_records) / len(winning_records)
                if winning_records else 0.0
            )
            avg_conviction_losing = (
                sum(r.conviction for r in losing_records) / len(losing_records)
                if losing_records else 0.0
            )
            
            total_profit_loss = sum(float(r.profit_loss) for r in records if r.profit_loss)
            
            # Find best and worst signals
            best_signal = max(records, key=lambda r: float(r.profit_loss) if r.profit_loss else 0)
            worst_signal = min(records, key=lambda r: float(r.profit_loss) if r.profit_loss else 0)
            
            # Calculate rolling win rates
            last_7d = cutoff_date + timedelta(days=days-7)
            last_30d = cutoff_date + timedelta(days=days-30)
            
            signals_7d = [r for r in records if r.signal_date >= last_7d]
            signals_30d = [r for r in records if r.signal_date >= last_30d]
            
            win_rate_7d = (sum(1 for r in signals_7d if r.correct) / len(signals_7d) * 100) if signals_7d else 0.0
            win_rate_30d = (sum(1 for r in signals_30d if r.correct) / len(signals_30d) * 100) if signals_30d else 0.0

            return SignalAccuracyMetrics(
                symbol=symbol,
                total_signals=total_signals,
                correct_signals=correct_signals,
                win_rate=win_rate,
                rolling_win_rates={
                    "7d": win_rate_7d,
                    "30d": win_rate_30d,
                    "90d": win_rate
                },
                avg_conviction_winning=avg_conviction_winning,
                avg_conviction_losing=avg_conviction_losing,
                total_profit_loss=total_profit_loss,
                best_signal={
                    "date": best_signal.signal_date.isoformat(),
                    "signal": best_signal.signal,
                    "conviction": best_signal.conviction,
                    "profit_loss": float(best_signal.profit_loss) if best_signal.profit_loss else 0
                },
                worst_signal={
                    "date": worst_signal.signal_date.isoformat(),
                    "signal": worst_signal.signal,
                    "conviction": worst_signal.conviction,
                    "profit_loss": float(worst_signal.profit_loss) if worst_signal.profit_loss else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating signal accuracy: {e}")
            raise


    async def evaluate_decisions(
        self,
        symbol: str,
        evaluation_window_days: int = 5
    ) -> Dict[str, int]:
        """
        Evaluate accuracy of historical decisions
        
        Compare decision price with price after evaluation_window_days
        """
        try:
            # 1. Get decisions that haven't been evaluated yet
            # and are old enough for evaluation
            cutoff_date = datetime.utcnow() - timedelta(days=evaluation_window_days)
            
            # Subquery to find already evaluated decision IDs
            evaluated_stmt = select(QUADSignalAccuracy.decision_id)
            evaluated_ids = (await self.db.execute(evaluated_stmt)).scalars().all()
            
            stmt = select(QUADDecision).where(
                and_(
                    QUADDecision.symbol == symbol,
                    QUADDecision.timestamp <= cutoff_date,
                    QUADDecision.id.notin_(evaluated_ids) if evaluated_ids else True
                )
            )
            
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
            
            if not decisions:
                return {"evaluated": 0, "correct": 0, "skipped": 0}
            
            evaluated_count = 0
            correct_count = 0
            
            for decision in decisions:
                # Find price after 'evaluation_window_days'
                target_date = decision.timestamp + timedelta(days=evaluation_window_days)
                
                # Fetch price from price_history closest to target_date
                # Using a 3-day buffer for weekends
                price_stmt = text("""
                    SELECT close, date
                    FROM price_history
                    WHERE symbol = :symbol 
                    AND date >= :target_date
                    ORDER BY date ASC
                    LIMIT 1
                """)
                
                target_date_val = target_date.date() if hasattr(target_date, 'date') else target_date
                
                price_result = await self.db.execute(
                    price_stmt, 
                    {"symbol": symbol, "target_date": target_date_val}
                )
                future_row = price_result.fetchone()
                
                if not future_row:
                    logger.warning(f"No future price data for {symbol} at {target_date}")
                    continue
                
                future_price = float(future_row[0])
                start_price = float(decision.current_price)
                
                price_change = ((future_price - start_price) / start_price) * 100
                
                # Determine if signal was correct
                # BUY: profit > 0
                # SELL: profit < 0
                correct = False
                if decision.signal == "BUY" and price_change > 0:
                    correct = True
                elif decision.signal == "SELL" and price_change < 0:
                    correct = True
                elif decision.signal == "HOLD":
                    # For HOLD, maybe neutral price action? 
                    # Let's say HOLD is correct if abs(change) < 1%
                    correct = abs(price_change) < 1.0
                
                # Calculate P&L (absolute)
                # Assuming 1 share for simplicity
                pnl = future_price - start_price if decision.signal == "BUY" else start_price - future_price
                if decision.signal == "HOLD": pnl = 0
                
                # Create accuracy record
                accuracy = QUADSignalAccuracy(
                    symbol=symbol,
                    decision_id=decision.id,
                    signal=decision.signal,
                    conviction=decision.conviction,
                    signal_date=decision.timestamp,
                    evaluation_date=future_row[1],
                    price_at_signal=decision.current_price,
                    price_at_evaluation=future_price,
                    price_change_percent=price_change,
                    correct=correct,
                    profit_loss=pnl
                )
                
                self.db.add(accuracy)
                evaluated_count += 1
                if correct:
                    correct_count += 1
            
            await self.db.commit()
            return {
                "evaluated": evaluated_count,
                "correct": correct_count,
                "win_rate": (correct_count / evaluated_count * 100) if evaluated_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error evaluating decisions for {symbol}: {e}")
            await self.db.rollback()
            raise


# Global instance (will be initialized with DB session)
quad_analytics_service: Optional[QUADAnalyticsService] = None
