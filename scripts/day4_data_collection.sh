#!/bin/bash

# Day 4 Data Collection Script
# Collects insider trading, corporate events, and option chain data

echo "=== DAY 4 DATA COLLECTION ==="
echo ""

# Run insider trading collection
echo "1. Fetching Insider Trading Data (last 30 days)..."
docker exec quad_backend python -c "
import sys
sys.path.insert(0, '/app')
from app.services.insider_trading_service import InsiderTradingService
import logging
logging.basicConfig(level=logging.WARNING)

service = InsiderTradingService()
results = service.fetch_and_store(days=30)
print(f'✅ Insider Trading: {results[\"records_stored\"]} records stored')
"

echo ""

# Run corporate events collection
echo "2. Fetching Corporate Events (last 90 days)..."
docker exec quad_backend python -c "
import sys
sys.path.insert(0, '/app')
from app.services.corporate_events_service import CorporateEventsService
import logging
logging.basicConfig(level=logging.WARNING)

service = CorporateEventsService()
results = service.fetch_and_store(days=90)
print(f'✅ Corporate Events: {results[\"records_stored\"]} records stored')
"

echo ""

# Run option chain collection (only during market hours)
echo "3. Fetching Option Chain Data (FNO stocks)..."
docker exec quad_backend python -c "
import sys
sys.path.insert(0, '/app')
from app.services.option_chain_service import OptionChainService
import logging
logging.basicConfig(level=logging.WARNING)

service = OptionChainService()
results = service.fetch_and_store()
if results['records_stored'] > 0:
    print(f'✅ Option Chain: {results[\"records_stored\"]} records stored')
else:
    print('⚠️ Option Chain: No data (market closed or no options available)')
"

echo ""
echo "=== DATA COLLECTION COMPLETE ==="
echo ""

# Show database summary
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

print("=== DATABASE SUMMARY ===")

tables = ['insider_trading', 'corporate_events', 'option_chain']
for table in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        cursor.execute(f'SELECT COUNT(DISTINCT symbol) FROM {table}')
        symbols = cursor.fetchone()[0]
        print(f"{table:20}: {count:6,} records, {symbols:4} symbols")
    except:
        print(f"{table:20}: Table not found")

conn.close()
EOF
