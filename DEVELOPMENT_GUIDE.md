# Fortune Trading Platform: Comprehensive Development Documentation

**Version**: 1.0.0  
**Role**: Senior Technical Writer & Software Architect  
**Scope**: Purely Development (Architecture, APIs, Frontend, Integration, Rules)

---

## 1. Project Overview

### Purpose and Scope
The Fortune Trading Platform is an institutional-grade stock analysis SaaS designed for professional and零售 users. It consolidates heterogeneous data sources (NSE, Yahoo Finance, Screener) into a unified **Reasoning Engine (QUAD)**. The platform provides real-time breadths, derivatives mapping, technical indicators, and institutional activity tracking.

### Key Goals
- **Architectural Shift**: Migration from script-based legacy logic to a robust, async FastAPI + Next.js 14 stack.
- **Deterministic Reasoning**: Implementation of the QUAD architecture—a 6-pillar analysis engine (Trend, Momentum, Volatility, Liquidity, Sentiment, Regime).
- **Frontend Excellence**: A "Premium Fintech" UI that prioritizes data density without compromising speed or aesthetics.

---

## 2. Architecture Stack

The system follows a three-tier architecture with clear semantic boundaries.

### Layer-by-Layer Breakdown

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | [Next.js 14+](https://nextjs.org/) | Next-generation routing, server-side data fetching, and high SEO performance. |
| **Styling** | [TailwindCSS 4](https://tailwindcss.com/) | Performance-first utility styles with CSS variable-first configuration. |
| **UI Library** | [Shadcn/UI](https://ui.shadcn.com/) | Radix-based primitives that allow for high-end custom branding. |
| **Charts** | [Recharts 3.6+](https://recharts.org/) | SVG-based, natively responsive charting for financial time-series. |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | Extremely high performance, automatic Pydantic validation, and async I/O. |
| **Logic Layer** | `ReasoningEngine` | Pillar-based analytical architecture for "Trade Intent" generation. |
| **Database** | [PostgreSQL (PostGIS)](https://www.postgresql.org/) | Powerful relational storage for symbols, financial records, and historical data. |
| **Caching** | [Redis](https://redis.io/) | Used for session contexts, rate limiting, and caching expensive NSE API hits. |

### Technical Interaction
- **Frontend** consumes the **Backend API** via `Axios` and `TanStack Query` for robust state management.
- **Backend** orchestrates data from **Scraping Services** (NseUtils, YahooFinance) and passes it through the **Reasoning Engine**.
- **QUAD Engine** outputs a strict `TradeIntent v1.0` contract, which the Frontend renders using dedicated visualization pillars.

---

## 3. Backend API Reference

The API follows a domain-driven router structure. All endpoints are prefixed with `/api/v1`.

### 🟢 Market Data (`/market`)
*Focus: Overall market health and institutional pulse.*

| Endpoint | Method | Parameters | Response Format |
| :--- | :--- | :--- | :--- |
| `/market/breadth` | `GET` | None | `{ data: [{ symbol, advances, declines... }] }` |
| `/market/activity/volume` | `GET` | None | Lists top 20 stocks by traded volume. |
| `/market/indices` | `GET` | None | Live snapshots of Nifty, BankNifty, and Sensex. |

### 🔴 Derivatives (`/derivatives`)
*Focus: Options heatmap, Open Interest (OI) analysis, and Futures.*

| Endpoint | Method | Parameters | Response Format |
| :--- | :--- | :--- | :--- |
| `/derivatives/option-chain/{symbol}`| `GET` | `symbol`, `indices` | Nested CE/PE strikes with Greeks and OI metrics. |
| `/derivatives/futures/{symbol}` | `GET` | `symbol` | Futures prices, daily OI change, and premium/discount. |
| `/derivatives/pcr/{symbol}` | `GET` | `symbol` | Floating point PCR (Put-Call Ratio) for nearest expiry. |

### 🔵 Technicals (`/technicals`)
*Focus: Mathematical indicators and chart data.*

| Endpoint | Method | Parameters | Response Format |
| :--- | :--- | :--- | :--- |
| `/technicals/indicators/{symbol}` | `GET` | `symbol` | Object containing 50+ TA-Lib indicator outputs. |
| `/technicals/intraday/{symbol}` | `GET` | `symbol`, `interval` | Array of OHLCV objects for chart rendering. |

### 🟣 Insider & Sentinel (`/insider`)
*Focus: Tracking "Smart Money" movements.*

| Endpoint | Method | Parameters | Response Format |
| :--- | :--- | :--- | :--- |
| `/insider/trades` | `GET` | `from`, `to` | List of corporate insider transactions. |
| `/insider/bulk-deals` | `GET` | `from`, `to` | High-volume institutional transactions from NSE. |
| `/insider/short-selling` | `GET` | `from`, `to` | Daily reported short volumes per security. |

---

## 4. Frontend Design Guidelines

### Aesthetic Principles: "Premium Fintech"
- **Dark Node**: Use a palette based on deep slates (`#020617`) and zincs. Avoid pure black.
- **Glassmorphism**: Backdrop blurs (`blur-md`) and 10-15% opacity backgrounds for cards.
- **Precision Typography**: Use Geist Sans or Inter. Data-dense tables use Monospace for numbers.

### Styling & Component Rules
- **Tailwind Tokens**: Use semantic tokens (e.g., `primary`, `accent`, `muted`) defined in `globals.css`.
- **Iconography**: [Lucide React](https://lucide.dev/) for consistency. Stroke width set to `1.5` or `2.0`.
- **Chart Colors**: 
  - Gains/Success: `Emerald-500` or `oklch(0.696 0.17 162.48)`
  - Losses/Error: `Rose-500` or `oklch(0.704 0.191 22.216)`

---

## 5. Development Rules

### Rule 1: API-First Accuracy (No Hallucinations)
Do not invent backend fields. Always inspect the Pydantic models in `backend/app/api/v1/endpoints/` before writing frontend types.

### Rule 2: Signature Verification
Before calling a Python function, verify its signature (arguments and types) in the source file. Ensure the Frontend `useQuery` hooks match the expected API parameters.

### Rule 3: Execution Workflow
1.  **Plan**: Draft the implementation logic.
2.  **Code**: Write clean, typed code.
3.  **Verify**: Perform manual validation and run Playwright E2E tests.

### Rule 4: Error Handling
- **Backend**: Always return descriptive `HTTPException` details.
- **Frontend**: Handle API failures gracefully using TanStack Query's `error` states and Toast notifications.

---

## 6. Implementation Status

### ✅ Completed
- **Backend API Expansion**: Full coverage for Market, Derivatives, Insider, and Technicals.
- **QUAD Reasoning Engine**: Core logic and v1.0 contract enforcement.
- **Frontend Core**: Dashboard layout, Sidebar, Theme Toggle, and Component Library.
- **CORS & Integration**: Secure communication between 8000 (API) and 3010 (Frontend).

### 🟡 In-Progress / Pending
- **Advanced Sentinel**: Insider pattern detection and notification engine.
- **Portfolio Tracking**: Real-time holding analysis using the Reasoning Engine.
- **Technical Charting**: Full-screen TradingView-style integration for indicator overlays.

---

## 7. Future Development Enhancements

- **Real-Time Push**: WebSocket integration for live price breakouts and sentinel alerts.
- **AI Narrative Expansion**: Utilizing LLMs to turn QUAD pillar scores into deeper psychological market summaries.
- **Custom Indicators**: A Python-based sandbox for users to write and backtest custom strategies.

---
*Document maintained by: Fortune Trading Architecture Team*
