# 📘 Project Master Guide & Developer Instructions

> **CRITICAL**: This document is the **Single Source of Truth** for the project. Read this before writing any code.

## 1. Project Overview
**Name**: Portfolio-Grade Stock Analysis SaaS
**Goal**: Transform a Python-script-based trading tool into a high-performance, interactive SaaS platform providing institutional-grade data (Derivatives, Insider, Technicals) to retail users.

---

## 2. Architecture Stack
| Layer | Technology | Details |
|-------|------------|---------|
| **Frontend** | **Next.js 14** | App Router, Server Components, TypeScript. |
| **Styling** | **TailwindCSS** | Utility-first, Custom Design System. |
| **UI Library** | **Shadcn/UI** | Radix-based, Accessible, Professional components. |
| **Charts** | **Recharts** | Responsive, declarative charts. |
| **Backend** | **FastAPI** | High-performance Async Python REST API. |
| **Database** | **SQLite** | Local persistence for User Watchlists & Snapshots. |
| **Data Sources**| **Hybrid** | `NSEMasterData` (Charting), `NseUtils` (Live), `Screener` (Fundamentals). |

---

## 3. Backend API Reference (Existing)
The backend has been expanded with 4 critical routers. **Do not hallucinate new endpoints.** Use these:

### 🟢 Market Data (`/market`)
- `GET /market/breadth`: Advance/Decline Ratio.
- `GET /market/activity/volume`: Most Active by Volume.
- `GET /market/activity/value`: Most Active by Value.
- `GET /market/indices`: Live data for Nifty 50, Bank Nifty, etc.

### 🔴 Derivatives (`/derivatives`)
- `GET /derivatives/option-chain/{symbol}?indices=true`: Full Option Chain.
- `GET /derivatives/futures/{symbol}`: Futures Prices & OI.
- `GET /derivatives/pcr/{symbol}`: Put-Call Ratio (calculated).

### 🔵 Technicals (`/technicals`)
- `GET /technicals/intraday/{symbol}?interval=5m`: Intraday OHLCV for charts.
- `GET /technicals/indicators/{symbol}`: 50+ Indicators (RSI, MACD, BB) + Stats.

### 🟣 Insider & Sentinel (`/insider`)
- `GET /insider/trades`: Insider Trading (SAST/Promoters).
- `GET /insider/bulk-deals`: Large institutional deals.
- `GET /insider/short-selling`: Daily short selling reports.

---

## 4. Frontend Design Guidelines
**Aesthetics**: "Dark Node", "Glassmorphism", "Premium Fintech".
- **Backgrounds**: Deep slate/zinc colors (e.g., `bg-slate-950`).
- **Cards**: Subtle borders, slight translucency (`bg-slate-900/50 backdrop-blur`).
- **Typography**: Inter or Geist Sans. Clean, readable, professional.
- **Interactivity**: Hover effects on rows, instantaneous chart tooltips.

**Component Rules**:
- Use **Shadcn/UI** for all primitives (Buttons, Inputs, Dialogs, Tables).
- Do not build custom dropdowns/modals from scratch; wrap Shadcn components.
- Use **Lucide React** for icons.

---

## 5. Development Rules (Strict)
1.  **No Hallucinations**:
    - Do not invent API methods. Check `nse_utils.py` or the Backend Plan first.
    - If a data point seems missing, **Check the API first** (e.g., use `/technicals/indicators` for RSI, don't calculate it in JS).

2.  **Verify Signatures**:
    - Before calling a backend function, verify its arguments in the python file.
    - Example: `get_insider_trading` takes `from_date` (str), not datetime object.

3.  **Step-by-Step Execution**:
    - **Plan**: Update `MIGRATION_TASKS.md`.
    - **Code**: Implement the feature.
    - **Verify**: Check against the Master Guide.

4.  **Directory Structure**:
    - `backend/`: FastAPI Application.
    - `frontend/`: (Legacy) Streamlit App.
    - `frontend-new/`: **(Target)** Next.js Application.

---

## 6. Implementation Status
- [x] Backend API Expansion (Market, Derivatives, Insider, Technicals).
- [ ] Frontend Setup (Next.js Initialization).
- [ ] UI Component Implementation.
- [ ] Integration.
