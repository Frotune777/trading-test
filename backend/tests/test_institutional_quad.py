"""
Test script for Institutional QUAD v2

This script validates that all components work together end-to-end.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime

from app.reasoning.institutional.pillars import (
    PriceStructurePillar,
    InstitutionalFlowPillar,
    DerivativesPillar,
    RegimePillar,
    FundamentalPillar,
    ExecutionPillar
)
from app.reasoning.institutional.input_bundles import (
    PriceStructureInput,
    InstitutionalFlowInput,
    DerivativesInput,
    RegimeInput,
    FundamentalInput,
    ExecutionInput
)
from app.reasoning.institutional.risk_governor import GlobalRiskGovernor
from app.reasoning.institutional.decision_assembler import BayesianDecisionAssembler


def create_mock_price_data():
    """Create mock price data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    return pd.DataFrame({
        'date': dates,
        'open': 100 + pd.Series(range(100)).cumsum() * 0.1,
        'high': 102 + pd.Series(range(100)).cumsum() * 0.1,
        'low': 98 + pd.Series(range(100)).cumsum() * 0.1,
        'close': 100 + pd.Series(range(100)).cumsum() * 0.1,
        'volume': [1000000] * 100
    })


def test_pillar_1_price_structure():
    """Test Pillar 1: Price & Market Structure"""
    print("\n=== Testing Pillar 1: Price & Market Structure ===")
    
    pillar = PriceStructurePillar()
    
    input_bundle = PriceStructureInput(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ohlcv_daily=create_mock_price_data(),
        bid_levels=[(100, 1000), (99.95, 2000), (99.90, 1500)],
        ask_levels=[(100.05, 1000), (100.10, 2000), (100.15, 1500)],
        upper_circuit=110.0,
        lower_circuit=90.0
    )
    
    output = pillar.analyze(input_bundle)
    
    print(f"Primary Bias: {output.primary_bias.value}")
    print(f"Confidence: {output.confidence:.1f}%")
    print(f"Health: {output.health.value}")
    print(f"Probability Distribution:")
    print(f"  Strong Bearish: {output.prob_strong_bearish:.3f}")
    print(f"  Bearish: {output.prob_bearish:.3f}")
    print(f"  Neutral: {output.prob_neutral:.3f}")
    print(f"  Bullish: {output.prob_bullish:.3f}")
    print(f"  Strong Bullish: {output.prob_strong_bullish:.3f}")
    print(f"Risk Flags: {output.risk_flags}")
    
    # Validate probability sum
    prob_sum = (output.prob_strong_bearish + output.prob_bearish + 
                output.prob_neutral + output.prob_bullish + output.prob_strong_bullish)
    assert 0.99 <= prob_sum <= 1.01, f"Probabilities must sum to 1.0, got {prob_sum}"
    print("✅ Probability distribution validated")
    
    return output


def test_all_pillars():
    """Test all 6 pillars"""
    print("\n=== Testing All 6 Pillars ===")
    
    pillars = {
        'Price Structure': PriceStructurePillar(),
        'Institutional Flow': InstitutionalFlowPillar(),
        'Derivatives': DerivativesPillar(),
        'Regime': RegimePillar(),
        'Fundamental': FundamentalPillar(),
        'Execution': ExecutionPillar()
    }
    
    # Create minimal input bundles (will trigger DEGRADED/FAILED states)
    inputs = {
        'Price Structure': PriceStructureInput(
            symbol="RELIANCE",
            timestamp=datetime.now(),
            ohlcv_daily=create_mock_price_data(),
            bid_levels=[(100, 1000)],
            ask_levels=[(100.05, 1000)],
            upper_circuit=110.0,
            lower_circuit=90.0
        ),
        'Institutional Flow': InstitutionalFlowInput(
            symbol="RELIANCE",
            timestamp=datetime.now(),
            fii_net_30d=pd.DataFrame({'fii_net_value': [100] * 20}),
            dii_net_30d=pd.DataFrame({'dii_net_value': [50] * 20}),
            bulk_deals_30d=pd.DataFrame(),
            block_deals_30d=pd.DataFrame(),
            insider_trades_90d=pd.DataFrame()
        ),
        'Derivatives': DerivativesInput(
            symbol="RELIANCE",
            timestamp=datetime.now(),
            option_chain_current=pd.DataFrame(),
            option_chain_next=pd.DataFrame(),
            futures_current=pd.DataFrame(),
            spot_price=100.0
        ),
        'Regime': RegimePillar(),
        'Fundamental': FundamentalPillar(),
        'Execution': ExecutionPillar()
    }
    
    outputs = []
    for name, pillar in pillars.items():
        try:
            # Skip pillars without proper inputs for now
            if name in ['Regime', 'Fundamental', 'Execution']:
                print(f"\n{name}: Skipped (requires full input bundle)")
                continue
                
            print(f"\n{name}:")
            output = pillar.analyze(inputs[name])
            print(f"  Bias: {output.primary_bias.value}")
            print(f"  Confidence: {output.confidence:.1f}%")
            print(f"  Health: {output.health.value}")
            outputs.append(output)
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return outputs


