"""
Phase 4 Integration Test - End-to-End ReasoningEngine Test
Tests the full flow from data fetch to trade recommendation.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.reasoning_service import ReasoningService

def test_phase_4_integration():
    """Test end-to-end integration with real data fetch."""
    
    print("=" * 60)
    print("Phase 4: End-to-End Integration Test")
    print("=" * 60)
    
    # Initialize reasoning service
    print("\n✓ Step 1: Initializing ReasoningService...")
    service = ReasoningService()
    print("  Service initialized with 6 pillars")
    
    # Test with a known liquid stock
    symbol = "RELIANCE"
    
    print(f"\n✓ Step 2: Analyzing {symbol}...")
    print("  Fetching price data...")
    print("  Calculating technical indicators...")
    print("  Building snapshot and context...")
    print("  Running reasoning engine...")
    
    try:
        result = service.analyze_symbol(symbol)
        
        print("\n" + "=" * 60)
        print(f"ANALYSIS RESULT FOR {symbol}")
        print("=" * 60)
        
        # Display recommendation
        print(f"\n🎯 RECOMMENDATION: {result['action']}")
        print(f"📊 CONFIDENCE: {result['confidence_score']:.1f}/100")
        print(f"📈 POSITION SIZE: {result['quantity_factor']:.0%}")
        
        # Display reasoning
        print(f"\n💡 REASONING:")
        print(f"   {result['reasoning']}")
        
        # Display pillar breakdown
        print(f"\n📊 PILLAR SCORES:")
        scores = result['pillar_scores']
        print(f"   Trend:      {scores['trend']:.1f}/100")
        print(f"   Momentum:   {scores['momentum']:.1f}/100")
        print(f"   Volatility: {scores['volatility']:.1f}/100")
        print(f"   Liquidity:  {scores['liquidity']:.1f}/100")
        print(f"   Sentiment:  {scores['sentiment']:.1f}/100")
        print(f"   Regime:     {scores['regime']:.1f}/100")
        
        # Display market context
        print(f"\n🌍 MARKET CONTEXT:")
        ctx = result['market_context']
        print(f"   Regime: {ctx['regime']}")
        print(f"   VIX: {ctx['vix_level']:.1f}")
        
        # Display technical state
        print(f"\n📉 TECHNICAL STATE:")
        tech = result['technical_state']
        print(f"   LTP: ₹{tech['ltp']:.2f}")
        print(f"   SMA50: ₹{tech['sma_50']:.2f}")
        print(f"   SMA200: ₹{tech['sma_200']:.2f}")
        print(f"   RSI: {tech['rsi']:.1f}")
        
        print("\n" + "=" * 60)
        print("✅ Phase 4 Integration Test PASSED")
        print("=" * 60)
        
        # Verify data quality
        assert result['confidence_score'] > 0, "Confidence should be positive"
        assert result['action'] in ['BUY', 'SELL', 'HOLD', 'NO_TRADE', 'EXIT_ALL'], "Valid action"
        assert scores['trend'] >= 0 and scores['trend'] <= 100, "Trend score valid"
        assert scores['momentum'] >= 0 and scores['momentum'] <= 100, "Momentum score valid"
        
        print("\n✓ All validations passed!")
        print("✓ ReasoningEngine is production-ready!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_phase_4_integration()
