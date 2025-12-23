#!/bin/bash

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Starting Fortune Trading QUAD system in Docker..."
docker-compose up -d --build

echo ""
echo "✅ System started!"
echo "➡️  Frontend: http://localhost:3010"
echo "➡️  Backend:  http://localhost:8000/docs"
echo "➡️  DB Admin: (Connect via preferred client to port 5438)"
