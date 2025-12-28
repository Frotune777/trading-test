# Fortune Trading Platform - QUAD Analytics

> **Institutional-Grade Quantitative Trading Platform**  
> Democratizing professional trading tools for retail traders through deterministic AI reasoning.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📊 Project Statistics

| Metric | Count |
|--------|-------|
| **Total Lines of Code** | **~28,000** |
| **Python (Backend)** | 10,500+ lines |
| **TypeScript/React (Frontend)** | 17,254 lines |
| **SQL (Migrations)** | 768 lines |
| **API Endpoints** | 50+ endpoints |
| **Database Tables** | 45+ tables |
| **Unit Tests** | 30+ tests |
| **Docker Services** | 4 services |

---

## 🎯 What is QUAD?

**QUAD** (Quantitative Unified Analysis & Decision-making) is a professional-grade trading platform that combines:

- **6-Pillar Reasoning Engine**: Trend, Momentum, Volatility, Liquidity, Sentiment, Regime
- **Institutional Data Access**: Derivatives, Insider Trading, FII/DII Activity
- **Real-time Market Analysis**: Live WebSocket feeds, Technical Indicators
- **Risk Management**: Kill switches, Position limits, P&L tracking
- **Semi-Auto Execution**: Action Center for order approval workflow

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- 8GB RAM minimum

### Launch in 3 Steps

```bash
# 1. Clone and setup
git clone https://github.com/Frotune777/trading-test.git
cd trading-test
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Access the platform
# Frontend: http://localhost:3010
# API Docs: http://localhost:8000/docs
# Backend:  http://localhost:8000
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend python migrations/run_new_migrations.py

# Verify tables
docker-compose exec db psql -U quad_user -d quad_trading -c "\dt"
```

---

## 🏗️ Architecture

### Tech Stack

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS 4
- Shadcn/UI Components
- Recharts for visualization

**Backend**
- Python 3.11
- FastAPI (async)
- Pydantic v2
- SQLAlchemy 2.0
- TA-Lib for technical analysis

**Infrastructure**
- PostgreSQL 16 (primary database)
- Redis (caching & sessions)
- Docker & Docker Compose
- Nginx (reverse proxy)

**Integrations**
- Angel One Broker API
- OpenAlgo (multi-broker support)
- NSE Data APIs
- WebSocket real-time feeds

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  Dashboard │ QUAD Analytics │ Risk Control │ Monitoring │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────┴───────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ QUAD Engine  │  │ Risk Engine  │  │ Execution    │  │
│  │ 6 Pillars    │  │ Kill Switch  │  │ Service      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Data Pipeline│  │ Monitoring   │  │ Auth Service │  │
│  │ NSE/Broker   │  │ Observability│  │ Argon2/Fernet│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│              Data Layer (PostgreSQL + Redis)             │
│  45+ Tables │ Migrations │ Indexes │ Real-time Cache    │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. QUAD Reasoning Engine
- **Deterministic AI**: 6-pillar analysis (Trend, Momentum, Volatility, Liquidity, Sentiment, Regime)
- **Conviction Scoring**: Weighted confidence scores for each signal
- **Decision History**: Full audit trail of all trading decisions
- **Pillar Drift Analysis**: Track how each pillar evolves over time

### 2. Risk Management
- **Kill Switch**: Global emergency stop for all trading
- **Position Limits**: Max exposure, daily loss limits
- **Pre-trade Validation**: Automatic risk checks before execution
- **Real-time P&L**: Live profit/loss tracking with snapshots

### 3. Action Center (Semi-Auto Trading)
- **Order Approval Workflow**: Review orders before execution
- **Pending Queue**: Manage all pending orders
- **Audit Logs**: Immutable record of all approvals/rejections
- **User Modes**: Auto vs Semi-Auto execution

### 4. Comprehensive Monitoring
- **Latency Tracking**: API response times
- **Traffic Monitoring**: Request rates and patterns
- **Error Logging**: Centralized error tracking
- **System Health**: Infrastructure status dashboard

### 5. Multi-Broker Support
- **Angel One**: Direct integration with REST + WebSocket
- **OpenAlgo**: Unified API for 24+ Indian brokers
- **Broker Abstraction**: Easy to add new brokers

### 6. Security & Authentication
- **Argon2 Password Hashing**: Industry-standard security
- **Fernet API Key Encryption**: Secure credential storage
- **Session Management**: Redis-backed sessions
- **Auth Caching**: Fast API key validation

---

## 📁 Project Structure

