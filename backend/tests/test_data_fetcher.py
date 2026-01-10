import pytest
import pytest_asyncio
from datetime import time, datetime
from typing import Optional
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.data_fetcher import AutomatedDataFetcher

@pytest.mark.asyncio
async def test_data_fetcher_market_hours():
    fetcher = AutomatedDataFetcher()
    
    # Inside market hours (10:00 AM)
    assert fetcher._is_market_hours(time(10, 0)) is True
    
    # Outside market hours (8:00 AM)
    assert fetcher._is_market_hours(time(8, 0)) is False
    
    # Close time (3:30 PM)
    assert fetcher._is_market_hours(time(15, 30)) is True

@pytest.mark.asyncio
async def test_data_fetcher_lifecycle():
    fetcher = AutomatedDataFetcher()
    assert fetcher.is_running is False
    
    # We mock fetch_snapshot and sleep to avoid infinite loop
    with patch.object(fetcher, 'fetch_snapshot', new_callable=AsyncMock) as mock_fetch:
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            # We need to break the loop somehow. 
            # We can side_effect asyncio.sleep to raise exception or stop the fetcher
            async def stop_side_effect(*args):
                fetcher.stop()
            
            mock_sleep.side_effect = stop_side_effect
            
            # Start scheduler (it should run once loop and then stop due to side effect)
            await fetcher.start_scheduler()
            
            assert fetcher.is_running is False
            assert mock_sleep.called
