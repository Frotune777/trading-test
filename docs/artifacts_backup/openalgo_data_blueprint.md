# Data Architecture & OpenAlgo Modeling Blueprint

This blueprint serves as a foundational architecture to align the "Fortune Trading QUAD System" with the [OpenAlgo](https://openalgo.io) framework. 

**Status**: Exhaustive Audit Complete. The model now abstracts:
- **Intraday Depth**: Greeks, Order Books, VWAP.
- **Institutional Context**: Bulk/Block/Insider activity.
- **Deep Financials**: P&L, Balance Sheet, Cash Flow (Crore-normalized).
- **Static Metadata**: ISIN, Lot Sizes, Expiries.

---

## 1️⃣ Data Source Inventory

| Source Name | Type | Coverage | Reliability | Role in System |
| :--- | :--- | :--- | :--- | :--- |
| `yfinance` | REST (API) | Historical OHLCV, basic metrics | High | Primary Historical Engine |
| `NSEMasterData`| REST (API) | Tick-accurate OHLCV, Master Scrips | High | Primary Intraday/Historical Fallback |
| `ScreenerEnhanced`| REST (Scraper)| Deep Financials/P&L/Shareholding | Very High | **Authoritative** Financial Database |
| `NseUtils` | REST (API) | Live Options, Order Book, Institutional | Medium | **Authoritative** for Live Depth & Greeks |
| `nselib` | Python Lib | BhavCopy, Breadth, Corp actions | Very High | **Authoritative** for EOD Adjustments & Delivery |

---

## 2️⃣ Canonical Market Data Model (OpenAlgo Compatible)

The model is expanded into four distinct "Contexts" to support advanced OpenAlgo logic:

### A. Identity & Profile (Static)
- `isin`, `listing_date`, `lot_size`, `tick_size`.
- **Peer Mapping**: Industry-specific tags to support relative strength analysis.

### B. Dynamic Depth (Live)
- **The Greeks**: Delta, Gamma, Theta, Vega, Rho (calculated from `NseUtils` IV).
- **L2 Order Book**: Top 5 Bid/Ask layers for slippage estimation.
- **VWAP Discovery**: Real-time anchoring for mean-reversion signals.

### C. Institutional Flow (Context)
- **Bulk/Block Tracking**: Real-time detection of high-volume non-market transactions.
- **Delivery Analysis**: Cross-referencing price moves with high delivery % from `BhavCopy` to confirm "Smart Money" moves.
- **Insider Activity**: Bias detection from Promoter buying/selling.

### D. Deep Fundamentals (Value)
- **Financial Health**: Debt-to-Equity, Interest Coverage, Cash Flow stability.
- **Growth Vectors**: Sequential Sales/Profit growth from Quarterly tables.
- **Shareholding Health**: Tracking Pledge %, FII/DII entry/exit.

---

## 3️⃣ Data Pull & Fallback Matrix (Refined)

| DATA TYPE | PRIMARY | FALLBACK | FREQUENCY |
| :--- | :--- | :--- | :--- |
| **OHLCV** | `NSEMaster` | `yfinance` | Continuous |
| **Delivery Data** | `BhavCopy` | `Screener` | EOD (After 6:30 PM) |
| **Greeks / Chain** | `NseUtils` | *N/A* (Manual) | 1-min / 5-min |
| **P&L / BS / CF** | `Screener` | `yfinance` | Quarterly |
| **Institutional** | `NseUtils` | `NSE CSV Archives`| Intra-day snapshots |

> [!NOTE]
> **Cascading Ingestion**: The `UnifiedDataService` checks for data existence in the Primary source. If `null` or empty, it automatically triggers the Fallback source before passing data to the **Normalization Layer**.

---

## 4️⃣ Normalization & Identity Table (XREF)

To maintain compatibility with OpenAlgo, a **Cross-Reference (XREF) Table** is maintained in-process (and persisted in `data_sources` metadata):

| Standard Symbol | `yfinance` Suffix | `NSE` Symbol | `Screener` URL Slug |
| :--- | :--- | :--- | :--- |
| `RELIANCE` | `RELIANCE.NS` | `RELIANCE` | `RELIANCE` |
| `NIFTY_50` | `^NSEI` | `NIFTY 50` | `indices/NIFTY-50` |

The **Normalization Layer** (`DataNormalizer`) ensures that regardless of the source, the output dictionary always complies with the `StandardSchema`.

The following entities follow OpenAlgo's abstraction layer.

### Instrument (Identity)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `symbol` | STRING | ✅ | Canonical identifier (e.g., `RELIANCE`) |
| `exchange` | STRING | ✅ | `NSE`, `BSE`, `MCX` |
| `instrument_type` | ENUM | ✅ | `EQUITY`, `FUTURES`, `OPTIONS`, `INDEX` |
| `token` | STRING | ❌ | Exchange-specific instrument ID |
| `expiry` | DATE | ⚠️ | Required for FUT/OPT |
| `strike` | FLOAT | ⚠️ | Required for OPT |
| `option_type` | ENUM | ⚠️ | `CE`, `PE` |
| `lot_size` | INTEGER | ✅ | Minimum trading unit |

### Market Data (Time-Series)
| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | DATETIME | ISO 8601 (UTC/IST handle) |
| `open` | FLOAT | |
| `high` | FLOAT | |
| `low` | FLOAT | |
| `close` | FLOAT | Last Price (LTP) if snapshot |
| `volume` | INTEGER | |
| `oi`| INTEGER | Open Interest (Derivatives only) |

---

## 4️⃣ Data Normalization Strategy

To ensure OpenAlgo can plug in without schema changes, we adopt a **normalization-first** approach:

1.  **Symbol Identity Preservation**: 
    - Internal ID: `NSE:RELIANCE`
    - yfinance mapping: `RELIANCE.NS`
    - OpenAlgo mapping: `NSE_EQ:RELIANCE` (example)
2.  **Date/Time Consistency**:
    - All storage in UTC.
    - Application layer converts to `IST` (UTC+5:30) for display.
3.  **Raw vs Derived Data**:
    - **RAW Store**: All incoming JSON/CSV from NSE is persisted as-is in `custom_metrics` (EAV pattern).
    - **Canonical Store**: Normalized OHLCV goes into `price_history` and `intraday_prices`.
4.  **Precision**:
    - Prices rounded to 2 decimal places (or 0.05 tick size for NSE).

---

## 5️⃣ OpenAlgo Phase-2 Integration Plan

OpenAlgo will be integrated as a **Broker Abstraction Layer**.

### Integration Touchpoints:
1.  **Data Ingestion**: Replace `yfinance` polling with OpenAlgo's WebSocket/Feed handlers for real-time tickers.
2.  **Order Execution**: The `Decision Engine` (D) will send signals to a new `OpenAlgoClient` instead of manual entry.
3.  **State Management**: Use OpenAlgo's position/order tracking instead of custom DB tracking for live trades.

### Zero-Refactor Guarantee Checklist:
- [ ] Schema uses `instrument_type` instead of hardcoded `is_fno`.
- [ ] Analysis services interact with `Instrument` objects, not raw strings.
- [ ] Database supports `timestamp` with timezone.
- [ ] `SignalGenerator` outputs are decoupled from `OrderExecutor`.

---

## 📚 Reference Documentation
For a detailed field-by-field breakdown including data types and sample values, refer to the [Unified Data Dictionary](file:///home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/docs/data_dictionary.md).

