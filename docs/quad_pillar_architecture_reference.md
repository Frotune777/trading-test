# QUAD System - Pillar Architecture Reference (TradeIntent v1.0)

## Document Overview
This document provides a comprehensive reference for the six analytical pillars that comprise the QUAD (Quantitative & Unified Analysis & Decision) reasoning engine. It details their roles, data dependencies, output specifications, and integration patterns.

---

## 1. PILLAR DEFINITIONS

### 1.1 Trend Pillar
- **Status**: ✅ IMPLEMENTED
- **Analytical Role**: Evaluates price trend strength and direction using moving average alignment
- **Technical Approach**: Multi-timeframe SMA crossover analysis (Daily + Weekly confirmation)
- **Key Indicators**: SMA50, SMA200, SMA20 (weekly)
- **Output**: Directional bias (BULLISH/BEARISH/NEUTRAL) based on MA stack alignment

### 1.2 Momentum Pillar
- **Status**: ✅ IMPLEMENTED
- **Analytical Role**: Measures rate of price change and oscillator signals
- **Technical Approach**: RSI zones + MACD crossover analysis
- **Key Indicators**: RSI (14-period), MACD, MACD Signal, MACD Histogram
- **Output**: Momentum strength classification (Bullish momentum, Overbought, Oversold, Neutral)

### 1.3 Volatility Pillar
- **Status**: ⚠️ PLACEHOLDER
- **Analytical Role**: Assesses price volatility and risk conditions
- **Intended Approach**: ATR (Average True Range) analysis, Bollinger Band width
- **Current Behavior**: Returns hardcoded neutral (50.0 score, NEUTRAL bias)
- **Planned Output**: Volatility regime classification (Low/Normal/High/Extreme)

### 1.4 Liquidity Pillar
- **Status**: ⚠️ PLACEHOLDER
- **Analytical Role**: Evaluates market depth and execution feasibility
- **Intended Approach**: Bid-ask spread analysis, L2 order book depth, volume profile
- **Current Behavior**: Returns hardcoded neutral (50.0 score, NEUTRAL bias)
- **Planned Output**: Liquidity quality score (0-100, tight/normal/wide spread classification)

### 1.5 Sentiment Pillar
- **Status**: ✅ IMPLEMENTED
- **Analytical Role**: Analyzes derivatives-based market sentiment
- **Technical Approach**: Open Interest change patterns, Greeks exposure (Delta/Gamma)
- **Key Indicators**: OI Change, Delta, Gamma, Theta
- **Output**: Derivatives sentiment (Long buildup, Short buildup, Covering, Unwinding)

### 1.6 Regime Pillar
- **Status**: ✅ IMPLEMENTED
- **Analytical Role**: Determines macro market environment and risk appetite
- **Technical Approach**: Market-wide trend detection using benchmark index (NIFTY 50)
- **Key Indicators**: Market regime classification, VIX level, ADX
- **Output**: Market regime (BULLISH/BEARISH/VOLATILE/SIDEWAYS) with VIX-based adjustments

---

## 2. DATA SOURCES

### 2.1 Trend Pillar
**Required Inputs**:
- `LiveDecisionSnapshot.ltp` (Last Traded Price)
- `LiveDecisionSnapshot.sma_50` (50-day Simple Moving Average)
- `LiveDecisionSnapshot.sma_200` (200-day Simple Moving Average)
- `LiveDecisionSnapshot.sma_20_weekly` (Weekly 20-period SMA)

**Data Source**: NSE historical price data via `TechnicalAnalysisService`
**Wiring Status**: ✅ CONNECTED (via `SnapshotBuilder.build_snapshot()`)
**Update Frequency**: Daily (indicators calculated on historical OHLCV data)

### 2.2 Momentum Pillar
**Required Inputs**:
- `LiveDecisionSnapshot.rsi` (Relative Strength Index)
- `LiveDecisionSnapshot.macd` (MACD line)
- `LiveDecisionSnapshot.macd_signal` (MACD signal line)
- `LiveDecisionSnapshot.macd_hist` (MACD histogram)

