# SaaS Migration Task List

## 🟢 Phase 1: Backend API Expansion (FastAPI)
- [x] **Infrastructure Setup**
    - [x] Create `backend/app/api/v1/endpoints/market.py`
    - [x] Create `backend/app/api/v1/endpoints/derivatives.py`
    - [x] Create `backend/app/api/v1/endpoints/insider.py`
    - [x] Create `backend/app/api/v1/endpoints/technicals.py`
    - [x] Register new routers in `backend/app/api/v1/router.py`

- [x] **Market Data Endpoints (`market.py`)**
    - [x] Implement `GET /market/breadth` → `nse_utils.get_advance_decline()`
    - [x] Implement `GET /market/activity/volume` → `nse_utils.most_active_equity_stocks_by_volume()`
    - [x] Implement `GET /market/activity/value` → `nse_utils.most_active_equity_stocks_by_value()`
    - [x] Implement `GET /market/indices` → `yfinance` (Existing but needs hardening)

- [x] **Derivatives Endpoints (`derivatives.py`)**
    - [x] Implement `GET /derivatives/option-chain/{symbol}` → `nse_utils.get_option_chain(symbol)`
    - [x] Implement `GET /derivatives/futures/{symbol}` → `nse_utils.futures_data(symbol)`
    - [x] Implement `GET /derivatives/pcr/{symbol}` (Put-Call Ratio)

- [x] **Insider & Corporate Endpoints (`insider.py`)**
    - [x] Implement `GET /insider/trades` → `nse_utils.get_insider_trading(from_date, to_date)`
    - [x] Implement `GET /insider/bulk-deals` → `nse_utils.get_bulk_deals(from_date, to_date)`
    - [x] Implement `GET /insider/block-deals` → `nse_utils.get_block_deals(from_date, to_date)`
    - [x] Implement `GET /insider/short-selling` → `nse_utils.get_short_selling(from_date, to_date)`

- [x] **Technical Analysis Endpoints (`technicals.py`)**
    - [x] Implement `GET /technicals/indicators/{symbol}` → Fetch History -> `TechnicalAnalysisService(df).calculate_all()`
    - [x] Implement `GET /technicals/intraday/{symbol}` → `NSEMasterData.get_history(symbol, interval='1m')`

## 🟡 Phase 2: Frontend Setup (Next.js 14)
- [x] **Initialization**
    - [x] Initialize Next.js project in `frontend-new/`
    - [x] Configure TailwindCSS
    - [x] Configure Shadcn/UI components
    - [x] Setup API Client (Axios/React Query)

- [x] **Core Pages & Layouts**
    - [x] Create App Layout (Sidebar, Header, Theme Toggle)
    - [x] Create Dashboard Page (`/dashboard`)
    - [x] Create Stock Analysis dynamic page (`/stock/[symbol]`)

## 🔵 Phase 3: Frontend Feature Implementation
- [x] **Dashboard Widgets**
    - [x] Market Pulse Cards (Indices)
    - [x] Top Gainers/Losers Ticker
    - [x] Market Breadth Widget with Advance/Decline Ratio

- [x] **Stock Analysis Tabs**
    - [x] **Overview Tab**: Price Chart, Key Metrics, Corp Actions
    - [x] **Technical Tab**: Intraday Chart, Indicators Table (50+ indicators)
    - [x] **Derivatives Tab**: Option Chain Heatmap, PCR Chart, Futures Display
    - [x] **Insider Tab**: Insider Trades Table, Bulk Deals, Block Deals

## 🟣 Phase 4: Integration & Polish
- [ ] **End-to-End Testing**
    - [ ] Verify Data Flow (Backend -> Frontend)
    - [ ] Check Intraday Chart performance
- [ ] **Deployment Prep**
    - [ ] optimize Dockerfile for Next.js
    - [ ] Finalize Documentation
