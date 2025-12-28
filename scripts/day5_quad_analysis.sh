#!/bin/bash

# Day 5 Data Collection Script
# Runs QUAD analysis for top 50 NIFTY stocks via API to populate quad_decisions table

echo "=== DAY 5: QUAD DECISIONS POPULATION ==="
echo ""
echo "Objective: Populate quad_decisions table with 1500+ records"
echo "Target: 50 NIFTY stocks analyzed"
echo ""

# Check if backend is running
HEALTH_CHECK=$(curl -s http://localhost:8000/api/v1/health 2\u003e/dev/null)
if [ -z "$HEALTH_CHECK" ] || ! echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "❌ Error: Backend is not running or unhealthy"
    echo "Please start the application first: docker-compose up -d"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# NIFTY 50 symbols
SYMBOLS=(
    "RELIANCE" "TCS" "HDFCBANK" "INFY" "ICICIBANK"
    "HINDUNILVR" "ITC" "SBIN" "BHARTIARTL" "KOTAKBANK"
    "LT" "AXISBANK" "ASIANPAINT" "MARUTI" "SUNPHARMA"
    "TITAN" "ULTRACEMCO" "BAJFINANCE" "NESTLEIND" "WIPRO"
    "HCLTECH" "ONGC" "NTPC" "POWERGRID" "M\u0026M"
    "TATAMOTORS" "TATASTEEL" "TECHM" "ADANIENT" "COALINDIA"
    "JSWSTEEL" "INDUSINDBK" "BAJAJFINSV" "GRASIM" "HINDALCO"
    "DRREDDY" "CIPLA" "EICHERMOT" "BRITANNIA" "DIVISLAB"
    "APOLLOHOSP" "BPCL" "TATACONSUM" "HEROMOTOCO" "SHRIRAMFIN"
    "SBILIFE" "ADANIPORTS" "LTIM" "BAJAJ-AUTO" "HDFCLIFE"
)

echo "1. Running QUAD Analysis for ${#SYMBOLS[@]} NIFTY 50 stocks..."
echo ""

SUCCESSFUL=0
FAILED=0
TOTAL=${#SYMBOLS[@]}

# Process each symbol
for i in "${!SYMBOLS[@]}"; do
    SYMBOL="${SYMBOLS[$i]}"
    INDEX=$((i + 1))
    
    echo -n "[$INDEX/$TOTAL] Analyzing $SYMBOL... "
    
    # URL encode the symbol to handle special characters (M&M, BAJAJ-AUTO, etc.)
    ENCODED_SYMBOL=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SYMBOL', safe=''))")
    
    # Call QUAD analysis API with encoded symbol
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/quad/analysis/$ENCODED_SYMBOL" \
        -H "Content-Type: application/json" \
        -w "\n%{http_code}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        CONVICTION=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('conviction', 'N/A'))" 2\u003e/dev/null || echo "N/A")
        SIGNAL=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('signal', 'N/A'))" 2\u003e/dev/null || echo "N/A")
        echo "✅ Conviction: $CONVICTION% | Signal: $SIGNAL"
        ((SUCCESSFUL++))
    else
        echo "❌ Failed (HTTP $HTTP_CODE)"
        ((FAILED++))
        # Show error details for first few failures
        if [ $FAILED -le 3 ]; then
            echo "   Error: $BODY" | head -c 100
            echo ""
        fi
    fi
    
    # Small delay to avoid overwhelming the API
    sleep 0.5
done

echo ""
echo "=== ANALYSIS SUMMARY ==="
echo "Total symbols: $TOTAL"
echo "Successful: $SUCCESSFUL"
echo "Failed: $FAILED"
echo ""

# Verify database
echo "2. Verifying database..."
echo ""

python3 \u003c\u003c'EOF'
import sqlite3
from datetime import datetime

try:
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()

    print("=== DATABASE SUMMARY ===")
    print()

    # Check quad_decisions table
    cursor.execute('SELECT COUNT(*) FROM quad_decisions')
    total_decisions = cursor.fetchone()[0]
    print(f"quad_decisions: {total_decisions:,} records")

    if total_decisions \u003e 0:
        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM quad_decisions')
        unique_symbols = cursor.fetchone()[0]
        print(f"Unique symbols: {unique_symbols}")
        
        cursor.execute('SELECT MIN(decision_time), MAX(decision_time) FROM quad_decisions')
        min_date, max_date = cursor.fetchone()
        print(f"Date range: {min_date} to {max_date}")
        
        print("\nTop 10 symbols by decision count:")
        cursor.execute('''
            SELECT symbol, COUNT(*) as cnt, 
                   AVG(conviction) as avg_conviction,
                   signal
            FROM quad_decisions 
            GROUP BY symbol 
            ORDER BY cnt DESC 
            LIMIT 10
        ''')
        for row in cursor.fetchall():
            print(f"  {row[0]:15} {row[1]:4} decisions  |  Avg Conviction: {row[2]:.1f}%  |  Signal: {row[3]}")
        
        # Check if target met
        print()
        if total_decisions \u003e= 50:
            print(f"✅ SUCCESS: {total_decisions} decisions stored for {unique_symbols} symbols")
        else:
            print(f"⚠️ PARTIAL: {total_decisions} decisions stored")
    else:
        print("⚠️ No decisions found in database")

    conn.close()
    
except Exception as e:
    print(f"❌ Error checking database: {e}")
EOF

echo ""
echo "=== DAY 5 COMPLETE ==="
echo ""