**Data Source**: NSE historical price data via `TechnicalAnalysisService`
**Wiring Status**: ✅ CONNECTED (via `SnapshotBuilder.build_snapshot()`)
**Update Frequency**: Daily (calculated on OHLCV data)

### 2.3 Volatility Pillar
**Required Inputs** (Planned):
- `LiveDecisionSnapshot.atr` (Average True Range) - NOT YET IN SCHEMA
- `LiveDecisionSnapshot.bb_width` (Bollinger Band Width) - NOT YET IN SCHEMA
- `SessionContext.vix_level` (India VIX)

**Data Source**: NSE historical data + India VIX index
**Wiring Status**: ❌ NOT CONNECTED (placeholder returns neutral)
**Update Frequency**: Intraday (when implemented)

### 2.4 Liquidity Pillar
**Required Inputs** (Planned):
- `LiveDecisionSnapshot.bid_price` (Best bid)
- `LiveDecisionSnapshot.ask_price` (Best ask)
- `LiveDecisionSnapshot.bid_qty` (Bid depth)
- `LiveDecisionSnapshot.ask_qty` (Ask depth)
- `LiveDecisionSnapshot.spread_pct` (Bid-ask spread %)

**Data Source**: NSE L2 market depth (Level 2 order book)
**Wiring Status**: ⚠️ PARTIAL (fields exist in schema but not populated by `SnapshotBuilder`)
**Update Frequency**: Real-time (when implemented)

### 2.5 Sentiment Pillar
**Required Inputs**:
- `LiveDecisionSnapshot.oi_change` (Change in Open Interest)
- `LiveDecisionSnapshot.delta` (Option delta)
- `LiveDecisionSnapshot.gamma` (Option gamma)
- `LiveDecisionSnapshot.ltp` (for price direction correlation)
- `LiveDecisionSnapshot.prev_close` (for price change calculation)

**Data Source**: NSE Option Chain API (via `nse_utils`)
**Wiring Status**: ⚠️ PARTIAL (logic implemented but option data not always available)
**Update Frequency**: Intraday (options data updated every 3-5 minutes)

### 2.6 Regime Pillar
**Required Inputs**:
- `SessionContext.market_regime` (BULLISH/BEARISH/VOLATILE/SIDEWAYS)
- `SessionContext.vix_level` (India VIX spot level)
- `SessionContext.vix_percentile` (Optional: VIX historical percentile)

**Data Source**: `MarketRegime` service analyzing NIFTY 50 data
**Wiring Status**: ✅ CONNECTED (via `SnapshotBuilder.build_session_context()`)
**Update Frequency**: Every 5-15 minutes (warm path data)

---

## 3. OUTPUT FORMAT

### 3.1 Pillar Output Signature
Each pillar implements the `BasePillar.analyze()` method with signature:
```python
def analyze(snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]
```

**Returns**:
- `score: float` - Numeric score in range [0.0, 100.0]
- `bias: str` - Categorical label: "BULLISH" | "BEARISH" | "NEUTRAL"

### 3.2 Score Normalization Rules

**Trend Pillar**:
- Raw scoring: 60 points maximum (30 daily + 30 weekly)
- Normalization: `(raw_score / 60.0) * 100.0`
- Result range: 0-100, where 100 = perfect MA alignment

**Momentum Pillar**:
- Raw scoring: 40 points maximum (20 RSI + 20 MACD)
- Normalization: `(raw_score / 40.0) * 100.0`
- Result range: 0-100, where 100 = perfect bullish momentum

**Sentiment Pillar**:
- Base score: 50.0 (neutral baseline)
- Adjustments: ±20 for OI patterns, ±15 for Delta exposure, -10% for high Gamma
- No explicit normalization (directly operates on 0-100 scale)
- Result range: 0-100 after validation

