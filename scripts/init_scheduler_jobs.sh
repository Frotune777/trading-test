#!/bin/bash
# Initialize Scheduler Jobs via API
# Creates data collection jobs for NIFTY 50 stocks

API_BASE="http://localhost:8000/api/v1"

# NIFTY 50 symbols
SYMBOLS='["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","ITC","SBIN","BHARTIARTL","KOTAKBANK","LT","AXISBANK","ASIANPAINT","MARUTI","SUNPHARMA","TITAN","ULTRACEMCO","BAJFINANCE","NESTLEIND","WIPRO","HCLTECH","ONGC","NTPC","POWERGRID","M&M","TATAMOTORS","TATASTEEL","TECHM","ADANIENT","COALINDIA","JSWSTEEL","INDUSINDBK","BAJAJFINSV","GRASIM","HINDALCO","DRREDDY","CIPLA","EICHERMOT","BRITANNIA","DIVISLAB","APOLLOHOSP","BPCL","TATACONSUM","HEROMOTOCO","SHRIRAMFIN","SBILIFE","ADANIPORTS","LTIM","BAJAJ-AUTO","HDFCLIFE"]'

echo "=========================================="
echo "INITIALIZING SCHEDULER JOBS"
echo "=========================================="

# 1. Market Close Download (3:35 PM IST daily)
echo -e "\n1. Creating market close download job..."
curl -s -X POST "$API_BASE/scheduler/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"market_close\",
    \"symbols\": $SYMBOLS,
    \"intervals\": [\"1m\", \"5m\", \"15m\", \"1h\", \"1d\"],
    \"enabled\": true
  }" | jq .

# 2. Pre-Market Download (8:30 AM IST daily)
echo -e "\n2. Creating pre-market download job..."
curl -s -X POST "$API_BASE/scheduler/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"pre_market\",
    \"symbols\": $SYMBOLS,
    \"enabled\": true
  }" | jq .

# 3. Intraday LTP Refresh (every 5 minutes during market hours)
echo -e "\n3. Creating intraday LTP refresh job..."
curl -s -X POST "$API_BASE/scheduler/jobs" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_type\": \"intraday_ltp\",
    \"symbols\": $SYMBOLS,
    \"interval_minutes\": 5,
    \"enabled\": true
  }" | jq .

# 4. List all jobs
echo -e "\n=========================================="
echo "SCHEDULED JOBS SUMMARY"
echo "=========================================="
curl -s "$API_BASE/scheduler/jobs" | jq .

echo -e "\n✅ Scheduler initialization complete!"
