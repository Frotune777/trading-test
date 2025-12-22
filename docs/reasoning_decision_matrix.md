# 🎯 Reasoning Decision Matrix

This matrix defines the EXACT influence of each data category on the final `TradeIntent`. The Reasoning Engine uses this to weight signals and calculate position sizing.

---

## 🚦 Decision Impact Mapping

| DATA CATEGORY | IMPACTS: **DIRECTION** | IMPACTS: **CONFIDENCE** | IMPACTS: **RISK / SIZE** |
| :--- | :---: | :---: | :---: |
| **Price Action (LTP)** | ✅ Primary | ❌ No | ❌ No |
| **Trend (MA / SuperTrend)** | ✅ Primary | ✅ Confirmation | ❌ No |
| **Volatility (VIX)** | ❌ No | ✅ High | ✅ Primary (Scale-down) |
| **Volume Spikes** | ❌ No | ✅ Velocity | ✅ Scalp-only |
| **Option Greeks (Delta)** | ✅ Bias | ✅ High | ✅ Directional Exposure |
| **Option Greeks (Gamma)** | ❌ No | ✅ Low | ✅ Hedging required |
| **L2 Depth (Skew)** | ❌ No | ✅ Execution timing | ✅ Micro-sizing |
| **Insider Buying** | ❌ No | ✅ Pos. Long-term Bias| ✅ Position Sizing |
| **FII / DII Net Flow** | ❌ No | ✅ Regime Fit | ✅ High |
| **Quarterly Growth %** | ❌ No | ✅ Structural Fit | ✅ Portfolio Allocation|

---

## ⚖️ Trade-Off Rules

### 1. Directional Conflict
- **Conflict**: Trend is Bullish (Price), but Option Sentiment is Bearish (OI/PCR).
- **Rule**: No Trade. Confidence < 30%.
- **Reason**: Derivatives lead Price. Price-only breakouts without OI support are "Bull Traps".

### 2. Confidence vs. Risk Scaling
- **Rule**: Risk (Position Size) is a function of `SessionContext.Confidence`.
- **Logic**: 
  - Confidence > 80%: Full Position (1x).
  - Confidence 50-80%: Half Position (0.5x).
  - Confidence < 50%: Observation only (0x).

### 3. Missing Data Degradation
- If **VIX** is `@UNKNOWN`: Cap all trades at 25% risk.
- If **Order Book** is `@UNKNOWN`: Prohibit Entry within 5 mins of market open/close.

---

## 🧩 Canonical Reasoning Flow

1.  **Poll `SessionContext`**: Determine if the day is "Playable" (Regime Filter).
2.  **Monitor `LiveDecisionSnapshot`**: Identify Trigger (HOT Path).
3.  **Evaluate WARM Context**: Calculate `ConfidenceScore` (Confirm Trend/Momentum/Sentiment).
4.  **Check COLD Alignment**: Ensure scrip quality (ROE/Growth).
5.  **Output `TradeIntent`**: `{Action, Symbol, QuantityFactor, StopLoss, Target}`.

---

## 🚀 Phase 2 Ready
The logic above does not care *how* the Greeks or Price are fetched. Whether it's a legacy scraper or the **OpenAlgo WebSocket**, the `DecisionSnapshot` structure remains constant.
