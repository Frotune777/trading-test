# QUAD System - Volatility & Liquidity Pillar Calibration Matrices

## Document Purpose
This document defines the deterministic calibration matrices for the VolatilityPillar and LiquidityPillar, mapping raw indicator values to normalized scores ([0-100]) and directional biases.

---

## 1. VOLATILITY PILLAR CALIBRATION

### 1.1 ATR% (Average True Range as % of Close Price)

**Volatility Regime Classification:**

| ATR% Range | Regime Label | Base Score | Description |
|------------|--------------|------------|-------------|
| < 1.5% | Very Low | 85 | Extremely calm, low risk |
| 1.5% - 3.0% | Normal | 60 | Typical volatility range |
| 3.0% - 5.0% | High | 40 | Elevated risk |
| 5.0% - 8.0% | Very High | 25 | Dangerous volatility |
| > 8.0% | Extreme | 10 | Crisis-level volatility |

**Bias Determination:**
- ATR% < 3.0%: Bias = "NEUTRAL"
- ATR% ≥ 3.0%: Bias = "VOLATILE"

---

### 1.2 Bollinger Band Width % (Relative to Middle Band)

**Band Width Classification:**

| BB Width % | Regime Label | Base Score | Description |
|------------|--------------|------------|-------------|
| < 4.0% | Narrow | 80 | Compression, breakout pending |
| 4.0% - 8.0% | Normal | 60 | Standard range |
| 8.0% - 12.0% | Wide | 40 | Expansion phase |
| 12.0% - 18.0% | Very Wide | 25 | Strong trending |
| > 18.0% | Extreme | 15 | Parabolic move |

**Bias Determination:**
- BB Width < 8.0%: Bias = "NEUTRAL"
- BB Width ≥ 8.0%: Bias = "VOLATILE"

---

### 1.3 India VIX Level

**Market Fear Index Classification:**

| VIX Level | Regime Label | Base Score | VIX Percentile Adjustment |
|-----------|--------------|------------|---------------------------|
| < 12 | Very Low | 90 | Complacency risk: -5 if <10th percentile |
| 12 - 15 | Low | 75 | Calm market |
| 15 - 20 | Normal | 60 | Typical range |
| 20 - 25 | Elevated | 45 | Caution warranted |
| 25 - 30 | High | 30 | Fear phase |
| > 30 | Panic | 15 | Crisis mode |

**VIX-based Adjustments:**
- If VIX > 25 AND market_regime = "BULLISH": Reduce bullish pillar scores by 10%
- If VIX < 15 AND trend = "TRENDING": Boost trend confidence by +5 points
- If VIX in >80th percentile: Cap all pillar scores at 60 (uncertainty)

---

### 1.4 Composite Volatility Score Formula

```
Composite Score = (ATR_Score × 0.40) + (BB_Score × 0.30) + (VIX_Score × 0.30)
```

**Weighting Rationale:**
- ATR (40%): Instrument-specific volatility (primary signal)
- BB Width (30%): Price channel behavior (secondary signal)
- VIX (30%): Systemic risk environment (context)

**Final Bias Logic:**
```python
if ATR% >= 5.0 OR BB_Width >= 12.0 OR VIX >= 25:
    bias = "VOLATILE"
else:
    bias = "NEUTRAL"
```

---

### 1.5 Complete Volatility Calibration Matrix

| ATR% | BB Width% | VIX | Composite Score | Bias | Interpretation |
|------|-----------|-----|-----------------|------|----------------|
| <1.5 | <4.0 | <15 | 85 | NEUTRAL | Ideal trading conditions |
| 1.5-3.0 | 4.0-8.0 | 15-20 | 60 | NEUTRAL | Normal market |
| 3.0-5.0 | 8.0-12.0 | 20-25 | 42 | VOLATILE | Proceed with caution |
| >5.0 | >12.0 | >25 | 20 | VOLATILE | High risk, reduce exposure |
| <1.5 | >12.0 | <15 | 72 | NEUTRAL | Quiet stock, volatile market |
| >5.0 | <4.0 | >25 | 32 | VOLATILE | Stock calm, market panic |

