# QUAD Trading Platform: Enhanced Frontend Roadmap

## Overview

**Timeline**: 4 weeks  
**Tech Stack**: Next.js 14, TypeScript, TanStack Query, Zustand, Lightweight Charts  
**Backend API**: 200+ endpoints, 3 WebSocket channels  
**Target**: Production-ready trading dashboard

---

## Phase 1: Foundation, Auth & Global State (Week 1)

### Task 1.1: Project Setup & Core Architecture ⭐
- Initialize Next.js 14 with TypeScript (Strict Mode)
- Configure TanStack Query v5 for API management
- Set up Zustand stores:
  - `useAuthStore` - User session, API keys
  - `useMarketStore` - Prices, WebSocket subscriptions
  - `useRiskStore` - Kill switch, limits, positions
  - `useStrategyStore` - Strategies, active strategy
  - `useAlertStore` - Notifications, system alerts
- Create Private Route wrapper for authenticated pages
- **NEW**: Auto-generate TypeScript types from OpenAPI schema

### Task 1.1.1: Data Source Configuration Page ⭐ **CRITICAL**
- Create `/data-source` page for NSE data configuration
- **Purpose**: Replace yfinance with NSE data ingestion
- **Features**:
  - Symbol selection (NSE stocks)
  - Date range picker (from/to dates)
  - Interval selection (1d, 1h, 15m, etc.)
  - Manual data refresh button (`POST /data/ingest`)
  - Data availability checker (`GET /data/availability/{symbol}`)
  - Last ingestion timestamp display
  - Bulk data ingestion for multiple symbols
- **Backend Integration**:
  - Use existing NSE data scripts
  - Connect to `POST /api/v1/data/ingest` endpoint
  - Display ingestion progress and status
- **UI Components**:
  - Symbol search/autocomplete
  - Date range picker (react-day-picker)
  - Progress bar for bulk ingestion
  - Success/error toast notifications
  - Data availability status table
 
### Task 1.2: Authentication & Identity Management ⭐
- Build Login and Registration forms with Zod validation
- Implement "API Key Generation" flow
  - **Critical**: Add "Copy to Clipboard" + "Download Secret" (keys shown once)
  - Show warning modal about key security
- Create AuthInterceptor to attach `Authorization: Bearer <key>`
- Implement auto-logout on 401 Unauthorized
- **NEW**: Add session timeout warning (30 min idle)

### Task 1.3: Layout & Navigation ⭐
- Build sidebar navigation:
  - Dashboard, Analytics, Strategies, Market Data, Risk Control
  - **NEW**: Data Health, Insider Sentinel, ML Performance
- Implement top navbar with:
  - System Health indicator (polling `GET /health`)
  - **NEW**: Feed Health badge (HEALTHY/DEGRADED/DOWN)
  - **NEW**: Execution Mode toggle (DRY_RUN/LIVE)
  - User menu (profile, API keys, logout)

### Task 1.4: API Client Layer ⭐ **NEW**
- Create typed API client with all 200+ endpoints
- Implement retry logic with exponential backoff
- Add request/response interceptors
- Configure base URL from environment variables
- Add circuit breaker for failing endpoints

### Task 1.5: WebSocket Manager ⭐ **NEW**
- Set up WebSocket connection manager
- Implement auto-reconnection logic
- Create subscription manager for:
  - `ws://localhost:8000/ws/market` - Real-time prices
  - `ws://localhost:8000/ws/alerts` - System alerts
  - `ws://localhost:8000/ws/orders` - Order updates
- Add connection status indicator

---

## Phase 2: Market Data & Real-time Analytics (Week 2)

### Task 2.1: Market Watch & Tickers ⭐
- Build searchable stock list (`GET /stocks/{symbol}`)
- Implement "Price Card" component:
  - Poll `GET /market/{symbol}/ltp` every 2-5 seconds
  - **NEW**: Show LTP freshness indicator (< 5s = green)
  - **NEW**: Show price drift warning if Redis ≠ OpenAlgo
- Integrate Lightweight Charts for `GET /stocks/{symbol}/history`
- Add candlestick, line, and area chart modes

### Task 2.2: QUAD Analytics Dashboard ⭐
- Create "Decision Panel":
  - Input: Q/U/A/D scores
  - Output: BUY/SELL signal + Conviction gauge (0-100)
  - **NEW**: Show pillar radar chart (4-axis)
