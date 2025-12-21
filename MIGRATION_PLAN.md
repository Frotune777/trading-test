# SaaS Frontend Redesign & Migration Plan

## Executive Summary
The goal is to transition the current monolithic Streamlit application into a professional, scalable **Data-as-a-Service (SaaS)** architecture. This involves decoupling the frontend into a **Next.js 14** application and significantly expanding the **FastAPI** backend to expose all data pillars (Derivatives, Insider, Technicals) currently locked in Python logic or direct database access.

## 1. Architecture Shift
| Component | Current State | Target State |
|-----------|---------------|--------------|
| **Frontend** | Streamlit (Python, Server-side rendering) | **Next.js 14** (React, Client-side interactivity, TailwindCSS) |
| **Backend** | Direct DB Access via `db_manager.py` | **FastAPI** REST Layer (Data only, no logic leak) |
| **State** | Session State (Transient) | **React Query** (Server state) + **Zustand** (Client state) |
| **Styling** | Custom CSS injections | **TailwindCSS** + **Shadcn/UI** (Professional Component Library) |

---

## 2. API Expansion Plan (Backend)
The current API (`v1/endpoints/`) is insufficient. We must create new routers to expose the `NseUtils` and `NSEMasterData` capabilities.

### Phase 2.1: New API Endpoints
- **`v1/endpoints/market.py` for Generic Market Data**
    - `GET /market/breadth` → `nse_utils.get_advance_decline()`
    - `GET /market/activity/volume` → `nse_utils.most_active_equity_stocks_by_volume()`
    - `GET /market/indices` → `yfinance` (Existing but needs hardening)

- **`v1/endpoints/derivatives.py` for F&O**
    - `GET /derivatives/option-chain/{symbol}` → `nse_utils.get_option_chain()`
    - `GET /derivatives/futures/{symbol}` → `nse_utils.futures_data()`
    - `GET /derivatives/pcr/{symbol}` → Computed PCR from option chain.

- **`v1/endpoints/insider.py` for Smart Money**
    - `GET /insider/trades` → `nse_utils.get_insider_trading()`
    - `GET /insider/bulk-deals` → `nse_utils.get_bulk_deals()`
    - `GET /insider/block-deals` → `nse_utils.get_block_deals()`
    - `GET /insider/short-selling` → `nse_utils.get_short_selling()`

- **`v1/endpoints/technicals.py` for Charts**
    - `GET /technicals/indicators/{symbol}` → `TechnicalAnalysisService.analyze()`
    - `GET /technicals/intraday/{symbol}?interval=5m` → `NSEMasterData.get_history()` (For interactive charts)

---

## 3. Frontend Implementation Plan (Next.js)

### Phase 3.1: Setup & Foundations
- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS (Utility-first)
- **Components**: Shadcn/UI (Radix UI based, accessible, highly professional look)
- **Charts**: Recharts (Responsive, clean D3 wrapper) or Lightweight-Charts (TradingView style)
- **State/Fetching**: TanStack Query (React Query) for robust data fetching/caching.

### Phase 3.2: Page Structure
1.  **Dashboard (`/dashboard`)**:
    - "Market Pulse" Cards (Nifty/BankNifty Status).
    - Top Gainers/Losers Ticker.
    - User's Watchlist (Local Storage or DB).
2.  **Stock Analysis (`/stock/[symbol]`)**:
    - **Header**: Live Price, Change, Sparkline.
    - **Tabs**:
        - **Overview**: Key Metrics, Price Chart (Daily), Corporate Actions.
        - **Technical**: TradingView-style Chart (Intraday), Indicators Table (RSI/MACD signals).
        - **Derivatives**: Option Chain Visualization (Heatmap), OI Analysis Charts.
        - **Fundamentals**: Quarterly/Annual P&L Bar Charts, Shareholding Pie Charts.
        - **Insider**: Table of recent Promoter/Insider trades.
3.  **Screener (`/screener`)**:
    - Filterable table based on Database Snapshot.
4.  **Reports (`/reports`)**:
    - Smart Score Leaderboard.

### Phase 3.3: Professional UX Features
- **Dark/Light Mode**: First-class support via `next-themes`.
- **Skeleton Loading**: No spinning wheels; use pulsating UI skeletons.
- **Command Palette (`Cmd+K`)**: for fast navigation to any stock.
- **Responsive Mobile View**: Bottom navigation bar for mobile.

---

## 4. Execution Roadmap
1.  **Backend First**: Create `market.py`, `derivatives.py`, `insider.py` routers and register them.
2.  **Verify Data**: Use Curl/Postman to ensure JSON responses are clean.
3.  **Frontend Init**: `npx create-next-app` with TypeScript/Tailwind.
4.  **Component Build**: Create reusable `StockCard`, `MetricBadge`, `DataTable`.
5.  **Integration**: Connect Frontend to Backend APIs.
