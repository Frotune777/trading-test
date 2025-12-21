# 🚀 Fortune Trading QUAD System

Professional-grade stock market analysis and prediction platform for the Indian market (NSE).

## 🏗 Architecture
- **Pillar 1: Quantitative Engine (Q)** - 50+ technical indicators & patterns.
- **Pillar 2: Analytics Engine (A)** - Advanced multi-condition screener.
- **Pillar 3: Decision Engine (D)** - Multi-strategy signals & backtesting.
- **Pillar 4: Prediction Engine (P)** - ML direction and volatility forecasting.

## 🛠 Tech Stack
- **Backend**: FastAPI, PostgreSQL (TimescaleDB), Redis, Celery.
- **Frontend**: Next.js 14, TailwindCSS, Shadcn/UI, Lightweight Charts.
- **ML**: XGBoost, scikit-learn, TA-Lib.

## 🚀 Getting Started
1. **Clone & Setup Environment**:
   ```bash
   cp .env.example .env
   ```
2. **Launch with Docker**:
   ```bash
   docker-compose up --build
   ```
3. **Access**:
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Frontend: `http://localhost:3000`

## 📁 Repository Structure
- `backend/`: Core logic and API.
- `frontend/`: Next.js web application.
- `ml/`: Feature engineering and model serving.
- `legacy/`: Original Streamlit-based system files.