- Build "ML Prediction" view:
  - **Critical**: Display "Shadow Mode" badge if `shadow_mode: true`
  - Show confidence intervals (lower/upper bounds)
  - Display model accuracy percentage
- Develop "Decision History" table:
  - Filter by symbol, date, signal
  - Export to CSV functionality

### Task 2.3: Regime Detection Visualization ⭐ **NEW**
- Create regime indicator badge:
  - TRENDING_UP (green), TRENDING_DOWN (red)
  - RANGING (yellow), VOLATILE (orange)
- Show regime-specific TA weights
- Display regime change alerts

### Task 2.4: TA Aggregator Dashboard ⭐ **NEW**
- Build composite TA signal panel:
  - Trend score, Momentum score, Volatility score, Volume score
  - Weighted composite score with confidence
- Show indicator breakdown (SMA, RSI, MACD, etc.)
- Display regime-aware weighting

### Task 2.5: Conviction Timeline ⭐ **NEW**
- Implement time-series chart (`GET /quad-analytics/{symbol}/timeline`)
- Show conviction evolution over time
- Highlight signal changes (BUY → SELL)
- Add zoom and pan controls

---

## Phase 3: Strategy Management & Execution (Week 3)

### Task 3.1: Strategy CRUD & Builder ⭐
- Create list view for all strategies (`GET /strategy`)
- Build "Strategy Creator" form:
  - Name, Description, Type (technical/fundamental/hybrid)
  - Time windows (start_time, end_time)
  - Symbol mappings
- Implement "Toggle Strategy" switch (`POST /strategy/{id}/toggle`)
- Add strategy duplication feature

### Task 3.2: Execution & Order Workflow ⭐
- Build "Order Entry" modal:
  - Action (BUY/SELL), Quantity, Order Type (MARKET/LIMIT)
  - Strategy selection dropdown
- Implement "Dry Run" confirmation screen:
  - **Critical**: Display `risk_checks` results from backend
  - Show estimated price and total value
  - Require explicit confirmation
- Build "Action Center":
  - Show active positions
  - Display reconciliation status
  - **NEW**: Show broker vs internal state discrepancies

### Task 3.3: Strategy DSL Code Editor ⭐ **NEW**
- Integrate Monaco Editor for custom Python strategies
- Implement syntax highlighting and validation
- Add code templates (SMA Crossover, RSI Mean Reversion)
- Show dangerous code warnings (import os, exec, eval)
- Add "Test Strategy" button with validation feedback

### Task 3.4: Backtest Visualization ⭐ **NEW**
- Create backtest results dashboard:
  - Equity curve chart
  - Drawdown chart
  - Performance metrics (Sharpe, Sortino, Max DD)
  - Trade list with entry/exit points
- Add comparison mode (compare 2+ strategies)
- Export backtest report to PDF

---

## Phase 4: Risk Control, Alerts & Optimization (Week 4)

### Task 4.1: The Risk Command Center ⭐
- Build high-visibility "Risk Dashboard":
  - Total P&L (daily, weekly, all-time)
  - Position count vs limit (progress bar)
  - Concentration risk (pie chart)
  - Daily loss vs limit (progress bar)
- Implement Emergency Kill Switch:
  - **Critical**: Double-confirmation modal
  - Require "Reason" text field
  - Show impact warning (all strategies disabled)
- Add visual alerts for limit breaches (90%, 95%, 100%)

### Task 4.2: Alerts & Monitoring ⭐
- Set up WebSocket listener for real-time alerts
- Create "Notification Center" toast system:
  - Critical (red), Warning (yellow), Info (blue)
  - Persistent for critical alerts
- Build "System Health" page:
  - Database, Redis, OpenAlgo, WebSocket status
  - Component uptime and latency
  - **NEW**: Data quality metrics

### Task 4.3: Data Health Monitor ⭐ **NEW**
- Create data health dashboard:
  - LTP freshness by symbol (< 5s = healthy)
  - Price drift detection (Redis vs OpenAlgo)
  - Feed health timeline
  - Stale symbol alerts
- Add manual data refresh button (`POST /data/ingest`)

### Task 4.4: Position Reconciliation ⭐ **NEW**
- Build reconciliation dashboard:
  - Internal positions vs broker positions
  - Discrepancy highlighting
  - Auto-reconciliation status
  - Manual reconciliation trigger

