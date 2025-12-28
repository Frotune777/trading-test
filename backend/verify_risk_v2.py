import asyncio
import httpx
import sys
import logging
from app.core.risk_engine import RiskEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_risk")

BASE_URL = "http://localhost:8000/api/v1"

async def test_risk_controls():
    print("\n--- Testing Risk Management Engine ---")
    
    # 1. Test Kill Switch API
    print("\n1. Testing Kill Switch API...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Activate
        print("   Activating Kill Switch...")
        resp = await client.post(f"{BASE_URL}/risk-control/kill-switch", json={"action": "ACTIVATE", "reason": "Test Verification"})
        if resp.status_code == 200 and resp.json()['status'] == "success":
            print("✅ Kill Switch ACTIVATED")
        else:
            print(f"❌ Failed to activate Kill Switch: {resp.text}")
            return

        # Check Status
        print("   Checking Status...")
        resp = await client.get(f"{BASE_URL}/risk-control/kill-switch")
        if resp.json()['active'] == True:
            print("✅ Kill Switch Status: ACTIVE")
        else:
            print("❌ Kill Switch Status Incorrect")
            return

    # 2. Verify RiskEngine Blocks Trade when Kill Switch Active
    print("\n2. Verifying RiskEngine Block...")
    engine = RiskEngine()
    # Mock trade
    allowed, reason = await engine.check_risk("TEST", 10, 100.0)
    if not allowed and "Kill Switch is ACTIVE" in reason:
        print(f"✅ Trade BLOCKED correctly: {reason}")
    else:
        print(f"❌ Trade NOT blocked or wrong reason: {allowed}, {reason}")

    # 3. Deactivate Kill Switch
    print("\n3. Deactivating Kill Switch...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BASE_URL}/risk-control/kill-switch", json={"action": "DEACTIVATE", "reason": "Test Complete"})
        if resp.status_code == 200:
            print("✅ Kill Switch DEACTIVATED")
        else:
            print(f"❌ Failed to deactivate: {resp.text}")


    # 4. Test Position Limit (Hard Limit 1000)
    print("\n4. Testing Position Limit...")
    allowed, reason = await engine.check_risk("TEST", 1001, 100.0)
    if not allowed and "Quantity 1001 > Max Limit" in reason:
         print(f"✅ Position Limit Enforced: {reason}")
    else:
         print(f"❌ Position Limit Failed: {allowed}, {reason}")
         
    print("\n--- Validation Complete ---")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_risk_controls())
