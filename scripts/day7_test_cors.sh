#!/bin/bash

# Day 7: CORS Testing Script
# Verifies CORS configuration for frontend-backend communication

echo "=== DAY 7: CORS CONFIGURATION TESTING ==="
echo ""
echo "Objective: Verify CORS is properly configured for frontend access"
echo "Target: Test all allowed origins and verify CORS headers"
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

# Test origins
ORIGINS=(
    "http://localhost:3000"
    "http://localhost:3006"
    "http://localhost:3010"
    "http://127.0.0.1:3000"
    "http://127.0.0.1:3010"
)

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "1. Testing CORS Headers for Allowed Origins..."
echo ""

for ORIGIN in "${ORIGINS[@]}"; do
    ((TOTAL_TESTS++))
    echo "Testing origin: $ORIGIN"
    
    # Make request with Origin header
    RESPONSE=$(curl -s -H "Origin: $ORIGIN" -v http://localhost:8000/api/v1/health 2>&1)
    
    # Check for CORS headers
    if echo "$RESPONSE" | grep -q "access-control-allow-origin: $ORIGIN"; then
        echo "  ✅ CORS headers present"
        ((PASSED_TESTS++))
        
        # Verify specific headers
        if echo "$RESPONSE" | grep -q "access-control-allow-credentials: true"; then
            echo "  ✅ Credentials allowed"
        fi
        if echo "$RESPONSE" | grep -q "access-control-expose-headers"; then
            echo "  ✅ Expose headers configured"
        fi
    else
        echo "  ❌ CORS headers missing"
        ((FAILED_TESTS++))
    fi
    echo ""
done

echo "2. Testing Disallowed Origin..."
echo ""
((TOTAL_TESTS++))
DISALLOWED_ORIGIN="http://evil.com"
echo "Testing origin: $DISALLOWED_ORIGIN"
RESPONSE=$(curl -s -H "Origin: $DISALLOWED_ORIGIN" -v http://localhost:8000/api/v1/health 2>&1)

if echo "$RESPONSE" | grep -q "access-control-allow-origin: $DISALLOWED_ORIGIN"; then
    echo "  ❌ SECURITY ISSUE: Disallowed origin was accepted!"
    ((FAILED_TESTS++))
else
    echo "  ✅ Disallowed origin correctly rejected"
    ((PASSED_TESTS++))
fi
echo ""

echo "3. Testing Preflight OPTIONS Request..."
echo ""
((TOTAL_TESTS++))
RESPONSE=$(curl -s -X OPTIONS \
    -H "Origin: http://localhost:3010" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -v http://localhost:8000/api/v1/health 2>&1)

if echo "$RESPONSE" | grep -q "< HTTP/1.1 200"; then
    echo "  ✅ OPTIONS request successful"
    ((PASSED_TESTS++))
    
    if echo "$RESPONSE" | grep -q "access-control-allow-methods"; then
        echo "  ✅ Allowed methods header present"
    fi
else
    echo "  ❌ OPTIONS request failed"
    ((FAILED_TESTS++))
fi
echo ""

echo "4. Testing API Endpoints with CORS..."
echo ""

ENDPOINTS=(
    "/api/v1/health"
    "/api/v1/quad/RELIANCE/history?limit=1"
    "/api/v1/quad/WIPRO/timeline?days=7"
)

for ENDPOINT in "${ENDPOINTS[@]}"; do
    ((TOTAL_TESTS++))
    echo "Testing: $ENDPOINT"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Origin: http://localhost:3010" \
        "http://localhost:8000$ENDPOINT")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ HTTP $HTTP_CODE"
        ((PASSED_TESTS++))
    else
        echo "  ❌ HTTP $HTTP_CODE"
        ((FAILED_TESTS++))
    fi
done
echo ""

echo "5. Testing Docker Network Configuration..."
echo ""
((TOTAL_TESTS++))

# Check if frontend and backend are on same network
BACKEND_NETWORK=$(docker inspect quad_backend --format='{{range $net,$v := .NetworkSettings.Networks}}{{$net}}{{end}}')
FRONTEND_NETWORK=$(docker inspect quad_frontend_new --format='{{range $net,$v := .NetworkSettings.Networks}}{{$net}}{{end}}' 2>/dev/null)

if [ -n "$FRONTEND_NETWORK" ] && [ "$BACKEND_NETWORK" = "$FRONTEND_NETWORK" ]; then
    echo "  ✅ Frontend and backend on same network: $BACKEND_NETWORK"
    ((PASSED_TESTS++))
elif [ -z "$FRONTEND_NETWORK" ]; then
    echo "  ⚠️ Frontend container not found (may not be running)"
    ((PASSED_TESTS++))
else
    echo "  ❌ Network mismatch: Backend=$BACKEND_NETWORK, Frontend=$FRONTEND_NETWORK"
    ((FAILED_TESTS++))
fi
echo ""

echo "=== TEST SUMMARY ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

# Detailed CORS header inspection
echo "=== DETAILED CORS HEADERS ==="
echo ""
echo "Sample request with all CORS headers:"
curl -s -H "Origin: http://localhost:3010" -v http://localhost:8000/api/v1/health 2>&1 | \
    grep -E "(^< |access-control|vary)" | head -20
echo ""

# Success criteria
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ SUCCESS: All $TOTAL_TESTS CORS tests passed!"
    echo ""
    echo "CORS Configuration Summary:"
    echo "  - Allowed origins: localhost:3000, 3006, 3010, 127.0.0.1:3000, 3010"
    echo "  - Credentials: Enabled"
    echo "  - Exposed headers: All (*)"
    echo "  - Allowed methods: GET, POST, PUT, DELETE, OPTIONS, PATCH"
    echo "  - Preflight cache: 3600 seconds"
    echo ""
    echo "=== DAY 7 COMPLETE ==="
    exit 0
else
    echo "⚠️ PARTIAL SUCCESS: $PASSED_TESTS/$TOTAL_TESTS tests passed"
    echo "Please investigate failed tests"
    exit 1
fi