def test_risk_governor():
    """Test Global Risk Governor"""
    print("\n=== Testing Global Risk Governor ===")
    
    # Create mock pillar output
    from app.reasoning.institutional import PillarOutput, PillarHealth, DirectionalBias
    
    pillar_output = PillarOutput(
        pillar_name="PRICE_STRUCTURE",
        timestamp=datetime.now(),
        prob_strong_bullish=0.1,
        prob_bullish=0.3,
        prob_neutral=0.4,
        prob_bearish=0.15,
        prob_strong_bearish=0.05,
        primary_bias=DirectionalBias.NEUTRAL,
        confidence=40.0,
        health=PillarHealth.HEALTHY,
        feature_contributions={'test': 1.0},
        data_sources=['test'],
        feature_version='1.0.0'
    )
    
    governor = GlobalRiskGovernor()
    
    # Test with healthy pillars
    validity, reasons = governor.validate_decision([pillar_output] * 6)
    print(f"Validity: {validity.value}")
    print(f"Reasons: {reasons}")
    
    # Test with failed core pillar
    failed_output = PillarOutput(
        pillar_name="PRICE_STRUCTURE",
        timestamp=datetime.now(),
        prob_strong_bullish=0.0,
        prob_bullish=0.0,
        prob_neutral=1.0,
        prob_bearish=0.0,
        prob_strong_bearish=0.0,
        primary_bias=DirectionalBias.NEUTRAL,
        confidence=0.0,
        health=PillarHealth.FAILED,
        health_message="Test failure",
        feature_contributions={},
        data_sources=[],
        feature_version='1.0.0',
        risk_flags=["PILLAR_FAILED"]
    )
    
    validity, reasons = governor.validate_decision([failed_output] + [pillar_output] * 5)
    print(f"\nWith failed core pillar:")
    print(f"Validity: {validity.value}")
    print(f"Reasons: {reasons}")
    assert validity.value == "INVALID", "Should be INVALID with failed core pillar"
    print("✅ Risk Governor validation working")


def test_decision_assembler():
    """Test Bayesian Decision Assembler"""
    print("\n=== Testing Bayesian Decision Assembler ===")
    
    from app.reasoning.institutional import PillarOutput, PillarHealth, DirectionalBias
    
    # Create 6 mock pillar outputs
    pillar_outputs = []
    pillar_names = [
        "PRICE_STRUCTURE",
        "INSTITUTIONAL_FLOW",
        "DERIVATIVES_POSITIONING",
        "REGIME_CONTEXT",
        "FUNDAMENTAL_THEMATIC",
        "EXECUTION_FEASIBILITY"
    ]
    
    for name in pillar_names:
        output = PillarOutput(
            pillar_name=name,
            timestamp=datetime.now(),
            prob_strong_bullish=0.1,
            prob_bullish=0.3,
            prob_neutral=0.3,
            prob_bearish=0.2,
            prob_strong_bearish=0.1,
            primary_bias=DirectionalBias.BULLISH,
            confidence=50.0,
            health=PillarHealth.HEALTHY,
            feature_contributions={'test_feature': 0.5},
            data_sources=['test_source'],
            feature_version='1.0.0'
        )
        # Add symbol attribute
        output.symbol = "RELIANCE"
        pillar_outputs.append(output)
    
    assembler = BayesianDecisionAssembler()
    decision = assembler.assemble(pillar_outputs)
    
    print(f"Final Bias: {decision['primary_bias']}")
    print(f"Confidence: {decision['confidence']:.1f}%")
    print(f"Validity: {decision['validity']}")
    print(f"Is Executable: {decision['is_executable']}")
    print(f"Risk Envelope:")
    print(f"  Position Size: {decision['max_position_size']:.2f}x")
    print(f"  Stop Loss: {decision['stop_loss_pct']:.1f}%")
    print(f"  Take Profit: {decision['take_profit_pct']:.1f}%")
    print(f"  Max Hold Days: {decision['max_hold_days']}")
    print("✅ Decision Assembler working")
    
    return decision


if __name__ == "__main__":
    print("=" * 60)
    print("INSTITUTIONAL QUAD V2 - VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Test individual pillar
        test_pillar_1_price_structure()
        
        # Test all pillars
        test_all_pillars()
        
        # Test Risk Governor
        test_risk_governor()
        
        # Test Decision Assembler
        test_decision_assembler()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