```
trading-test/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/  # API routes (50+ endpoints)
│   │   ├── brokers/           # Broker integrations
│   │   │   └── angelone/      # Angel One implementation
│   │   ├── core/              # Core utilities
│   │   │   ├── security/      # Auth & encryption
│   │   │   └── risk_engine.py # Risk management
│   │   ├── database/          # Models & migrations
│   │   │   ├── models_*.py    # SQLAlchemy models
│   │   │   └── schema.py      # Database schema
│   │   ├── reasoning/         # QUAD engine
│   │   │   └── pillars/       # 6 analysis pillars
│   │   ├── services/          # Business logic
│   │   └── websocket/         # Real-time feeds
│   ├── migrations/            # SQL migrations
│   ├── tests/                 # Unit & integration tests
│   └── requirements.txt       # Python dependencies
│
├── frontend-new/              # Next.js 14 frontend
│   ├── src/
│   │   ├── app/              # App router pages
│   │   ├── components/       # React components
│   │   │   ├── quad/        # QUAD-specific components
│   │   │   └── monitoring/  # Monitoring dashboards
│   │   ├── lib/api/         # API client functions
│   │   └── services/        # Frontend services
│   └── package.json
│
├── docs/                      # Documentation
│   ├── api_reference.md
│   ├── internal_architecture.md
│   └── implementation_status.md
│
├── docker-compose.yml         # Service orchestration
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 🗄️ Database Schema

### Core Tables (45+ total)

**Market Data**
- `companies` - Stock master data
- `price_history` - OHLCV historical data
- `latest_snapshot` - Current market state
- `option_chain` - Derivatives data
- `insider_trading` - Insider transactions

**QUAD Analytics**
- `quad_decisions` - Trading decisions
- `quad_snapshots` - Analysis snapshots
- `pillar_contributions` - Individual pillar scores
- `conviction_timeline` - Historical conviction

**Risk & Execution**
- `order_executions` - Trade audit log
- `pending_orders` - Action center queue
- `order_approval_logs` - Approval history
- `pnl_snapshots` - P&L tracking
- `trade_performance` - Per-trade metrics

**Monitoring**
- `latency_metrics` - API latency
- `api_traffic` - Request patterns
- `error_logs` - Error tracking
- `system_health` - Infrastructure status

**User Management**
- `users` - User accounts
- `user_sessions` - Active sessions

---

## 🔌 API Endpoints

### Core Endpoints (50+)

**Market Data**
- `GET /api/v1/stocks/{symbol}` - Stock details
- `GET /api/v1/market/overview` - Market summary
- `GET /api/v1/derivatives/option-chain` - Options data
- `GET /api/v1/insider/activity` - Insider trades

**QUAD Analytics**
- `POST /api/v1/quad-analysis/analyze` - Trigger analysis
- `GET /api/v1/quad-analytics/decisions` - Get decisions
- `GET /api/v1/quad-analytics/conviction-timeline` - Historical data

**Risk Control**
- `GET /api/v1/risk-control/status` - Risk status
- `POST /api/v1/risk-control/kill-switch` - Emergency stop
- `GET /api/v1/risk-control/limits` - Position limits

**Execution**
- `POST /api/v1/execution/place-order` - Place order
- `GET /api/v1/execution/positions` - Current positions
- `GET /api/v1/execution/orders` - Order history

**Action Center**
- `GET /api/v1/action-center/pending` - Pending orders
- `POST /api/v1/action-center/approve/{id}` - Approve order
- `POST /api/v1/action-center/reject/{id}` - Reject order

**Authentication**
- `POST /api/v1/auth/register` - Create user
- `POST /api/v1/auth/login` - Authenticate
- `POST /api/v1/auth/api-key/generate` - Generate API key

**Monitoring**
- `GET /api/v1/monitoring/health` - System health
- `GET /api/v1/monitoring/latency` - Latency metrics
- `GET /api/v1/monitoring/traffic` - Traffic stats

---

## 🧪 Testing

### Run Tests

```bash
# All tests
docker-compose exec backend pytest

# Unit tests only
docker-compose exec backend pytest tests/unit/

# Integration tests
docker-compose exec backend pytest tests/integration/

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html
```

### Test Coverage
- **Unit Tests**: 30+ tests (brokers, services, security)
- **Integration Tests**: API endpoint tests
- **Security Tests**: Auth & encryption validation

---

## 📚 Documentation

### Core Guides
- **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Technical reference
- **[SETUP.md](./SETUP.md)** - Installation & troubleshooting
- **[PROJECT_MASTER_GUIDE.md](./PROJECT_MASTER_GUIDE.md)** - Developer overview

### Deep Dives
- **[api_reference.md](./docs/api_reference.md)** - API documentation
- **[internal_architecture.md](./docs/internal_architecture.md)** - System design
- **[implementation_status.md](./docs/implementation_status.md)** - Roadmap

---

## 🔒 Security

- **Password Hashing**: Argon2id (OWASP recommended)
- **API Key Encryption**: Fernet symmetric encryption
- **Session Management**: Redis-backed with TTL
- **Auth Caching**: Fast validation with cache invalidation
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS**: Configured for production

---

## 🚦 Development Status

### ✅ Completed
- [x] QUAD Reasoning Engine (6 pillars)
- [x] Database migrations (45+ tables)
- [x] Risk management & kill switch
- [x] User authentication & API keys
- [x] Action center workflow
- [x] Monitoring & observability
- [x] Angel One broker integration
- [x] 30+ unit tests
- [x] Docker containerization

### 🚧 In Progress
- [ ] Frontend UI pages (5 remaining)
- [ ] Real-time WebSocket feeds
- [ ] Backtest engine
- [ ] ML model integration

### 📋 Planned
- [ ] Multi-broker expansion
- [ ] Advanced charting
- [ ] Mobile app
- [ ] Automated trading strategies

---

## 🤝 Contributing

This is a proprietary project. For access or collaboration inquiries, please contact the development team.

---

## 📄 License

Proprietary - All Rights Reserved

---

## 👥 Team

**Fortune Trading Engineering Team**

For questions or support, please refer to the documentation or contact the team.

---

**Last Updated**: December 29, 2025  
**Version**: 1.0.0-QUAD  
**Status**: Production-Ready Backend | Frontend Development In Progress