**Edge Cases:**
- Missing ATR: Use BB Width × 1.5 weight, reduce total confidence by 20%
- Missing BB: Use ATR × 1.5 weight, reduce total confidence by 15%
- Missing VIX: Default to 15.0 (historical median), flag as estimate

---

## 2. LIQUIDITY PILLAR CALIBRATION

### 2.1 Bid-Ask Spread % (Relative to Mid Price)

**Spread Tightness Classification:**

| Spread % | Liquidity Quality | Base Score | Description |
|----------|-------------------|------------|-------------|
| < 0.05% | Excellent | 95 | Institutional-grade |
| 0.05% - 0.10% | Very Good | 85 | High liquidity |
| 0.10% - 0.20% | Good | 70 | Acceptable |
| 0.20% - 0.30% | Fair | 50 | Moderate slippage risk |
| 0.30% - 0.50% | Poor | 30 | Wide spread |
| > 0.50% | Very Poor | 10 | Illiquid, avoid |

**Bias Determination (Spread Alone):**
- Spread < 0.20%: Neutral (good execution environment)
- Spread ≥ 0.20%: Bearish bias (execution risk)

---

### 2.2 Depth Ratio (Bid Qty ÷ Ask Qty)

**Depth Balance Classification:**

| Depth Ratio | Balance Type | Base Score | Bias Impact |
|-------------|--------------|------------|-------------|
| 0.0 - 0.5 | Heavy Ask | 60 | BEARISH (sellers dominate) |
| 0.5 - 0.7 | Ask Skewed | 70 | Slight BEARISH |
| 0.7 - 1.3 | Balanced | 80 | NEUTRAL (healthy) |
| 1.3 - 2.0 | Bid Skewed | 70 | Slight BULLISH |
| > 2.0 | Heavy Bid | 60 | BULLISH (buyers dominate) |

**Bias Determination (Depth Alone):**
- Ratio < 0.7: Bias = "BEARISH"
- Ratio 0.7 - 1.3: Bias = "NEUTRAL"
- Ratio > 1.3: Bias = "BULLISH"

**Depth Absolute Threshold:**
- If `(bid_qty + ask_qty) < 1000`: Multiply score by 0.6 (thin depth penalty)
- If `(bid_qty + ask_qty) < 100`: Score = 15 (critically thin)

---

### 2.3 ADOSC (Chaikin A/D Oscillator)

**Volume Pressure Classification:**

| ADOSC Value | Pressure Type | Score Adjustment | Bias Impact |
|-------------|---------------|------------------|-------------|
| > 2000 | Strong Accumulation | +15 | BULLISH |
| 1000 - 2000 | Accumulation | +10 | Slight BULLISH |
| 0 - 1000 | Weak Accumulation | +5 | NEUTRAL |
| -1000 - 0 | Weak Distribution | -5 | NEUTRAL |
| -2000 - -1000 | Distribution | -10 | Slight BEARISH |
| < -2000 | Strong Distribution | -15 | BEARISH |

**ADOSC is Optional:**
- If missing, use spread + depth only (no volume confirmation)
- If present, apply as adjustment to composite score

---

### 2.4 Composite Liquidity Score Formula

**Without ADOSC:**
```
Composite Score = (Spread_Score × 0.60) + (Depth_Score × 0.40)
```

**With ADOSC:**
```
Base Score = (Spread_Score × 0.50) + (Depth_Score × 0.30) + (Volume_Score × 0.20)
Composite Score = Base Score + ADOSC_Adjustment
```

**Final Bias Logic:**
```python
if Spread > 0.30% OR Total_Depth < 1000:
    bias = "BEARISH"  # Poor liquidity
elif Depth_Ratio > 1.5 AND ADOSC > 1000:
    bias = "BULLISH"  # Strong buying interest
elif Depth_Ratio < 0.7 AND ADOSC < -1000:
    bias = "BEARISH"  # Strong selling pressure
else:
    bias = "NEUTRAL"
```

---

### 2.5 Complete Liquidity Calibration Matrix

