# Angel One Integration - Testing Guide

## Overview
Comprehensive unit tests have been created for the Angel One broker integration covering authentication, REST API, and WebSocket functionality.

## Test Files Created

### 1. Authentication Tests
**File:** `backend/tests/unit/brokers/test_angelone_auth.py`

**Coverage:**
- TOTP generation
- Login success/failure scenarios
- Token generation and refresh
- Token validation
- Session management
- Error handling

**Test Count:** 12 tests

### 2. REST API Tests
**File:** `backend/tests/unit/brokers/test_angelone_rest.py`

**Coverage:**
- Rate limiting
- HTTP request handling with retries
- Order placement (success/failure)
- Order modification
- Order cancellation
- Position fetching
- Holdings fetching
- Order book retrieval

**Test Count:** 10 tests

### 3. WebSocket Tests
**File:** `backend/tests/unit/brokers/test_angelone_websocket.py`

**Coverage:**
- WebSocket connection
- Symbol subscription/unsubscription
- Message handling
- Heartbeat mechanism
- Disconnection and reconnection
- Error handling

**Test Count:** 8 tests

## Running the Tests

### Prerequisites
```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio pytest-mock

# Or using requirements.txt
pip install -r backend/requirements.txt
```

### Run All Angel One Tests
```bash
cd backend
python3 -m pytest tests/unit/brokers/ -v
```

### Run Specific Test Files
```bash
# Authentication tests only
python3 -m pytest tests/unit/brokers/test_angelone_auth.py -v

# REST API tests only
python3 -m pytest tests/unit/brokers/test_angelone_rest.py -v

# WebSocket tests only
python3 -m pytest tests/unit/brokers/test_angelone_websocket.py -v
```

### Run with Coverage
```bash
python3 -m pytest tests/unit/brokers/ --cov=app.brokers.angelone --cov-report=html
```

## Configuration

### Environment Variables
Update your `.env` file with Angel One credentials:

```bash
# Angel One Broker Integration
ANGELONE_API_KEY=your_angel_one_api_key_here
ANGELONE_CLIENT_ID=your_client_id_here
ANGELONE_PASSWORD=your_password_here
ANGELONE_TOTP_SECRET=your_totp_secret_here

# Broker Selection
BROKER_TYPE=angelone  # or 'openalgo'
```

### Getting Angel One Credentials
1. Register at https://smartapi.angelbroking.com/
2. Create an API app to get API Key
3. Note your Client ID (trading account number)
4. Set up TOTP for 2FA and save the secret

## Test Structure

### Mocking Strategy
- **Authentication:** Mocks HTTP requests to Angel One API
- **REST API:** Mocks requests.Session and internal methods
- **WebSocket:** Mocks websockets.connect and message handling

### Fixtures
- `auth`: Mock AngelOneAuth instance
- `rest_client`: AngelOneREST instance with mocked auth
- `ws_client`: AngelOneWebSocket instance with mocked auth

## Integration Tests (TODO)

Integration tests will test actual Angel One API connectivity:

```python
# backend/tests/integration/test_angelone_integration.py
@pytest.mark.integration
@pytest.mark.skipif(not has_angelone_credentials(), reason="Angel One credentials not configured")
async def test_real_connection():
    # Test actual API connection
    pass
```

## Next Steps

1. **Install Dependencies:**
   ```bash
   pip install pytest pytest-asyncio pytest-mock
   ```

2. **Run Tests:**
   ```bash
   python3 -m pytest tests/unit/brokers/ -v
   ```

3. **Fix Any Failures:**
   - Check import paths
   - Verify mock configurations
   - Update test data as needed

4. **Add Integration Tests:**
   - Create `tests/integration/test_angelone_integration.py`
   - Test real API connectivity (with credentials)
   - Test WebSocket streaming

5. **CI/CD Integration:**
   - Add to GitHub Actions workflow
   - Run on every PR
   - Generate coverage reports

## Test Coverage Goals

- **Unit Tests:** 90%+ coverage
- **Integration Tests:** Critical paths covered
- **E2E Tests:** Full order lifecycle

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Ensure you're in the backend directory
cd backend

# Install in development mode
pip install -e .
```

### Async Test Failures
Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

### Mock Issues
If mocks aren't working:
```bash
pip install pytest-mock
```

## Documentation

See also:
- [Angel One API Documentation](https://smartapi.angelbroking.com/docs)
- [Implementation Plan](../../../.gemini/antigravity/brain/b79701c4-c7da-46a5-8630-b2746a2875c7/implementation_plan.md)
- [Angel One Auth Module](../app/brokers/angelone/angelone_auth.py)
- [Angel One REST Module](../app/brokers/angelone/angelone_rest.py)
- [Angel One WebSocket Module](../app/brokers/angelone/angelone_websocket.py)
