# Technology Stack Reference

This project utilizes a modern, decoupled stack built for high-performance financial analysis.

## 🏗️ Architecture Overview

The system is split into three main tiers:
1.  **Frontend (Next.js)**: A React-based application for data visualization and user interaction.
2.  **Backend (FastAPI)**: A high-performance Python API that handles data fetching, calculation, and reasoning.
3.  **Data Persistence (PostgreSQL & Redis)**: Efficient storage for historical data and low-latency caching.

---

## 💻 Frontend Stack

| Layer | Implementation |
| :--- | :--- |
| **Framework** | Next.js 14+ (App Router) |
| **Language** | TypeScript |
| **Styling** | TailwindCSS 4 |
| **Components** | Radix UI + Shadcn/UI |
| **Data Fetching** | TanStack React Query + Axios |
| **Charting** | Recharts 3.6 |

---

## ⚙️ Backend Stack

| Layer | Implementation |
| :--- | :--- |
| **API Framework** | Python 3.11+ / FastAPI |
| **Data Logic** | Pandas / NumPy / SciPy |
| **Reasoning** | QUAD Engine (Pillar-based) |
| **Technical Analysis** | TA-Lib |
| **Scraping** | BS4 / nselib / yfinance |

---

## 🗄️ Infrastructure

- **Database**: PostgreSQL (Relational Data)
- **Cache**: Redis (Rate Limiting & Session Context)
- **Deployment**: Docker Compose (Multi-container architecture)

For deep-dive development instructions, see the [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) in the project root.