**Regime Pillar**:
- Base scores: BULLISH=85, BEARISH=15, SIDEWAYS=50, VOLATILE=50
- VIX adjustments: -10 for BULLISH + high VIX, +5 for trending + low VIX
- Result range: 0-100 after `_validate_score()` clipping

**Placeholder Pillars** (Volatility, Liquidity):
- Hardcoded score: 50.0
- Hardcoded bias: "NEUTRAL"
- No normalization (static output)

### 3.3 Validation & Clipping
All pillar scores are passed through `BasePillar._validate_score(score)`:
```python
return max(0.0, min(100.0, score))  # Clamps to [0, 100]
```

---

## 4. VALIDATION CRITERIA

### 4.1 Definition of "Real Analytical Logic"
A pillar is considered "implemented" (non-placeholder) if:
1. **Dynamic Calculation**: Score varies based on input data (not hardcoded)
2. **Data Dependency**: Consumes at least one field from `LiveDecisionSnapshot` or `SessionContext`
3. **Logic Branching**: Contains conditional logic that produces different outputs for different market conditions
4. **Bias Determination**: Bias is computed, not hardcoded to "NEUTRAL"

### 4.2 Placeholder Detection
Placeholders are explicitly tracked in:
```python
ReasoningEngine.placeholder_pillars = set(['volatility', 'liquidity'])
```

**Criteria**:
- Pillar always returns `(50.0, "NEUTRAL")` regardless of inputs
- No data fields consumed from snapshot/context
- Marked in `PillarContribution.is_placeholder = True`

### 4.3 Execution Readiness Thresholds
```python
MAX_PLACEHOLDER_THRESHOLD = 2  # Maximum allowed placeholders for execution readiness
MIN_VALID_CONVICTION = 20.0    # Minimum conviction score for valid analysis
```

**Rules**:
- `is_execution_ready = False` if `placeholder_pillars > 2`
- `is_execution_ready = False` if any `failed_pillars` exist
- `is_execution_ready = False` if `conviction_score < 20.0`
- Conviction score capped at 60.0 when `placeholder_pillars > MAX_PLACEHOLDER_THRESHOLD`

### 4.4 Output Validation Checks
1. **Score Range**: `0.0 <= score <= 100.0` (enforced by `_validate_score`)
2. **Bias Values**: Must be in `["BULLISH", "BEARISH", "NEUTRAL"]`
3. **Non-Null**: Score and bias must both be returned (no `None` values)
4. **Determinism**: Same inputs must produce same outputs (no randomness)

---

## 5. INTEGRATION BOUNDARIES

### 5.1 Pillar → DirectionalBias Flow
```
Pillar Outputs (6 × (score, bias))
    ↓
Weighted Aggregation (conviction_score = Σ(score × weight))
    ↓
Bias Counting (bullish_count vs bearish_count from pillar biases)
    ↓
DirectionalBias Determination:
  - conviction ≥ 65 AND bullish_count > bearish_count → BULLISH
  - conviction ≤ 35 AND bearish_count > bullish_count → BEARISH
  - Otherwise → NEUTRAL
  - If invalid data → INVALID
```

**Pillar Weights** (from Decision Matrix):
- Trend: 30%
- Momentum: 20%
- Volatility: 10%
- Liquidity: 10%
- Sentiment: 10%
- Regime: 20%

### 5.2 Pillar → AnalysisQuality Flow
```python
AnalysisQuality(
    total_pillars=6,
    active_pillars=len(pillars) - len(placeholder_pillars) - len(failed_pillars),
    placeholder_pillars=len(placeholder_pillars),  # Currently 2: volatility, liquidity
    failed_pillars=[...]  # Pillars that raised exceptions
)
```

