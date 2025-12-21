import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.recommendation_service import RecommendationService

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_recommendations():
    print("🚀 Initializing Recommendation Service...")
    service = RecommendationService()
    
    print("\n📊 generating 'balanced' recommendations...")
    recs = service.generate_recommendations(strategy='balanced', limit=5)
    
    if not recs:
        print("⚠️ No recommendations found. Check if database has data.")
        return

    print(f"✅ Found {len(recs)} recommendations:\n")
    for r in recs:
        print(f"Stock: {r['symbol']}")
        print(f"  Smart Score: {r['smart_score']} ({r['action']})")
        print(f"  Technical: {r['technical_score']}")
        print(f"  Fundamental: {r['fundamental_score']}")
        print(f"  Details: {r['technical_details'].get('trend', 'N/A')}")
        print(f"  Signal: {r.get('stop_loss', 'N/A')} / {r.get('target_price', 'N/A')}")
        print(f"  Why? {r.get('explanation', 'N/A')}")
        print("-" * 30)

if __name__ == "__main__":
    test_recommendations()
