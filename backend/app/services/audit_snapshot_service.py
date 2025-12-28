import json
import os
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.contracts.state_contracts import AnalysisState

logger = logging.getLogger(__name__)

class AuditSnapshotService:
    """
    Snapshots the QUAD engine state for regression testing and regulatory audit.
    Complies with Phase A requirements for immutable storage.
    """
    
    def __init__(self, snapshot_dir: str = "audit/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def save_snapshot(self, state: AnalysisState) -> str:
        """
        Save an AnalysisState to an immutable JSON file.
        
        Args:
            state: The AnalysisState to snapshot
            
        Returns:
            Path to the saved snapshot
        """
        try:
            # Convert to dict and handle datetimes
            data = state.dict()
            
            # Formatting filename: symbol_YYYYMMDD_HHMMSS_logical_id.json
            timestamp_str = state.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{state.symbol}_{timestamp_str}_{state.decision_id[:8]}.json"
            filepath = self.snapshot_dir / filename
            
            # Serialize with custom datetime handler
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            json_content = json.dumps(data, default=datetime_handler, indent=2, sort_keys=True)
            
            # Add checksum for integrity
            checksum = hashlib.sha256(json_content.encode()).hexdigest()
            
            # We store the checksum inside a sidecar or as part of the JSON metadata
            # For simplicity and "institutional audit-ability", we'll wrap it
            wrapped_content = {
                "metadata": {
                    "checksum": checksum,
                    "snapshot_version": "1.0",
                    "created_at": datetime.utcnow().isoformat()
                },
                "state": data
            }
            
            final_json = json.dumps(wrapped_content, default=datetime_handler, indent=2)
            
            with open(filepath, "w") as f:
                f.write(final_json)
            
            # Make file read-only to simulation immutability (best effort on local filesystem)
            os.chmod(filepath, 0o444)
            
            logger.info(f"✅ Immutable audit snapshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to save audit snapshot: {e}")
            raise

    def verify_snapshot(self, filepath: str) -> bool:
        """
        Verify the integrity of a snapshot using its embedded checksum.
        """
        try:
            with open(filepath, "r") as f:
                wrapped_data = json.load(f)
            
            metadata = wrapped_data.get("metadata", {})
            original_checksum = metadata.get("checksum")
            state_data = wrapped_data.get("state")
            
            if not original_checksum or not state_data:
                return False
            
            # Re-serialize state part exactly as it was saved to verify hash
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
                
            # Note: During load, ISO strings aren't converted back automatically
            # We need to ensure serialization for hashing is deterministic
            json_to_verify = json.dumps(state_data, indent=2, sort_keys=True)
            current_checksum = hashlib.sha256(json_to_verify.encode()).hexdigest()
            
            return original_checksum == current_checksum
            
        except Exception:
            return False

# Global instance
audit_snapshot_service = AuditSnapshotService()
