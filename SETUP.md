# Fortune Trading Platform: Setup Guide

Welcome to the **Fortune Trading Platform**. This guide covers setting up the development environment using Docker (recommended) or manual installation.

---

## 🏗️ Recommended: Docker Setup

The easiest way to run the entire stack is using Docker Compose.

### 1. Prerequisites
- Docker & Docker Compose
- `.env` file (copy from `.env.example`)

### 2. Launching the Stack
Run the provided script to start the Backend, Frontend, Redis, and Database:

```bash
./start_docker.sh
```

- **Frontend**: `http://localhost:3010`
- **Backend API**: `http://localhost:8000/api/v1`
- **Interactive API Docs**: `http://localhost:8000/docs`

### 3. Stopping the Stack
```bash
./stop_docker.sh
```

---

## 🐍 Manual Backend Setup (Local)

If you need to run the backend outside of Docker:

### 1. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run FastAPI
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚛️ Manual Frontend Setup (Local)

### 1. Install Node Dependencies
```bash
cd frontend-new
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

The frontend will start at `http://localhost:3010`.

---

## 🔧 Troubleshooting

### Port Conflicts
- Ensure ports `3010`, `8000`, `5432` (Postgres), and `6379` (Redis) are free.

### CORS Errors
- Verify that `BACKEND_CORS_ORIGINS` in `.env` includes `["http://localhost:3010"]`.

---
*For development rules and architecture, see [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md).*
