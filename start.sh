#!/bin/bash

# Start database and redis services
docker compose up -d db redis

# Give services time to start
sleep 3

# Start backend (assumes venv is already activated)
# Backend runs on port 8000, Frontend on port 3006
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
