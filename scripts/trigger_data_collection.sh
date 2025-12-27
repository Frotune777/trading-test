#!/bin/bash
# Manually trigger data collection to populate database immediately
# This script runs the scheduled jobs NOW instead of waiting for their scheduled times

API_BASE="http://localhost:8000/api/v1"

echo "=========================================="
echo "MANUAL DATA COLLECTION TRIGGER"
echo "=========================================="

# 1. Trigger market close download NOW
echo -e "\n1. Triggering market close download..."
curl -s -X POST "$API_BASE/scheduler/jobs/market_close_download/run" | jq .
sleep 2

# 2. Trigger pre-market download NOW
echo -e "\n2. Triggering pre-market download..."
curl -s -X POST "$API_BASE/scheduler/jobs/pre_market_download/run" | jq .
sleep 2

# 3. Trigger LTP refresh NOW
echo -e "\n3. Triggering LTP refresh..."
curl -s -X POST "$API_BASE/scheduler/jobs/intraday_ltp_refresh/run" | jq .

echo -e "\n=========================================="
echo "✅ Data collection triggered!"
echo "Check Docker logs for progress:"
echo "  docker logs quad_backend --tail 100 -f"
echo "=========================================="
