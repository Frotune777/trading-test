# 📘 Project Master Guide & Developer Instructions

> **CRITICAL**: This document is the **Single Source of Truth** for the project. Read this before writing any code. For a deeper dive, refer to the [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md).

---

## 1. Project Overview
**Name**: Fortune Trading QUAD SaaS  
**Goal**: Transform legacy stock analysis scripts into a high-performance, interactive SaaS platform providing institutional-grade QUAD (Quantitative, Underlying, Analysis, Derivatives) reasoning to retail traders.

### Key Technical Outcomes:
- **Unified Reasoning Engine**: 6 Pillars of analysis outputting a static `TradeIntent v1.0` contract.
- **Async Architecture**: FastAPI backend capable of handling multiple market data streams concurrently.
- **Premium UX**: Next.js 14 based dashboard with high-fidelity charts and glassmorphism design.

---

## 2. Architecture Stack
| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14** | App Router, Server Components, TypeScript. |
| **Styling** | **TailwindCSS 4** | Themeable CSS-first utility styles. |
| **UI Library** | **Shadcn/UI** | Accessible primitives based on Radix UI. |
| **Charts** | **Recharts** | Declarative, SVG-based responsive charting. |
| **Backend** | **FastAPI** | High-performance Async Python API with Pydantic v2. |
| **Database** | **PostgreSQL** | Relational data with PostGIS extensions. |
| **Data Sources**| **Hybrid** | NSEMasterData, NseUtils, Screener, Yahoo Finance. |

---

## 3. Backend API Reference (Existing)
*Do not hallucinate new endpoints. Use These existing routers:*

### 🟢 Market Data (`/market`)
- `GET /market/breadth`: Advance/Decline Ratio snapshots.
- `GET /market/activity/volume`: Market leaders by volume.
- `GET /market/indices`: Live global and domestic major indices.

### 🔴 Derivatives (`/derivatives`)
- `GET /derivatives/option-chain/{symbol}`: Full nested option chain data.
- `GET /derivatives/futures/{symbol}`: Futures price and Open Interest.
- `GET /derivatives/pcr/{symbol}`: Put-Call Ratio implementation.

### 🔵 Technicals (`/technicals`)
- `GET /technicals/indicators/{symbol}`: 50+ indicators (RSI, MACD, etc.).
- `GET /technicals/intraday/{symbol}`: Chart-ready OHLCV data.

### 🟣 Insider & Sentinel (`/insider`)
- `GET /insider/trades`: Insider Trading reports from NSE.
- `GET /insider/bulk-deals`: Significant institutional bulk deals.
- `GET /insider/short-selling`: Reported daily short-selling metrics.

---

## 4. Frontend Design Guidelines
**Aesthetics**: "Dark Node", "Glassmorphism", "Premium Fintech".

- **Palette**: Deep slate backgrounds (`oklch(0.145 0 0)`) with neutral accents.
- **Surfaces**: Cards use `bg-slate-900/50` with `backdrop-blur-md` and `border-slate-800`.
- **Interactions**: Subtle lift on hover, micro-animations for data arrival.
- **Components**: Standardize on **Shadcn/UI**; use **Lucide React** for icons.

---

## 5. Development Rules (Strict)

1.  **Direct Correlation**: Backend models (Pydantic) must map 1:1 to Frontend interfaces.
2.  **No Hallucinations**: Never invent API endpoints. Check `app/api/v1/router.py`.
3.  **Step-by-Step**: Plan changes in `MIGRATION_TASKS.md` or a task artifact before coding.
4.  **Verification**: Every new feature must be verified against the `DEVELOPMENT_GUIDE.md` standards.

---

## 6. Implementation Status
- [x] **Phase 1**: Infrastructure & Dockerization.
- [x] **Phase 2**: Backend API Expansion (Market, Derivatives, Insider, Technicals).
- [x] **Phase 3**: QUAD Reasoning Engine Core.
- [x] **Phase 4**: Next.js 14 Frontend Setup & Integration.
- [/] **Phase 5**: Advanced Sentinel Analytics (In Progress).

---

## 7. Future Enhancements
- Real-time WebSockets for breakout alerts.
- Advanced AI-driven market psychological summaries.
- Customized user-defined technical strategy builder.

---
*For full API schemas and design tokens, see the [docs/](./docs/) directory.*
