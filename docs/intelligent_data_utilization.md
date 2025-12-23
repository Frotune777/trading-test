# 🧠 Intelligent Data Utilization & Reasoning Design

This document defines how the Fortune Trading QUAD System utilizes market data for intelligent reasoning, ensuring a clean separation between data ingestion and decision logic.

## 1️⃣ Data Tiering (Access Paths)

All available data domains are classified to optimize processing and minimize "analysis paralysis" in live environments.

| TIER | PATH NAME | LATENCY / REFRESH | USAGE | DATA DOMAINS |
| :--- | :--- | :--- | :--- | :--- |
| 🔥 | **HOT PATH** | < 1 min (Tick/Snapshot) | Triggering entry/exit, trailing stops | LTP, L2 Depth, OI Change, Greeks (Delta/Gamma) |
| 🌤️ | **WARM PATH** | 5m - 60m (Contextual) | Confidence scoring, signal filtering | VIX, Adv/Dec, VWAP, Bulk Deals, Trend confirmation |
| ❄️ | **COLD PATH** | Daily / Quarterly | Backtesting, ML Feature pipeline | P&L, BS, Cash Flow, Shareholding, Insider History |

---

## 2️⃣ Canonical Reasoning Objects

The reasoning engine interacts with these standardized objects, never with raw data source responses.

### A. `LiveDecisionSnapshot` (Unit of Decision)
*Produced per symbol, per analysis cycle.*
- **PriceState**: `{ltp, vwap, spread, tick_direction}`
- **LiquidityState**: `{bid_ask_ratio, depth_concentration, vol_spike_ratio}`
- **DerivativeGreeks**: `{delta_exposure, gamma_wall, theta_decay_risk}`
- **ConfidenceScore**: 0-100 (Derived from WARM path filters)

### B. `SessionContext` (Market Environment)
*Produced once per session header or on major regime shifts.*
- **MarketRegime**: `[BULLISH, BEARISH, VOLATILE, SIDEWAYS]`
- **GlobalVIX**: Current volatility percentile.
- **BreadthState**: Advance/Decline ratio + Index Momentum.
- **InstitutionalBias**: Net FII/DII flow (Day-to-date).

### C. `ResearchStore` (Cold Storage)
- Historical OHLCV (Adjusted).
- Multi-year financial tables.
- Standardized metadata scrip master.

---

## 3️⃣ QUAD Intelligence Influence Mapping

| QUAD PILLAR | HOT PATH (Execution) | WARM PATH (Conviction) | COLD PATH (Strategy Fit) |
| :--- | :--- | :--- | :--- |
| **TREND** | Price Breakouts | Moving Average Anchoring | Multi-year channel alignment |
| **MOMENTUM** | RSI Velocity, Vol Spikes | Advance/Decline confirmation| Quarterly Growth CAGR |
| **VOLATILITY** | Spread expansion, IV Skew| India VIX percentile | Historical IV Median |
| **LIQUIDITY** | L2 Depth, Bid/Ask skew | Block Deal spikes | Average Daily Volume (ADV) |
| **SENTIMENT** | OI Spikes, PCR Change | FII/DII activity, News tone| Insider Trading disclosures |
| **REGIME** | *N/A* | VIX + Breadth + Sector Rot. | Macro Cycles / Industry ROE |

---

## 4️⃣ OpenAlgo Forward-Compatibility Interface

To ensure Phase 2 integration requires **Zero Refactoring**, the reasoning engine uses an **Abstraction Interface**:

```python
class IMarketDataProvider(ABC):
    @abstractmethod
    def get_live_snapshot(self, symbol: str) -> LiveDecisionSnapshot:
        """Currently calls UnifiedDataService; will call OpenAlgo in P2"""
        pass

    @abstractmethod
    def get_session_context(self) -> SessionContext:
        """Currently calls MarketRegime Service; will call OpenAlgo Feed in P2"""
        pass
```

### Constraints for Phase 2:
- **No Hallucination**: If Greeks aren't provided by the feed, the model must degrade to "Price Only" mode with reduced Confidence.
- **Identity Abstraction**: All logic uses `InstrumentUID`. The mapper handles `NSE:RELIANCE` vs `RELIANCE.NS`.
- **Execution Agnostic**: The Reasoning Agent only outputs `TradeIntent`. The *OpenAlgo Broker Bridge* handles the actual Order implementation.

---

## ⚠️ Graceful Degradation Logic

If critical data is missing, the Reasoning Agent must explicitly downgrade the decision:
- **Missing L2 Depth**: Falls back to "N/A" metrics; Logic degrades to neutral/historical scores.
- **Missing Option Chain**: Falls back to "N/A" metrics; Sentiment Pillar returns Neutral.
- **Missing Fundamentals**: Strategy restricted to "Day Trading" only; Carry-forward prohibited.
