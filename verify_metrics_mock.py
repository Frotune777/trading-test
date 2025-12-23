
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.reasoning.pillars.liquidity_pillar import LiquidityPillar
from app.reasoning.pillars.sentiment_pillar import SentimentPillar
from app.core.market_snapshot import LiveDecisionSnapshot
from datetime import datetime

def verify_missing_metrics_behavior():
    print("Verifying Pillar behavior with missing data...")
    
    # Create empty snapshot (simulating market closed / no data)
    snapshot = LiveDecisionSnapshot(
        symbol="TEST",
        timestamp=datetime.now(),
        ltp=100.0,
        vwap=100.0,
        open=100.0,
        high=100.0,
        low=100.0,
        prev_close=100.0,
        volume=0
    )
    
    # Test Liquidity Pillar
    liq_pillar = LiquidityPillar()
    score, bias, metrics = liq_pillar.analyze(snapshot, None)
    print("\nLiquidity Pillar Metrics (Expect N/A):")
    print(metrics)
    
    if "Spread %" in metrics and metrics["Spread %"] == "N/A":
        print("✅ Liquidity Pillar handles missing data correctly")
    else:
        print("❌ Liquidity Pillar failed to return N/A metrics")

    # Test Sentiment Pillar
    sent_pillar = SentimentPillar()
    score, bias, metrics = sent_pillar.analyze(snapshot, None)
    print("\nSentiment Pillar Metrics (Expect N/A):")
    print(metrics)
    
    if "OI Change" in metrics and metrics["OI Change"] == "N/A":
        print("✅ Sentiment Pillar handles missing data correctly")
    else:
         print("❌ Sentiment Pillar failed to return N/A metrics")

if __name__ == "__main__":
    verify_missing_metrics_behavior()
