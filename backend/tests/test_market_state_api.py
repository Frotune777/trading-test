import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
import json
import time

@pytest.mark.asyncio
async def test_get_market_state_api():
    from app.core.auth import get_current_user
    from app.core.database import get_db
    from app.services.market_state_service import MarketStateSnapshot
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Clear overrides after test
        app.dependency_overrides = {}
        
        # Setup mocks
        mock_user = MagicMock()
        mock_user.id = 1
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        snapshot = MarketStateSnapshot(
            symbol="RELIANCE",
            ltp=2500.0,
            is_fresh=True,
            feed_status="HEALTHY",
            timestamp=time.time()
        )
        
        # Patch the service method
        with patch("app.api.v1.endpoints.market_state.market_state_service.get_market_state", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = snapshot
            
            # Set dependency overrides
            app.dependency_overrides[get_current_user] = lambda: mock_user
            app.dependency_overrides[get_db] = lambda: mock_db
            
            try:
                response = await ac.get("/api/v1/market-state/RELIANCE")
                
                assert response.status_code == 200
                data = response.json()
                assert data["symbol"] == "RELIANCE"
                assert data["ltp"] == 2500.0
                assert data["is_fresh"] is True
            finally:
                app.dependency_overrides = {}
