#!/bin/bash
# Run migrations inside Docker container

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running migrations inside Docker...${NC}"
echo "======================================"
echo ""

# Check if containers are running
if ! docker-compose ps | grep -q "backend.*Up"; then
    echo -e "${RED}❌ Backend container is not running${NC}"
    echo "Starting containers..."
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 5
fi

echo "1. Running user migration..."
docker-compose exec -T backend sh -c "cd /app && PYTHONPATH=/app python scripts/migrate_users.py"

echo ""
echo "2. Running action center migration..."
docker-compose exec -T backend sh -c "cd /app && PYTHONPATH=/app python scripts/migrate_action_center.py"

echo ""
echo -e "${GREEN}✅ Migrations completed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Check backend logs: docker-compose logs -f backend"
echo "  2. Test the API: curl http://localhost:8000/api/v1/health"
