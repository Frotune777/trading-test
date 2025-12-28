#!/bin/bash

# Day 6: QUAD Analytics Endpoints Testing Script
# Tests all QUAD analytics endpoints for multiple stocks

echo "=== DAY 6: QUAD ANALYTICS ENDPOINTS TESTING ==="
echo ""
echo "Objective: Verify all QUAD analytics endpoints are working correctly"
echo "Target: Test history, timeline, and accuracy endpoints for 10 stocks"
echo ""

# Check if backend is running
HEALTH_CHECK=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null)
if [ -z "$HEALTH_CHECK" ] || ! echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "❌ Error: Backend is not running or unhealthy"
    echo "Please start the application first: docker-compose up -d"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Test stocks (top 10 by conviction from Day 5)
TEST_STOCKS=(
    "WIPRO" "BHARTIARTL" "MARUTI" "GRASIM" "NESTLEIND"
    "TITAN" "BAJAJ-AUTO" "TECHM" "INFY" "HINDALCO"
)

echo "Testing QUAD Analytics Endpoints for ${#TEST_STOCKS[@]} stocks..."
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test each stock
for SYMBOL in "${TEST_STOCKS[@]}"; do
    echo "[$((${#TEST_STOCKS[@]} - ${#TEST_STOCKS[@]} + TOTAL_TESTS/3 + 1))/${#TEST_STOCKS[@]}] Testing $SYMBOL..."
    
    # Test 1: History endpoint
    ((TOTAL_TESTS++))
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/quad/$SYMBOL/history?limit=5")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ History endpoint: $HTTP_CODE"
        ((PASSED_TESTS++))
    else
        echo "  ❌ History endpoint: $HTTP_CODE"
        ((FAILED_TESTS++))
    fi
    
    # Test 2: Timeline endpoint
    ((TOTAL_TESTS++))
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/quad/$SYMBOL/timeline?days=30")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ Timeline endpoint: $HTTP_CODE"
        ((PASSED_TESTS++))
    else
        echo "  ❌ Timeline endpoint: $HTTP_CODE"
        ((FAILED_TESTS++))
    fi
    
    # Test 3: Accuracy endpoint
    ((TOTAL_TESTS++))
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/quad/$SYMBOL/accuracy?days=90")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ Accuracy endpoint: $HTTP_CODE"
        ((PASSED_TESTS++))
    else
        echo "  ❌ Accuracy endpoint: $HTTP_CODE"
        ((FAILED_TESTS++))
    fi
    
    echo ""
done

echo "=== TEST SUMMARY ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

# Detailed response testing
echo "=== DETAILED RESPONSE TESTING ==="
echo ""

echo "1. Testing History endpoint with RELIANCE:"
curl -s "http://localhost:8000/api/v1/quad/RELIANCE/history?limit=2" | python3 -m json.tool | head -30
echo ""

echo "2. Testing Timeline endpoint with WIPRO:"
curl -s "http://localhost:8000/api/v1/quad/WIPRO/timeline?days=30" | python3 -m json.tool
echo ""

echo "3. Testing Accuracy endpoint with INFY:"
curl -s "http://localhost:8000/api/v1/quad/INFY/accuracy?days=90" | python3 -m json.tool
echo ""

# Success criteria
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ SUCCESS: All $TOTAL_TESTS tests passed!"
    echo ""
    echo "=== DAY 6 COMPLETE ==="
    exit 0
else
    echo "⚠️ PARTIAL SUCCESS: $PASSED_TESTS/$TOTAL_TESTS tests passed"
    echo "Please investigate failed endpoints"
    exit 1
fi
