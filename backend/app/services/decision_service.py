"""
Decision Ledger Service
Records and manages trading decisions with causal explainability
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.database.models_decision import DecisionLedger, CausalContribution, DecisionOutcome


class DecisionService:
    def __init__(self, db: Session):
        self.db = db
    
    def record_decision(
        self,
        strategy_id: int,
        symbol: str,
        user_id: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        weights: Dict[str, float],
        risk_checks: Dict[str, str],
        causal_graph: List[Dict[str, Any]],
        mode: str = "DRY_RUN",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Record a trading decision with full causal explainability
        
        Args:
            strategy_id: ID of strategy making the decision
            symbol: Stock symbol
            user_id: User ID
            inputs: Input data (price, indicators, regime, ML prediction)
            output: Decision output (action, position_size, etc.)
            weights: Pillar weights (Q, U, A, D)
            risk_checks: Risk check results
            causal_graph: List of causal factors
            mode: DRY_RUN, LIVE, or BACKTEST
            notes: Optional notes
            tags: Optional tags
        
        Returns:
            Decision record with decision_id
        """
        # Generate unique decision ID
        decision_id = f"d-{uuid.uuid4().hex[:8]}"
        
        # Calculate total conviction from causal graph
        conviction = self._calculate_conviction(causal_graph, output)
        
        # Create decision record
        decision = DecisionLedger(
            decision_id=decision_id,
            strategy_id=strategy_id,
            symbol=symbol,
            user_id=user_id,
            mode=mode,
            final_decision=output.get('action', 'HOLD'),
            conviction=conviction,
            position_size=output.get('position_size'),
            inputs=inputs,
            weights=weights,
            risk_checks=risk_checks,
            causal_graph=causal_graph,
            output_details=output,
            notes=notes,
            tags=tags or [],
        )
        
        self.db.add(decision)
        self.db.flush()  # Get the ID
        
        # Record individual causal contributions
        for cause in causal_graph:
            contribution = CausalContribution(
                decision_id=decision_id,
                cause_type=cause.get('type', 'INDICATOR'),
                cause_name=cause['cause'],
                cause_value=cause.get('value'),
                effect_description=cause['effect'],
                effect_magnitude=cause.get('magnitude', 0),
                confidence=cause['confidence'],
                conviction_contribution=cause.get('contribution', 0),
            )
            self.db.add(contribution)
        
        self.db.commit()
        self.db.refresh(decision)
        
        return self._decision_to_dict(decision)
    
    def _calculate_conviction(
        self, 
        causal_graph: List[Dict[str, Any]], 
        output: Dict[str, Any]
    ) -> int:
        """
        Calculate overall conviction (0-100) from causal graph
        
        Uses weighted sum of causal contributions and their confidences
        """
        if not causal_graph:
            return 50  # Neutral conviction
        
        # Sum weighted contributions
        total_contribution = 0
        total_weight = 0
        
        for cause in causal_graph:
            confidence = cause.get('confidence', 0.5)
            magnitude = abs(cause.get('magnitude', 0))
            contribution = magnitude * confidence
            
            total_contribution += contribution
            total_weight += confidence
        
        # Normalize to 0-100 scale
        if total_weight > 0:
            raw_conviction = (total_contribution / total_weight) * 10  # Scale factor
            conviction = min(100, max(0, int(raw_conviction)))
        else:
            conviction = 50
        
        # Adjust based on risk checks
        risk_warnings = sum(1 for v in output.get('risk_checks', {}).values() if v == 'WARN')
        risk_failures = sum(1 for v in output.get('risk_checks', {}).values() if v == 'FAIL')
        
        conviction -= (risk_warnings * 5)
        conviction -= (risk_failures * 15)
        
        return max(0, min(100, conviction))
    
    def _decision_to_dict(self, decision: DecisionLedger) -> Dict[str, Any]:
        """Convert decision model to dictionary"""
        return {
            'decision_id': decision.decision_id,
            'timestamp': decision.timestamp.isoformat(),
            'strategy_id': decision.strategy_id,
            'symbol': decision.symbol,
            'mode': decision.mode,
            'final_decision': decision.final_decision,
            'conviction': decision.conviction,
            'inputs': decision.inputs,
            'weights': decision.weights,
            'risk_checks': decision.risk_checks,
            'causal_graph': decision.causal_graph,
            'output': decision.output_details,
            'executed': decision.executed,
            'execution_price': float(decision.execution_price) if decision.execution_price else None,
            'execution_time': decision.execution_time.isoformat() if decision.execution_time else None,
            'actual_pnl': float(decision.actual_pnl) if decision.actual_pnl else None,
            'was_correct': decision.was_correct,
            'tags': decision.tags,
        }
    
    async def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a single decision by ID"""
        decision = self.db.query(DecisionLedger).filter(
            DecisionLedger.decision_id == decision_id
        ).first()
        
        if not decision:
            return None
        
        return self._decision_to_dict(decision)
    
    async def get_decisions_by_symbol(
        self, 
        symbol: str, 
        user_id: str,
        limit: int = 50,
        mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get decision history for a symbol"""
        query = self.db.query(DecisionLedger).filter(
            and_(
                DecisionLedger.symbol == symbol,
                DecisionLedger.user_id == user_id
            )
        )
        
        if mode:
            query = query.filter(DecisionLedger.mode == mode)
        
        decisions = query.order_by(desc(DecisionLedger.timestamp)).limit(limit).all()
        
        return [self._decision_to_dict(d) for d in decisions]
    
    async def get_decisions_by_strategy(
        self,
        strategy_id: int,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get decisions made by a specific strategy"""
        decisions = self.db.query(DecisionLedger).filter(
            and_(
                DecisionLedger.strategy_id == strategy_id,
                DecisionLedger.user_id == user_id
            )
        ).order_by(desc(DecisionLedger.timestamp)).limit(limit).all()
        
        return [self._decision_to_dict(d) for d in decisions]
    
    async def update_execution(
        self,
        decision_id: str,
        execution_price: float,
        execution_status: str,
        execution_time: Optional[datetime] = None
    ) -> bool:
        """Update decision with execution results"""
        decision = self.db.query(DecisionLedger).filter(
            DecisionLedger.decision_id == decision_id
        ).first()
        
        if not decision:
            return False
        
        decision.executed = True
        decision.execution_price = Decimal(str(execution_price))
        decision.execution_status = execution_status
        decision.execution_time = execution_time or datetime.now()
        
        self.db.commit()
        return True
    
    async def update_outcome(
        self,
        decision_id: str,
        actual_pnl: float,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        was_correct: Optional[bool] = None
    ) -> bool:
        """Update decision with final outcome"""
        decision = self.db.query(DecisionLedger).filter(
            DecisionLedger.decision_id == decision_id
        ).first()
        
        if not decision:
            return False
        
        decision.actual_pnl = Decimal(str(actual_pnl))
        decision.exit_price = Decimal(str(exit_price))
        decision.exit_time = exit_time or datetime.now()
        decision.was_correct = was_correct
        
        self.db.commit()
        return True
    
    async def get_decision_timeline(
        self,
        symbol: str,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get decision timeline for visualization
        Shows evolution of decisions over time
        """
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        decisions = self.db.query(DecisionLedger).filter(
            and_(
                DecisionLedger.symbol == symbol,
                DecisionLedger.user_id == user_id,
                DecisionLedger.timestamp >= start_date
            )
        ).order_by(DecisionLedger.timestamp).all()
        
        timeline = []
        for d in decisions:
            timeline.append({
                'timestamp': d.timestamp.isoformat(),
                'decision': d.final_decision,
                'conviction': d.conviction,
                'price': d.inputs.get('price'),
                'regime': d.inputs.get('regime'),
                'executed': d.executed,
                'pnl': float(d.actual_pnl) if d.actual_pnl else None,
            })
        
        return timeline
    
    async def analyze_causal_accuracy(
        self,
        decision_id: str
    ) -> Dict[str, Any]:
        """
        Analyze which causal factors were actually important
        Requires decision to have outcome data
        """
        decision = self.db.query(DecisionLedger).filter(
            DecisionLedger.decision_id == decision_id
        ).first()
        
        if not decision or not decision.was_correct is not None:
            return {'error': 'Decision not found or outcome not available'}
        
        # Get causal contributions
        contributions = self.db.query(CausalContribution).filter(
            CausalContribution.decision_id == decision_id
        ).all()
        
        # Analyze which causes were validated by outcome
        validated_causes = []
        for contrib in contributions:
            # Simple heuristic: high confidence causes in correct decisions were valid
            was_valid = decision.was_correct and contrib.confidence > 0.7
            
            validated_causes.append({
                'cause': contrib.cause_name,
                'was_valid': was_valid,
                'confidence': contrib.confidence,
                'actual_impact': contrib.confidence if was_valid else 0.0,
            })
        
        return {
            'decision_id': decision_id,
            'was_correct': decision.was_correct,
            'validated_causes': validated_causes,
            'top_valid_causes': sorted(
                [c for c in validated_causes if c['was_valid']],
                key=lambda x: x['actual_impact'],
                reverse=True
            )[:3]
        }