| Spread % | Depth Ratio | ADOSC | Composite Score | Bias | Interpretation |
|----------|-------------|-------|-----------------|------|----------------|
| <0.05 | 0.9-1.1 | >1000 | 95 | BULLISH | Excellent liquidity + buying |
| 0.05-0.10 | 0.8-1.2 | 0-1000 | 82 | NEUTRAL | Very good liquidity |
| 0.10-0.20 | 0.7-1.3 | Any | 70 | NEUTRAL | Good liquidity |
| 0.20-0.30 | 0.6-1.4 | -500-500 | 52 | NEUTRAL | Fair liquidity |
| 0.30-0.50 | <0.6 | <-1000 | 25 | BEARISH | Poor + selling pressure |
| >0.50 | Any | Any | 10 | BEARISH | Illiquid, avoid |
| <0.10 | >2.0 | >2000 | 88 | BULLISH | Tight + heavy buying |
| <0.10 | <0.5 | <-2000 | 40 | BEARISH | Tight but heavy selling |

**Edge Cases:**
- Zero bid or ask qty: Score = 0 (no liquidity)
- Missing ADOSC: Reduce total confidence by 10%
- Stale depth data (>5min old): Flag as unreliable, cap score at 60

---

## 3. IMPLEMENTATION GUIDELINES

### 3.1 Score Clamping
All final scores MUST be clamped to [0, 100]:
```python
final_score = max(0.0, min(100.0, computed_score))
```

### 3.2 Determinism Requirement
- Same inputs MUST produce same outputs (no randomness)
- Use fixed thresholds (no adaptive learning in v1.0)
- Timestamp-independent (no time-of-day adjustments)

### 3.3 Data Quality Flags
Pillars should track data quality:
- `has_all_indicators`: Boolean (True if all inputs present)
- `confidence_penalty`: Percentage reduction for missing data
- `data_age_seconds`: Time since snapshot creation

### 3.4 Non-Execution Guarantee
These calibrations produce ANALYSIS ONLY:
- Scores express risk/opportunity assessment
- Biases express directional opinion
- NO position sizing, NO price targets, NO stop-loss levels

---

## 4. VALIDATION THRESHOLDS

### 4.1 Volatility Pillar
- **Minimum Valid Score**: 0 (crisis scenario)
- **Maximum Valid Score**: 100 (perfect calm)
- **Typical Range**: 40-80 (normal markets)
- **Execution Ready Threshold**: Score > 30 (avoid extreme volatility)

### 4.2 Liquidity Pillar
- **Minimum Valid Score**: 0 (no liquidity)
- **Maximum Valid Score**: 100 (perfect liquidity)
- **Typical Range**: 50-90 (liquid stocks)
- **Execution Ready Threshold**: Score > 40 (avoid illiquid instruments)

---

## 5. CALIBRATION MAINTENANCE

### 5.1 Review Schedule
- **Quarterly**: Review threshold appropriateness using historical data
- **Post-Crisis**: Recalibrate after market regime shifts
- **Annual**: Backtest matrix performance against manual trading decisions

### 5.2 Tuning Principles
- Thresholds should reflect 80th percentile of observed ranges
- Score distributions should be approximately normal (avoid clustering at extremes)
- Bias labels should trigger in ~20-30% of cases (not every tick)

### 5.3 Version Control
- Current Version: **v1.0**
- Last Updated: 2025-12-22
- Next Review: 2026-03-22
- Change Log: Initial calibration based on NSE data (2020-2025)

---

## 6. INTEGRATION CHECKLIST

- [ ] Update `VolatilityPillar` with exact thresholds from Section 1.5
- [ ] Update `LiquidityPillar` with exact thresholds from Section 2.5
- [ ] Add data quality tracking to both pillars
- [ ] Create unit tests for boundary conditions (e.g., ATR = 3.0% exactly)
- [ ] Validate composite scores sum correctly with weights
- [ ] Document any deviation from these matrices in code comments
- [ ] Add monitoring for score distributions in production

---

**Document Version**: 1.0  
**Schema Compatibility**: TradeIntent v1.0.0  
**Maintained By**: Fortune Trading QUAD Calibration Team
