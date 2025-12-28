#!/bin/bash
# Setup script for Action Center migration

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Action Center Migration Setup${NC}"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Check if API_KEY_PEPPER is set
if ! grep -q "^API_KEY_PEPPER=" .env; then
    echo "Generating API_KEY_PEPPER..."
    PEPPER=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "" >> .env
    echo "# Security (Generated $(date))" >> .env
    echo "API_KEY_PEPPER=$PEPPER" >> .env
    echo "SESSION_EXPIRY_TIME=03:00" >> .env
    echo -e "${GREEN}✅ API_KEY_PEPPER added to .env${NC}"
else
    echo -e "${GREEN}✅ API_KEY_PEPPER already exists in .env${NC}"
fi

# Export environment variables from .env
echo ""
echo "Loading environment variables..."
set -a  # automatically export all variables
source .env
set +a

echo ""
echo "Running migrations..."
echo "======================================"

# Run user migration
echo "1. Creating users table..."
cd backend && PYTHONPATH=$(pwd) ../venv/bin/python scripts/migrate_users.py
echo ""

# Run action center migration
echo "2. Creating action center tables..."
PYTHONPATH=$(pwd) ../venv/bin/python scripts/migrate_action_center.py
cd ..

echo ""
echo -e "${GREEN}✅ All migrations completed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start the backend: cd backend && uvicorn app.main:app --reload"
echo "  2. Test the API: curl http://localhost:8000/api/v1/health"
