# Frontend vs. Backend Data Gap Analysis

This report highlights the discrepancies between the data available in the backend API (now including `NSEMasterData`, Insider, & Bulk Deals) and what is effectively visualized in the Streamlit Frontend (`frontend/app.py`).

## 🚨 Critical Gaps (High Priority)

### 1. Derivatives (F&O) Module - **COMPLETELY MISSING**
- **Backend Capability:** `NSEDerivatives` and `NseUtils` provide full **Option Chain** (Calls/Puts, OI, IV, Greeks), **Futures Data**, and **FII/DII Activity**.
- **Frontend Status:** No dedicated tab or view. Users cannot see option chains, PCR (Put Call Ratio), or institutional flows.
- **Impact:** Removes a massive pillar of analysis for traders.

### 2. Market Sentiment & Insider Activity - **COMPLETELY MISSING**
- **Backend Capability:** `NseUtils` provides:
    - **Insider Trading** (SAST/PIT Reg 7)
    - **Bulk & Block Deals** (Big money movement)
    - **Short Selling Data**
    - **Market Breadth** (Advances/Declines)
- **Frontend Status:** No "Sentiment" or "Insider" tab. This high-value signal data is hidden from the user.
- **Impact:** Users miss "Smart Money" movements.

### 3. Technical Indicators Visualization - **MISSING**
- **Backend Capability:** `TechnicalAnalysisService` computes **50+ indicators**:
    - Trend: SMA (20, 50, 200), EMA, Supertrend, ADX.
    - Momentum: RSI, MACD, Stochastic, CCI.
    - Volatility: Bollinger Bands, ATR.
- **Frontend Status:** The "Charts" tab (`tab2`) only displays **Price (Candle/Line)** and **Volume**.
- **Gap:** No ability to overlay Moving Averages, Bollinger Bands, or view RSI/MACD sub-charts.

### 4. Interactive Intraday Charts - **MISSING**
- **Backend Capability:** `NSEMasterData` can fetch **1-minute** granularity historical data.
- **Frontend Status:**
    - "Charts" tab only supports **Daily** resolution (1W, 1M, 1Y views are all built on daily data).
    - "Download" tab *does* allow downloading Intraday CSVs, but you cannot *view* them on the chart.
- **Gap:** Users cannot perform intraday analysis (e.g., 5-min candle patterns) despite the backend supporting it.

## ⚠️ Important Gaps (Medium Priority)

### 5. Corporate Actions & Announcements
- **Backend Capability:** `UnifiedDataService` aggregates Dividends, Splits, Bonus issues, and Board Meetings.
- **Frontend Status:** Not displayed.
- **Impact:** Users are blind to upcoming price-adjusting events.

### 6. Detailed Fundamentals
- **Backend Capability:** `ScreenerEnhanced` provides rich data (Cash Flows, Detailed Ratios).
- **Frontend Status:** Displays only basic P&L. Cash Flow Statement is missing.

## ✅ Matched Data (Implemented)
| Data Point | Backend Source | Frontend Location | Status |
|------------|---------------|-------------------|--------|
| **Rank 1 Data** | `NSEComplete` | "Overview" Tab | ✅ **Live** |
| **52W High/Low** | `Unified/Screener` | "Overview" Tab | ✅ **Live** |
| **Peers** | `ScreenerEnhanced` | "Peers" Tab | ✅ **Live** |
| **Shareholding** | `ScreenerEnhanced` | "Overview" | ✅ **Live** |
| **Price History** | `NSEMasterData` | "Charts" Tab | ⚠️ **Partial** (Daily Only) |

## Recommendations
1.  **New "Market Pulse" Tab**: Display FII/DII activity, Market Breadth, and Bulk Deals.
2.  **New "Insiders" Tab**: Show Insider Trading and Shareholding changes.
3.  **Upgrade "Charts" Tab**: Add "Intraday" toggle (using `NSEMasterData` 1m/5m data) and Technical Indicator overlays.
4.  **Add "Derivatives" Tab**: Visualize Option Chain.
