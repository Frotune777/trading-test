from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime

class DirectionalBias(Enum):
    """
    Reasoning output ONLY. Does NOT authorize execution.
    Expresses the engine's directional opinion based on analysis.
    """
    BULLISH = "BULLISH"  # Logic favors upside
    BEARISH = "BEARISH"  # Logic favors downside
    NEUTRAL = "NEUTRAL"  # No directional edge detected
    INVALID = "INVALID"  # Analysis failed or insufficient data

@dataclass
class PillarContribution:
    """
    Individual pillar's contribution to the reasoning decision.
    Used for transparency and explainability.
    """
    name: str                    # "trend", "momentum", "volatility", etc.
    score: float                 # 0-100 (pillar-specific scale)
    bias: str                    # "BULLISH", "BEARISH", "NEUTRAL"
    is_placeholder: bool         # True if returning hardcoded neutral
    weight_applied: float        # Weight used in aggregation (e.g., 0.30)
    metrics: Optional[dict] = None # Key metrics used for calculation (e.g., {"ATR%": 1.2, "VIX": 14})

@dataclass
class AnalysisQuality:
    """
    Metadata about the analysis completeness and reliability.
    Critical for frontend to calibrate user trust appropriately.
    
    v1.0 Fields: total_pillars, active_pillars, placeholder_pillars, failed_pillars, data_age_seconds
    v1.1 Additions: calibration_version, pillar_weights_snapshot
    """
    # v1.0 Fields (FROZEN)
    total_pillars: int             # Total QUAD pillars (should be 6)
    active_pillars: int            # Pillars with real logic implemented
    placeholder_pillars: int       # Pillars returning neutral defaults
    failed_pillars: List[str]      # Pillars that threw exceptions
    data_age_seconds: Optional[int] = None  # Age of input snapshot
    
    # v1.1 Additions (OPTIONAL - backward compatible)
    calibration_version: Optional[str] = None  # e.g., "matrix_2024_q4"
    pillar_weights_snapshot: Optional[dict] = None  # e.g., {"trend": 0.30, "momentum": 0.20, ...}

@dataclass
class TradeIntent:
    """
    NON-BINDING reasoning output from QUAD engine. [CONTRACT v1.1.0]
    
    🚨 CRITICAL: This is NOT an execution instruction.
    This is a DIAGNOSTIC output expressing the engine's OPINION.
    
    Frontend MUST display this as analysis, NOT as trading advice.
    Execution layer MUST revalidate and apply its own risk rules.
    
    Contract Version: 1.1.0
    Changes from v1.0:
    - Extended: AnalysisQuality with calibration_version and pillar_weights_snapshot
    - All v1.0 fields remain unchanged (100% backward compatible)
    
    Breaking changes from v0.x:
    - Removed: quantity_factor, stop_loss, target_price
    - Added: quality metadata, execution_ready flag
    - Renamed: action → directional_bias
    """
    # Identity
    symbol: str
    analysis_timestamp: datetime
    
    # Core Reasoning Output
    directional_bias: DirectionalBias
    conviction_score: float  # 0-100 (how confident the logic is)
    
    # Explainability
    pillar_contributions: List[PillarContribution]
    reasoning_narrative: str  # Human-readable explanation
    
    # Quality Metadata (NEW in v1.0, EXTENDED in v1.1)
    quality: AnalysisQuality
    
    # Validity Flags (NEW in v1.0)
    is_analysis_valid: bool      # False if critical data missing
    is_execution_ready: bool     # False if placeholder pillars > threshold
    execution_block_reason: Optional[str] = None # E.g., "FEED_DEGRADED", "STALE_LTP"
    degradation_warnings: List[str] = None       # E.g., ["Volatility pillar is placeholder"]
    
    # Version & Schema
    contract_version: str = "1.1.0"  # Semantic versioning for frontend
