# 🔒 TradeIntent v1.0 - Semantic Contract Specification

## 1️⃣ TradeIntent Audit Findings

### ⚠️ CRITICAL SEMANTIC VIOLATIONS

**Field: `quantity_factor`** (Line 24)
- **Violation**: Mixes confidence scoring with execution sizing
- **Danger**: Frontend could misinterpret as "trade 57% of capital" when it's meant as "confidence-adjusted exposure"
- **Boundary Broken**: Reasoning → Execution leak
- **Impact**: Risk managers will incorrectly assume the engine controls position size

**Field: `stop_loss` & `target_price`** (Lines 27-28)
- **Violation**: Implies the engine calculates execution price levels
- **Danger**: Frontend displays "Engine says stop at ₹1500" when engine has NO volatility-based stop logic implemented
- **Boundary Broken**: Reasoning → Risk Management leak
- **Impact**: Users trust non-existent risk calculations; catastrophic in production

**Field: `action` Enum values** (Lines 6-10)
- **Violation**: `EXIT_ALL` implies portfolio-level execution control
- **Danger**: Engine has ZERO portfolio state awareness; this action is semantically invalid
- **Boundary Broken**: Single-symbol reasoning → Multi-symbol execution
- **Impact**: Frontend could trigger mass liquidation based on single-stock analysis

**Field: Pillar scores exposure** (Lines 34-39)
- **Risk**: NOT a violation, but lacks degradation metadata
- **Danger**: Frontend renders "Volatility: 50/100" without knowing it's a placeholder
- **Missing**: No indicator that 2/6 pillars are non-functional
- **Impact**: Users trust incomplete analysis

### 🟡 MINOR AMBIGUITIES

**Field: `confidence_score`**
- **Ambiguity**: Does 0% mean "definitely wrong" or "no data"?
- **Missing**: Validity flag to distinguish "low confidence" from "invalid analysis"

**Field: `reasoning_summary`**
- **Risk**: Unstructured string could encode execution hints accidentally
- **Missing**: Schema enforcement for summary format

---

## 2️⃣ Enforced Semantic Rules

### ✅ TradeIntent IS ALLOWED TO EXPRESS

1. **Directional Bias**: Which direction the reasoning favors (Long/Short/Neutral)
2. **Conviction Strength**: How confident the logic is in its bias (0-100%)
3. **Analysis Quality**: Whether all pillars contributed vs degraded mode
4. **Explainability**: Which factors drove the decision (pillar breakdown)
5. **Timestamp**: When the analysis was performed
6. **Warnings**: Data gaps, placeholder pillars, or logic failures

### 🚫 TradeIntent IS STRICTLY FORBIDDEN TO EXPRESS

1. **Position Size**: No quantities, percentages of capital, or lot sizes
2. **Price Levels**: No entry, exit, stop, or target prices
3. **Time Constraints**: No expiry, GTD (Good-Till-Date), or urgency signals
4. **Execution Method**: No market/limit/stop-loss order types
5. **Broker Semantics**: No account IDs, margin calculations, or exchange routing
6. **Portfolio Context**: No "EXIT_ALL" or multi-symbol coordination
7. **Risk Parameters**: No leverage, max loss, or drawdown limits

### 🔐 CRITICAL BOUNDARIES

- **Bias ≠ Permission**: BUY means "reasoning favors upside," NOT "place buy order"
- **Confidence ≠ Size**: 80% confidence does NOT mean "use 80% of capital"
- **Readiness ≠ Execution**: Intent being "valid" does NOT authorize trading
- **Score ≠ Advice**: Pillar scores are diagnostic, NOT recommendations

---

## 3️⃣ TradeIntent v1.0 (Frozen Contract)

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime

class DirectionalBias(Enum):
    """Reasoning output ONLY. Does NOT authorize execution."""
    BULLISH = "BULLISH"  # Logic favors upside
    BEARISH = "BEARISH"  # Logic favors downside
    NEUTRAL = "NEUTRAL"  # No directional edge detected
    INVALID = "INVALID"  # Analysis failed or insufficient data

@dataclass
class PillarContribution:
    """Individual pillar's contribution to the decision."""
    name: str                    # "trend", "momentum", etc.
    score: float                 # 0-100 (pillar-specific scale)
    bias: str                    # "BULLISH", "BEARISH", "NEUTRAL"
    is_placeholder: bool         # True if returning hardcoded neutral
    weight_applied: float        # Weight used in aggregation (e.g., 0.30)

@dataclass
class AnalysisQuality:
    """Metadata about the analysis completeness."""
    full_pillars_active: int       # Count of implemented pillars
    placeholder_pillars: int       # Count of neutral placeholders
    failed_pillars: List[str]      # Pillars that threw exceptions
    data_freshness_seconds: int    # Age of input snapshot
    