### 5.3 Pillar → PillarContribution Flow
Each pillar produces:
```python
PillarContribution(
    name="trend",  # Pillar identifier
    score=83.33,   # Normalized 0-100 score
    bias="BULLISH",  # Directional bias
    is_placeholder=False,  # True for volatility/liquidity
    weight_applied=0.30  # Weight used in aggregation
)
```

### 5.4 Execution Decoupling Guarantee
**Strict Non-Execution Rules**:
1. Pillars MUST NOT:
   - Reference position size, quantity, or capital
   - Calculate stop-loss or target prices
   - Consider portfolio context or existing positions
   - Reference broker APIs or exchange semantics
   - Make order routing decisions

2. Pillars MUST ONLY:
   - Analyze market data (price, volume, Greeks, breadth)
   - Produce diagnostic scores (0-100 scale)
   - Classify directional bias (opinion, not instruction)
   - Consume canonical `LiveDecisionSnapshot` and `SessionContext` objects

3. Enforcement:
   - TradeIntent v1.0 contract removed all execution fields
   - `DirectionalBias` enum explicitly states "Does NOT authorize execution"
   - Pillars are stateless (no memory of past trades)
   - Output is `TradeIntent` (non-binding recommendation only)

### 5.5 Contract Version Stability
- **Current Version**: `1.0.0`
- **Breaking Change Policy**: Any change to pillar output signatures, score ranges, or `PillarContribution` schema requires major version bump (e.g., 2.0.0)
- **Forward Compatibility**: Frontend checks `contract_version` field to ensure compatibility

---

## 6. SUMMARY MATRIX

| Pillar | Status | Data Source | Output Type | Execution Ready Impact |
|--------|--------|-------------|-------------|------------------------|
| Trend | ✅ Implemented | NSE OHLCV → SMA | 0-100 normalized | ✓ Contributes (30% weight) |
| Momentum | ✅ Implemented | NSE OHLCV → RSI/MACD | 0-100 normalized | ✓ Contributes (20% weight) |
| Volatility | ⚠️ Placeholder | N/A (planned: ATR/BB) | Hardcoded 50.0 | ⚠️ Degrades (counted in threshold) |
| Liquidity | ⚠️ Placeholder | N/A (planned: L2 depth) | Hardcoded 50.0 | ⚠️ Degrades (counted in threshold) |
| Sentiment | ✅ Implemented | NSE Option Chain | 0-100 adjusted | ✓ Contributes (10% weight) |
| Regime | ✅ Implemented | NIFTY 50 + VIX | 0-100 VIX-adjusted | ✓ Contributes (20% weight) |

**Current System State**:
- **Active Pillars**: 4/6 (Trend, Momentum, Sentiment, Regime)
- **Placeholder Count**: 2/6 (Volatility, Liquidity)
- **Execution Ready**: ✅ YES (placeholder count ≤ threshold of 2)
- **Conviction Cap**: None (would apply at >2 placeholders, capped at 60%)

---

## 7. EXTERNAL INTEGRATION NOTES

### For Frontend Developers
- Always check `PillarContribution.is_placeholder` before displaying pillar scores
- Display `degradation_warnings` prominently when placeholders are present
- Gate trading UI with `TradeIntent.is_execution_ready` flag
- Use `DirectionalBias` for UI display only (NOT as order direction)

### For Backend Developers
- Implement Volatility & Liquidity pillars before removing placeholder status
- Maintain deterministic pillar behavior (no randomness)
- All new pillars must follow `BasePillar` interface
- Update `ReasoningEngine.placeholder_pillars` when implementing new logic

### For Risk/Compliance Teams
- Current system produces recommendations with 67% typical conviction
- 2 of 6 analytical dimensions are placeholders (disclosed in warnings)
- System enforces execution readiness threshold (blocks if >2 placeholders fail)
- All outputs are non-binding opinions (no automatic execution)

---

**Document Version**: 1.0  
**Schema Version**: TradeIntent v1.0.0  
**Last Updated**: 2025-12-22  
**Maintained By**: Fortune Trading Platform Architecture Team
