import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.reasoning_service import ReasoningService

def test_sentinel():
    service = ReasoningService()
    symbol = "INDOSTAR" # Confirmed in debug output
    print(f"Testing Sentinel Logic for: {symbol}")
    
    try:
        result = service.analyze_symbol(symbol)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return

        print("\n=== QUAD ANALYSIS RESULTS ===")
        print(f"Symbol: {result['symbol']}")
        print(f"Bias: {result['directional_bias']}")
        print(f"Conviction: {result['conviction_score']:.2f}")
        
        print("\n=== SENTIMENT PILLAR (SENTINEL) ===")
        sentiment = result['pillar_scores'].get('sentiment', {})
        print(f"Score: {sentiment.get('score')}")
        print(f"Bias: {sentiment.get('bias')}")
        
        metrics = sentiment.get('metrics', {})
        print("Metrics:")
        for k, v in metrics.items():
            print(f"  - {k}: {v}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_sentinel()