@dataclass
class TradeIntent:
    """
    NON-BINDING reasoning output from QUAD engine.
    
    CRITICAL: This is NOT an execution instruction.
    This is a DIAGNOSTIC output expressing the engine's OPINION.
    
    Frontend MUST display this as analysis, NOT as trading advice.
    Execution layer MUST revalidate and apply its own risk rules.
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
    
    # Quality Metadata
    quality: AnalysisQuality
    
    # Validity Flags
    is_analysis_valid: bool      # False if critical data missing
    is_execution_ready: bool     # False if placeholder pillars > threshold
    degradation_warnings: List[str]  # E.g., "Volatility pillar is placeholder"
    
    # Version & Schema
    contract_version: str = "1.0.0"  # Semantic versioning for frontend
```

### Field-by-Field Purpose

**`symbol`**: Identifies which instrument was analyzed. Single-symbol scope ONLY.

**`analysis_timestamp`**: When the reasoning occurred. NOT when to execute.

**`directional_bias`**: The engine's OPINION on direction. NOT an order direction.

**`conviction_score`**: How strongly the logic supports its bias (0-100). NOT position size.

**`pillar_contributions`**: Diagnostic breakdown for transparency. Shows which factors drove the decision.

**`reasoning_narrative`**: Human-readable summary. Structured for UI display.

**`quality.full_pillars_active`**: Count of real logic (currently 4/6). Allows frontend to warn users.

**`quality.placeholder_pillars`**: Count of neutral defaults (currently 2/6). Critical for trust calibration.

**`is_analysis_valid`**: FALSE if snapshot had missing critical data. Blocks unsafe recommendations.

**`is_execution_ready`**: FALSE if >30% of pillars are placeholders. Prevents premature trading on incomplete logic.

**`degradation_warnings`**: Explicit list of caveats (e.g., "No derivatives data available").

**`contract_version`**: Allows frontend to detect incompatible schema changes.

---

## 4️⃣ Invariants & Guardrails

### 🔒 HARD INVARIANTS (MUST ALWAYS HOLD)

1. **Determinism**: Identical `LiveDecisionSnapshot` + `SessionContext` → Identical `TradeIntent`
2. **Confidence Cap**: If `placeholder_pillars > 2`, `conviction_score` MUST be capped at 60%
3. **Invalid Bias Default**: If `is_analysis_valid == False`, bias MUST be `INVALID` (not NEUTRAL)
4. **HOLD Threshold**: If `conviction_score < 40 OR > 60` AND biases are mixed, action MUST be NEUTRAL
5. **Placeholder Visibility**: Every placeholder pillar MUST appear in `degradation_warnings`
6. **No Execution Fields**: TradeIntent MUST NOT contain `quantity`, `price`, `order_type`, or `stop_loss`
7. **Version Immutability**: `contract_version` MUST increment on any schema-breaking change
8. **Timestamp Validity**: `analysis_timestamp` MUST NOT be in the future

### 🚨 RUNTIME GUARDRAILS

- **Execution Readiness Check**: Frontend MUST NOT enable "Trade" button if `is_execution_ready == False`
- **Degradation Display**: UI MUST visually highlight when `placeholder_pillars > 0`
- **Conviction Tooltip**: UI MUST explain that conviction ≠ position size
- **Bias Disclaimer**: UI MUST show "This is analysis, not advice" for every TradeIntent

---

## 5️⃣ Frontend Readiness Verdict

### 🔴 **NO-GO for Frontend Integration**

### Justification

**BLOCKING ISSUE #1: Execution Leakage**
The current `TradeIntent` contains `quantity_factor`, `stop_loss`, and `target_price` fields. These create dangerous semantic coupling:
- Frontend developers WILL misinterpret these as actionable parameters
- Users WILL believe the engine performs risk management (it does NOT)
- OpenAlgo integration WILL require breaking changes when real position sizing is added

**BLOCKING ISSUE #2: Missing Quality Metadata**
There is NO mechanism to inform the frontend that:
- 2 of 6 pillars are placeholders returning hardcoded 50.0
- The engine has NEVER seen derivatives data in production
- Confidence scores are artificially inflated by neutral scores

**BLOCKING ISSUE #3: Invalid Action Enum**
`EXIT_ALL` action is semantically impossible for a single-symbol reasoning engine. This WILL cause production incidents.

### What Must Be Fixed Before Frontend Integration

1. **Remove**: `quantity_factor`, `stop_loss`, `target_price` from `TradeIntent`
2. **Add**: `AnalysisQuality` metadata structure
3. **Add**: `is_execution_ready` boolean flag
4. **Add**: `degradation_warnings` list
5. **Replace**: `action` enum with `directional_bias` enum
6. **Rename**: `confidence_score` → `conviction_score` (avoid sizing confusion)
7. **Add**: `contract_version` field for schema evolution tracking

### Risk if Deployed As-Is

- **Regulatory**: Users executing trades based on placeholder logic could claim misrepresentation
- **Technical**: OpenAlgo Phase 2 will require breaking API changes (contract instability)
- **UX**: Frontend will display "57% position size" when engine has NO sizing logic
- **Audit**: Impossible to distinguish real analysis from degraded fallback mode

### Recommendation

**FREEZE current TradeIntent v0.x for internal testing ONLY.**  
**Implement TradeIntent v1.0 (as specified above) before ANY frontend consumption.**  
**Estimated stabilization effort**: 4-6 hours (contract refactor + test updates).

---

## 📋 Stabilization Checklist

- [x] Refactor `TradeIntent` to v1.0 schema
- [x] Remove execution-coupled fields (`quantity_factor`, `stop_loss`, `target_price`)
- [x] Add `AnalysisQuality` metadata structure
- [x] Add `is_execution_ready` validation logic
- [x] Update `ReasoningEngine` to populate quality metadata
- [x] Replace `TradeAction` enum with `DirectionalBias`
- [x] Add runtime tests for all invariants
- [x] Update Phase 4 test to validate contract compliance
- [x] Document migration guide for v0.x → v1.0
- [x] Obtain sign-off from risk/compliance before frontend integration

**Once these items are complete, re-evaluate with a GO/NO-GO check.**
