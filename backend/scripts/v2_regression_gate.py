import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from app.services.quad_analysis_engine import QUADAnalysisEngine
from app.services.audit_snapshot_service import audit_snapshot_service
from app.core.contracts.state_contracts import AnalysisState
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class RegressionGate:
    """
    Validates current engine logic against locked audit snapshots.
    If 'diff' > 0.001% in any score, the gate FAILS.
    """
    
    def __init__(self, snapshots_dir: str = "audit/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        
    async def run_verification(self, symbol: str) -> bool:
        """
        Runs the current engine for a symbol and compares against the latest snapshot.
        """
        logger.info(f"🚀 Starting Regression Gate for {symbol}...")
        
        # 1. Find the latest snapshot for this symbol
        snapshots = sorted(list(self.snapshots_dir.glob(f"{symbol}_*.json")), reverse=True)
        if not snapshots:
            logger.error(f"❌ No snapshots found for {symbol}. Cannot verify.")
            return False
            
        latest_snapshot_path = snapshots[0]
        logger.info(f"Using snapshot: {latest_snapshot_path}")
        
        # 2. Load the snapshot
        with open(latest_snapshot_path, "r") as f:
            snapshot_data = json.load(f)
            expected_state = snapshot_data["state"]
            
        # 3. Run the engine (requires an active database session)
        async with SessionLocal() as db:
            engine = QUADAnalysisEngine(db)
            # Re-running analyze_symbol will use current data in DB. 
            # Note: For perfect regression testing, we would need to mock the data fetchers
            # to return the EXACT same data as when the snapshot was taken.
            # In Phase A, we assume DB hasn't changed dramatically between snapshot and verify,
            # or we manually populate the DB with the snapshot's logical time data.
            try:
                current_decision = await engine.analyze_symbol(symbol)
            except Exception as e:
                logger.error(f"❌ Engine failed during verification: {e}")
                return False
                
        # 4. Compare
        # We compare conviction and signal as top-level regression points
        conviction_diff = abs(current_decision.conviction - expected_state["conviction"])
        signal_match = (current_decision.signal == expected_state["signal"])
        
        if conviction_diff > 0 or not signal_match:
            logger.error(f"❌ REGRESSION DETECTED for {symbol}")
            logger.error(f"Expected Signal: {expected_state['signal']}, Got: {current_decision.signal}")
            logger.error(f"Expected Conviction: {expected_state['conviction']}, Got: {current_decision.conviction}")
            return False
            
        logger.info(f"✅ Regression Gate passed for {symbol}")
        return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: python v2_regression_gate.py <SYMBOL>")
        sys.exit(1)
        
    symbol = sys.argv[1]
    gate = RegressionGate()
    success = await gate.run_verification(symbol)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
