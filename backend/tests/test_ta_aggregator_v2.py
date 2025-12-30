"""
Verification tests for TA Aggregator Phase 2.3 enhancements
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.ta_aggregator import TAggregator
from app.database.models_quad import QUADUserPreferences

@pytest.mark.asyncio
async def test_aggregator_db_weights():
    """Test that aggregator correctly loads weights from DB mock"""
    db_mock = AsyncMock()
    
    # Mock preference from DB
    mock_pref = MagicMock()
    mock_pref.ta_weights = {
        "TRENDING_UP": {
            "trend": 0.8,
            "momentum": 0.1,
            "volatility": 0.05,
            "volume": 0.05
        }
    }
    
    # Configure mock session to return mock_pref
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_pref
    db_mock.execute.return_value = result_mock
    
    aggregator = TAggregator(db_mock)
    weights = await aggregator._load_regime_weights("TRENDING_UP")
    
    assert weights["trend"] == 0.8
    assert weights["momentum"] == 0.1
    db_mock.execute.assert_called()

@pytest.mark.asyncio
async def test_aggregator_db_fallback():
    """Test fallback to defaults when DB load fails or is empty"""
    db_mock = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db_mock.execute.return_value = result_mock
    
    aggregator = TAggregator(db_mock)
    weights = await aggregator._load_regime_weights("RANGING")
    
    # Should use internal defaults
    assert weights["momentum"] == 0.40 # Default for RANGING
    assert weights["trend"] == 0.10

@pytest.mark.asyncio
async def test_aggregator_record_signal():
    """Test that aggregator records signals to the database"""
    db_mock = AsyncMock()
    aggregator = TAggregator(db_mock)
    
    # Create sample data
    data = pd.DataFrame({'close': [100.0]})
    
    await aggregator._record_signal(
        symbol="TEST",
        signal="BUY",
        confidence=0.8,
        regime="TRENDING_UP",
        composite_score=0.5,
        scores={"trend": 0.5},
        weights={"trend": 1.0},
        data=data
    )
    
    db_mock.add.assert_called()
    db_mock.commit.assert_called()

@pytest.mark.asyncio
async def test_update_regime_weights():
    """Test updating regime weights in DB"""
    db_mock = AsyncMock()
    
    # Mock existing prefs
    mock_pref = MagicMock()
    mock_pref.ta_weights = {}
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_pref
    db_mock.execute.return_value = result_mock
    
    aggregator = TAggregator(db_mock)
    new_weights = {
        "trend": 0.4,
        "momentum": 0.4,
        "volatility": 0.1,
        "volume": 0.1
    }
    
    success = await aggregator.update_regime_weights("VOLATILE", new_weights)
    
    assert success is True
    assert mock_pref.ta_weights["VOLATILE"] == new_weights
    db_mock.commit.assert_called()
