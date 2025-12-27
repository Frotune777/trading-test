#!/bin/bash

# Fortune Trading QUAD Unified Control Script
# Usage: ./quad.sh [start|stop|restart|status|logs|migrate]

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="quad"

# Pre-flight checks
check_deps() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Error: docker is not installed."
        exit 1
    fi
    if ! docker compose version &> /dev/null; then
        echo "❌ Error: docker-compose (v2) is not installed."
        exit 1
    fi
}

check_env() {
    if [ ! -f .env ]; then
        echo "⚠️  Warning: .env file not found. Creating from .env.example..."
        cp .env.example .env
    fi
}

start_system() {
    echo "🚀 Starting Fortune Trading QUAD system..."
    check_env
    docker compose -f $COMPOSE_FILE up -d --build
    echo "✅ System started!"
    echo "➡️  Frontend: http://localhost:3010"
    echo "➡️  Backend:  http://localhost:8000/docs"
}

stop_system() {
    echo "🛑 Stopping Fortune Trading QUAD system..."
    docker compose -f $COMPOSE_FILE down
    echo "✅ System stopped."
}

restart_system() {
    stop_system
    start_system
}

show_status() {
    echo "📊 System Status:"
    docker compose -f $COMPOSE_FILE ps
}

show_logs() {
    docker compose -f $COMPOSE_FILE logs -f --tail=100 $1
}

run_migrations() {
    echo "🔄 Running database migrations inside backend container..."
    docker compose -f $COMPOSE_FILE exec backend python run_migration.py
}

# Main
check_deps

case "$1" in
    start)
        start_system
        ;;
    stop)
        stop_system
        ;;
    restart)
        restart_system
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    migrate)
        run_migrations
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|migrate}"
        echo "Example: ./quad.sh start"
        exit 1
        ;;
esac
