import logging
from typing import Dict, Optional, List
from datetime import datetime
from ..core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ..core.trade_intent import TradeIntent, DirectionalBias, PillarContribution, AnalysisQuality
from .pillars.base_pillar import BasePillar

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    Unified decision engine for the QUAD system.
    Stateless, deterministic, and execution-agnostic.
    
    Output Contract: TradeIntent v1.0.0
    """
    
    # Maximum allowed placeholder pillars before blocking execution readiness
    MAX_PLACEHOLDER_THRESHOLD = 2
    
    # Minimum conviction score for valid analysis
    MIN_VALID_CONVICTION = 20.0
    
    def __init__(self):
        # Pillar weights (from Decision Matrix)
        self.weights = {
            'trend': 0.30,
            'momentum': 0.20,
            'volatility': 0.10,
            'liquidity': 0.10,
            'sentiment': 0.10,
            'regime': 0.20
        }
        
        # Track which pillars are placeholders (NONE - all implemented as of v1.0)
        self.placeholder_pillars = set()  # All 6 pillars now have real logic
        
        # Pillars will be injected later
        self.pillars: Dict[str, BasePillar] = {}
    
    def register_pillar(self, name: str, pillar: BasePillar):
        """Register a QUAD pillar."""
        if name not in self.weights:
            raise ValueError(f"Unknown pillar: {name}")
        self.pillars[name] = pillar
        logger.info(f"Registered pillar: {name}")
    
    def analyze(
        self, 
        snapshot: LiveDecisionSnapshot, 
        context: SessionContext
    ) -> TradeIntent:
        """
        Main reasoning function.
        
        Args:
            snapshot: Current instrument state
            context: Market-wide state
            
        Returns:
            TradeIntent v1.0 with quality metadata
        """
        analysis_timestamp = datetime.now()
        
        if not self.pillars:
            logger.warning("No pillars registered, returning INVALID analysis")
            return self._create_invalid_intent(
                snapshot.symbol,
                analysis_timestamp,
                "No analysis pillars available"
            )
        
        # Step 1: Collect pillar scores
        scores = {}
        biases = {}
        failed_pillars = []
        pillar_contributions = []
        
        for pillar_name, pillar in self.pillars.items():
            try:
                score, bias, metrics = pillar.analyze(snapshot, context)
                scores[pillar_name] = score
                biases[pillar_name] = bias
                
                # Create contribution record
                pillar_contributions.append(PillarContribution(
                    name=pillar_name,
                    score=score,
                    bias=bias,
                    is_placeholder=(pillar_name in self.placeholder_pillars),
                    weight_applied=self.weights[pillar_name],
                    metrics=metrics
                ))
                
                logger.debug(f"{pillar_name}: score={score}, bias={bias}")
            except Exception as e:
                logger.error(f"Pillar {pillar_name} failed: {e}")
                scores[pillar_name] = 50.0  # Neutral fallback
                biases[pillar_name] = "NEUTRAL"
                failed_pillars.append(pillar_name)
                
                # Still record as contribution (with failure flag)
                pillar_contributions.append(PillarContribution(
                    name=pillar_name,
                    score=50.0,
                    bias="NEUTRAL",
                    is_placeholder=True,  # Failed = placeholder behavior
                    weight_applied=self.weights[pillar_name],
                    metrics={"error": str(e)}
                ))
        
        # Step 2: Build quality metadata
        data_age = None
        if snapshot.timestamp:
            data_age = int((analysis_timestamp - snapshot.timestamp).total_seconds())

        # v1.1: Populate calibration version and weights snapshot
        calibration_version = "matrix_2024_q4"  # Current calibration version
        pillar_weights_snapshot = self.weights.copy()  # Frozen snapshot of weights

        quality = AnalysisQuality(
            total_pillars=len(self.weights),
            active_pillars=len(self.pillars) - len(self.placeholder_pillars) - len(failed_pillars),
            placeholder_pillars=len(self.placeholder_pillars),
            failed_pillars=failed_pillars,
            data_age_seconds=data_age,
            # v1.1 additions
            calibration_version=calibration_version,
            pillar_weights_snapshot=pillar_weights_snapshot
        )
        
        # Step 3: Generate degradation warnings
        warnings = []
        for pillar_name in self.placeholder_pillars:
            warnings.append(f"{pillar_name.capitalize()} pillar is placeholder (returns neutral)")
        for pillar_name in failed_pillars:
            warnings.append(f"{pillar_name.capitalize()} pillar failed during analysis")
        
        # Step 4: Weighted aggregation
        conviction_score = self._aggregate_scores(scores)
        
        # Apply conviction cap if too many placeholders
        if quality.placeholder_pillars > self.MAX_PLACEHOLDER_THRESHOLD:
            max_allowed = 60.0
            if conviction_score > max_allowed:
                conviction_score = max_allowed
                warnings.append(f"Conviction capped at {max_allowed}% due to {quality.placeholder_pillars} placeholder pillars")
        
        # Step 5: Determine directional bias
        directional_bias = self._determine_bias(conviction_score, biases)
        
        # Step 6: Validate analysis
        is_valid = conviction_score >= self.MIN_VALID_CONVICTION
        is_execution_ready = (
            is_valid and 
            quality.placeholder_pillars <= self.MAX_PLACEHOLDER_THRESHOLD and
            len(failed_pillars) == 0
        )
        
        if not is_execution_ready:
            warnings.append("Analysis not execution-ready (placeholders or failures present)")
        
        # Step 7: Generate reasoning narrative
        reasoning_narrative = self._generate_narrative(
            pillar_contributions, 
            directional_bias,
            conviction_score
        )
        
        return TradeIntent(
            symbol=snapshot.symbol,
            analysis_timestamp=analysis_timestamp,
            directional_bias=directional_bias,
            conviction_score=conviction_score,
            pillar_contributions=pillar_contributions,
            reasoning_narrative=reasoning_narrative,
            quality=quality,
            is_analysis_valid=is_valid,
            is_execution_ready=is_execution_ready,
            degradation_warnings=warnings,
            contract_version="1.1.0"
        )
    
    def _aggregate_scores(self, scores: Dict[str, float]) -> float:
        """Weighted sum of pillar scores."""
        total = 0.0
        for pillar_name, score in scores.items():
            weight = self.weights.get(pillar_name, 0.0)
            total += score * weight
        return round(total, 2)
    
    def _determine_bias(
        self, 
        conviction_score: float, 
        biases: Dict[str, str]
    ) -> DirectionalBias:
        """Map conviction score and pillar biases to directional bias."""
        # Count bullish vs bearish biases
        bullish_count = sum(1 for b in biases.values() if b == "BULLISH")
        bearish_count = sum(1 for b in biases.values() if b == "BEARISH")
        
        # Strong conviction thresholds
        if conviction_score >= 65 and bullish_count > bearish_count:
            return DirectionalBias.BULLISH
        elif conviction_score <= 35 and bearish_count > bullish_count:
            return DirectionalBias.BEARISH
        else:
            return DirectionalBias.NEUTRAL
    
    def _generate_narrative(
        self, 
        contributions: List[PillarContribution],
        bias: DirectionalBias,
        conviction: float
    ) -> str:
        """Generate human-readable reasoning narrative."""
        parts = [f"Bias: {bias.value} (Conviction: {conviction:.0f}%)"]
        
        # Highlight top 3 contributors
        sorted_contribs = sorted(contributions, key=lambda x: x.score, reverse=True)
        top_3 = sorted_contribs[:3]
        
        for contrib in top_3:
            placeholder_flag = " [P]" if contrib.is_placeholder else ""
            parts.append(f"{contrib.name.capitalize()}: {contrib.score:.0f} ({contrib.bias}){placeholder_flag}")
        
        return " | ".join(parts)
    
    def _create_invalid_intent(
        self, 
        symbol: str, 
        timestamp: datetime,
        reason: str
    ) -> TradeIntent:
        """Create an INVALID TradeIntent for error cases."""
        return TradeIntent(
            symbol=symbol,
            analysis_timestamp=timestamp,
            directional_bias=DirectionalBias.INVALID,
            conviction_score=0.0,
            pillar_contributions=[],
            reasoning_narrative=f"Analysis failed: {reason}",
            quality=AnalysisQuality(
                total_pillars=6,
                active_pillars=0,
                placeholder_pillars=0,
                failed_pillars=[]
            ),
            is_analysis_valid=False,
            is_execution_ready=False,
            degradation_warnings=[reason],
            contract_version="1.0.0"
        )