### Task 4.5: Advanced Features ⭐ **NEW**
- **Insider Sentinel**: Alert panel for insider trades (`GET /insider/sentinel/{symbol}`)
- **Peer Comparison**: Side-by-side stock comparison (`GET /quad-analytics/{symbol}/peers`)
- **ML Accuracy Tracking**: Model performance over time (`GET /quad-analytics/{symbol}/accuracy`)
- **Pillar Weight Customization**: Sliders for Q/U/A/D weights (`POST /preferences/weights`)

### Task 4.6: Final Polish & Testing ⭐
- Perform end-to-end audit:
  - Registration → Key Gen → Strategy Creation → Dry Run Order
- Verify mobile responsiveness (Risk Dashboard, Market Watch)
- Add dark mode toggle
- Implement keyboard shortcuts (Ctrl+K for search)
- Add loading skeletons for all data-heavy components

---

## Dev Team Deliverables Checklist

### **Core Requirements** ✅
- [ ] TypeScript types for all 200+ API endpoints
- [ ] Global error handler (401, 403, 500, network errors)
- [ ] Loading states (shimmer/skeleton loaders)
- [ ] Environment config (`.env.local` for `BASE_URL`)

### **Enhanced Requirements** ⭐ **NEW**
- [ ] Auto-generated types from OpenAPI schema
- [ ] Storybook for all reusable components
- [ ] E2E tests (Playwright) for critical flows
- [ ] Performance monitoring (React DevTools Profiler)
- [ ] Accessibility (WCAG 2.1 AA compliance)
- [ ] Dark mode support
- [ ] Offline support (Service Worker)
- [ ] Error boundaries for React errors
- [ ] API response caching (TanStack Query)
- [ ] WebSocket reconnection logic

---

## Recommended Tech Stack

```json
{
  "framework": "Next.js 14 (App Router)",
  "language": "TypeScript 5.3+",
  "state": "Zustand 4.x",
  "data-fetching": "TanStack Query v5",
  "forms": "react-hook-form + zod",
  "charts": "lightweight-charts + recharts",
  "tables": "@tanstack/react-table",
  "ui": "shadcn/ui (Radix UI primitives)",
  "notifications": "react-hot-toast",
  "code-editor": "@monaco-editor/react",
  "websocket": "reconnecting-websocket",
  "date": "date-fns",
  "icons": "lucide-react",
  "testing": "Vitest + Playwright"
}
```

---

## Critical Safety Features

### **1. Execution Safety**
- [ ] Visual DRY_RUN vs LIVE mode indicator
- [ ] Double-confirmation for all orders
- [ ] Risk check results display before execution
- [ ] Kill switch with reason requirement

### **2. Data Safety**
- [ ] LTP freshness indicator (< 5s)
- [ ] Price drift warnings
- [ ] Feed health monitoring
- [ ] Stale data alerts

### **3. ML Safety**
- [ ] "Shadow Mode" badges on all ML predictions
- [ ] Clear distinction between ML and QUAD decisions
- [ ] Model accuracy display
- [ ] Prediction confidence intervals

---

## Performance Targets

- **Initial Load**: < 2s
- **Time to Interactive**: < 3s
- **API Response**: < 500ms (p95)
- **WebSocket Latency**: < 200ms
- **Chart Render**: < 100ms
- **Bundle Size**: < 500KB (gzipped)

---

## Success Criteria

- [ ] All 200+ API endpoints integrated
- [ ] Real-time data updates via WebSocket
- [ ] Complete QUAD workflow (input → decision → execution)
- [ ] Risk controls fully functional
- [ ] Mobile responsive (tablet minimum)
- [ ] 100% TypeScript coverage
- [ ] E2E tests for critical paths
- [ ] Production deployment ready

---

## Next Steps

1. **Week 0 (Pre-work)**: Set up project, install dependencies, configure tooling
2. **Week 1**: Execute Phase 1 tasks
3. **Week 2**: Execute Phase 2 tasks
4. **Week 3**: Execute Phase 3 tasks
5. **Week 4**: Execute Phase 4 tasks + testing + deployment

**Estimated Total Effort**: 160-200 hours (1 developer, 4 weeks)

---

## Support Resources

- **Backend API Docs**: http://localhost:8000/docs
- **Frontend Integration Guide**: [frontend_integration_guide.md](file:///home/fortune/.gemini/antigravity/brain/033d9449-fd76-4d39-a20d-c4140141b80d/frontend_integration_guide.md)
- **Backend Health**: http://localhost:8000/api/v1/health
- **Test Results**: 34/34 tests passing (100%)
