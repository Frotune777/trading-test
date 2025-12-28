"""
Institutional QUAD Service

Orchestrates all 6 pillars and assembles final decision.
This is the main entry point for institutional QUAD v2 analysis.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import time

from ..database.db_manager import DatabaseManager
from ..reasoning.institutional.pillars import (
    PriceStructurePillar,
    InstitutionalFlowPillar,
    DerivativesPillar,
    RegimePillar,
    FundamentalPillar,
    ExecutionPillar
)
from ..reasoning.institutional.decision_assembler import BayesianDecisionAssembler
from ..reasoning.institutional.risk_governor import GlobalRiskGovernor
from ..reasoning.institutional import PillarOutput
from .input_builders import InputBuilderRegistry

logger = logging.getLogger(__name__)


class InstitutionalQUADService:
    """
    Orchestrates institutional QUAD v2 analysis.
    
    Responsibilities:
    1. Build input bundles for each pillar
    2. Execute all 6 pillars
    3. Assemble final decision via Bayesian aggregator
    4. Persist to quad_decisions_v2 table
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # Initialize all 6 pillars
        self.pillars = {
            'PRICE_STRUCTURE': PriceStructurePillar(),
            'INSTITUTIONAL_FLOW': InstitutionalFlowPillar(),
            'DERIVATIVES_POSITIONING': DerivativesPillar(),
            'REGIME_CONTEXT': RegimePillar(),
            'FUNDAMENTAL_THEMATIC': FundamentalPillar(),
            'EXECUTION_FEASIBILITY': ExecutionPillar()
        }
        
        # Initialize decision assembler (includes risk governor)
        self.risk_governor = GlobalRiskGovernor()
        self.decision_assembler = BayesianDecisionAssembler(self.risk_governor)
        
        # Initialize input builders
        self.input_builder_registry = InputBuilderRegistry(db_manager)
        
        logger.info("Initialized InstitutionalQUADService with 6 pillars and real input builders")
    
    async def analyze_symbol(self, symbol: str) -> Dict:
        """
        Run full institutional QUAD analysis for a symbol.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dict containing final decision with all pillar outputs
        """
        start_time = time.time()
        logger.info(f"Starting institutional QUAD analysis for {symbol}")
        
        try:
            # 1. BUILD INPUT BUNDLES
            logger.info("Building input bundles for all pillars")
            input_bundles = await self._build_input_bundles(symbol)
            
            # 2. EXECUTE ALL PILLARS
            logger.info("Executing all 6 pillars")
            pillar_outputs = self._execute_pillars(input_bundles)
            
            # 3. ASSEMBLE DECISION
            logger.info("Assembling final decision")
            decision = self.decision_assembler.assemble(pillar_outputs, symbol)
            
            # 4. ADD METADATA
            computation_time_ms = int((time.time() - start_time) * 1000)
            decision['computation_time_ms'] = computation_time_ms
            decision['symbol'] = symbol
            
            # 5. PERSIST TO DATABASE
            logger.info("Persisting decision to database")
            decision_id = await self._persist_decision(decision)
            decision['id'] = decision_id
            
            logger.info(f"QUAD analysis complete for {symbol} in {computation_time_ms}ms")
            logger.info(f"Result: {decision['primary_bias']} @ {decision['confidence']:.1f}% confidence")
            
            return decision
            
        except Exception as e:
            logger.error(f"QUAD analysis failed for {symbol}: {e}", exc_info=True)
            raise
    
    async def _build_input_bundles(self, symbol: str) -> Dict:
        """
        Build input bundles for all 6 pillars using the registry.
        
        Returns:
            Dict mapping pillar_name to input_bundle
        """
        logger.info(f"Building real input bundles for {symbol}")
        return await self.input_builder_registry.build_all(symbol)
    
    def _execute_pillars(self, input_bundles: Dict) -> list[PillarOutput]:
        """
        Execute all 6 pillars with their respective input bundles.
        
        Args:
            input_bundles: Dict mapping pillar_name to input_bundle
            
        Returns:
            List of PillarOutput objects
        """
        pillar_outputs = []
        
        for pillar_name, pillar in self.pillars.items():
            try:
                logger.info(f"Executing {pillar_name}")
                input_bundle = input_bundles[pillar_name]
                output = pillar.analyze(input_bundle)
                pillar_outputs.append(output)
                logger.info(f"{pillar_name}: {output.primary_bias.value} @ {output.confidence:.1f}% ({output.health.value})")
            except Exception as e:
                logger.error(f"Pillar {pillar_name} failed: {e}", exc_info=True)
                # Continue with other pillars - Risk Governor will handle failures
        
        return pillar_outputs
    
    async def _persist_decision(self, decision: Dict) -> int:
        """
        Persist decision to quad_decisions_v2 table.
        
        Args:
            decision: Decision dict from assembler
            
        Returns:
            Decision ID
        """
        import json
        
        # Extract pillar outputs
        pillar_outputs = decision.get('pillar_outputs', {})
        
        # Build SQL insert
        sql = """
        INSERT INTO quad_decisions_v2 (
            symbol, timestamp,
            
            -- Pillar 1
            p1_prob_strong_bullish, p1_prob_bullish, p1_prob_neutral, p1_prob_bearish, p1_prob_strong_bearish,
            p1_primary_bias, p1_confidence, p1_health, p1_health_message, p1_features, p1_version,
            
            -- Pillar 2
            p2_prob_strong_bullish, p2_prob_bullish, p2_prob_neutral, p2_prob_bearish, p2_prob_strong_bearish,
            p2_primary_bias, p2_confidence, p2_health, p2_health_message, p2_features, p2_version,
            
            -- Pillar 3
            p3_prob_strong_bullish, p3_prob_bullish, p3_prob_neutral, p3_prob_bearish, p3_prob_strong_bearish,
            p3_primary_bias, p3_confidence, p3_health, p3_health_message, p3_features, p3_version,
            
            -- Pillar 4
            p4_prob_strong_bullish, p4_prob_bullish, p4_prob_neutral, p4_prob_bearish, p4_prob_strong_bearish,
            p4_primary_bias, p4_confidence, p4_health, p4_health_message, p4_features, p4_version,
            
            -- Pillar 5
            p5_prob_strong_bullish, p5_prob_bullish, p5_prob_neutral, p5_prob_bearish, p5_prob_strong_bearish,
            p5_primary_bias, p5_confidence, p5_health, p5_health_message, p5_features, p5_version,
            
            -- Pillar 6
            p6_prob_strong_bullish, p6_prob_bullish, p6_prob_neutral, p6_prob_bearish, p6_prob_strong_bearish,
            p6_primary_bias, p6_confidence, p6_health, p6_health_message, p6_features, p6_version,
            
            -- Final decision
            final_prob_strong_bullish, final_prob_bullish, final_prob_neutral, final_prob_bearish, final_prob_strong_bearish,
            final_bias, final_confidence, base_confidence,
            
            -- Validity
            validity, blocking_reasons, is_executable, execution_risk_flags,
            
            -- Risk envelope
            max_position_size, stop_loss_pct, take_profit_pct, max_hold_days, expected_value,
            
            -- Metadata
            pillar_weights, all_risk_flags, num_healthy_pillars, num_degraded_pillars, num_failed_pillars,
            computation_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Helper to extract pillar data
        def get_pillar_data(pillar_name):
            p = pillar_outputs.get(pillar_name, {})
            return [
                p.get('prob_strong_bullish', 0.0),
                p.get('prob_bullish', 0.0),
                p.get('prob_neutral', 1.0),
                p.get('prob_bearish', 0.0),
                p.get('prob_strong_bearish', 0.0),
                p.get('primary_bias', 'NEUTRAL'),
                p.get('confidence', 0.0),
                p.get('health', 'FAILED'),
                p.get('health_message'),
                json.dumps(p.get('feature_contributions', {})),
                p.get('feature_version', '1.0.0')
            ]
        
        params = [
            decision['symbol'],
            decision['timestamp'].isoformat(),
            
            # All 6 pillars
            *get_pillar_data('PRICE_STRUCTURE'),
            *get_pillar_data('INSTITUTIONAL_FLOW'),
            *get_pillar_data('DERIVATIVES_POSITIONING'),
            *get_pillar_data('REGIME_CONTEXT'),
            *get_pillar_data('FUNDAMENTAL_THEMATIC'),
            *get_pillar_data('EXECUTION_FEASIBILITY'),
            
            # Final decision
            decision['prob_strong_bullish'],
            decision['prob_bullish'],
            decision['prob_neutral'],
            decision['prob_bearish'],
            decision['prob_strong_bearish'],
            decision['primary_bias'],
            decision['confidence'],
            decision['base_confidence'],
            
            # Validity
            decision['validity'],
            json.dumps(decision['blocking_reasons']),
            decision['is_executable'],
            json.dumps(decision['execution_risk_flags']),
            
            # Risk envelope
            decision['max_position_size'],
            decision['stop_loss_pct'],
            decision['take_profit_pct'],
            decision['max_hold_days'],
            decision['expected_value'],
            
            # Metadata
            json.dumps(decision['pillar_weights']),
            json.dumps(decision['all_risk_flags']),
            decision['num_healthy_pillars'],
            decision['num_degraded_pillars'],
            decision['num_failed_pillars'],
            decision['computation_time_ms']
        ]
        
        cursor = self.db.conn.execute(sql, params)
        self.db.conn.commit()
        
        return cursor.lastrowid
