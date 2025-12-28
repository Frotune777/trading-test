"""
Unit tests for QUAD Analytics Service
Tests pillar calculations, conviction scoring, and decision tracking
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pytz

from app.services.quad_service import QUADService
from app.core.contracts.state_contracts import AnalysisState


class TestQUADService:
    """Test suite for QUAD Analytics Service"""
    
    def test_quad_service_initialization(self, db_session):
        """Test QUAD service initializes correctly"""
        quad_service = QUADService(db_session)
        assert quad_service is not None
        assert quad_service.db == db_session
    
    def test_quality_pillar_calculation(self, db_session):
        """Test Quality pillar score calculation"""
        quad_service = QUADService(db_session)
        
        # Mock market data
        market_data = {
            "symbol": "RELIANCE",
            "pe_ratio": 25.5,
            "pb_ratio": 3.2,
            "roe": 15.8,
            "debt_to_equity": 0.45,
            "profit_margin": 12.5
        }
        
        quality_score = quad_service.calculate_quality(market_data)
        
        assert 0 <= quality_score <= 1
        assert isinstance(quality_score, float)
    
    def test_urgency_pillar_calculation(self, db_session):
        """Test Urgency pillar score calculation"""
        quad_service = QUADService(db_session)
        
        # Mock technical data
        technical_data = {
            "symbol": "RELIANCE",
            "rsi": 65,
            "macd_signal": "bullish",
            "volume_surge": 1.5,
            "price_momentum": 0.8
        }
        
        urgency_score = quad_service.calculate_urgency(technical_data)
        
        assert 0 <= urgency_score <= 1
        assert isinstance(urgency_score, float)
    
    def test_alignment_pillar_calculation(self, db_session):
        """Test Alignment pillar score calculation"""
        quad_service = QUADService(db_session)
        
        # Mock alignment data
        alignment_data = {
            "symbol": "RELIANCE",
            "sector_trend": "positive",
            "market_sentiment": 0.7,
            "insider_activity": "buying",
            "analyst_rating": "buy"
        }
        
        alignment_score = quad_service.calculate_alignment(alignment_data)
        
        assert 0 <= alignment_score <= 1
        assert isinstance(alignment_score, float)
    
    def test_drift_pillar_calculation(self, db_session):
        """Test Drift pillar score calculation"""
        quad_service = QUADService(db_session)
        
        # Mock drift data
        drift_data = {
            "symbol": "RELIANCE",
            "price_vs_ma50": 0.05,  # 5% above MA
            "volatility": 0.25,
            "beta": 1.2
        }
        
        drift_score = quad_service.calculate_drift(drift_data)
        
        assert 0 <= drift_score <= 1
        assert isinstance(drift_score, float)
    
    def test_conviction_score_calculation(self, db_session):
        """Test overall conviction score calculation"""
        quad_service = QUADService(db_session)
        
        pillar_scores = {
            "quality": 0.85,
            "urgency": 0.70,
            "alignment": 0.90,
            "drift": 0.15
        }
        
        conviction = quad_service.calculate_conviction(pillar_scores)
        
        assert 0 <= conviction <= 1
        assert isinstance(conviction, float)
        # Conviction should be weighted average
        expected = (0.85 * 0.3 + 0.70 * 0.25 + 0.90 * 0.25 + (1 - 0.15) * 0.20)
        assert abs(conviction - expected) < 0.01
    
    def test_complete_quad_analysis(self, db_session):
        """Test complete QUAD analysis workflow"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'fetch_market_data') as mock_market:
            with patch.object(quad_service, 'fetch_technical_data') as mock_technical:
                mock_market.return_value = {"pe_ratio": 25, "roe": 15}
                mock_technical.return_value = {"rsi": 65, "macd_signal": "bullish"}
                
                result = quad_service.analyze("RELIANCE")
                
                assert result is not None
                assert "quality_score" in result
                assert "urgency_score" in result
                assert "alignment_score" in result
                assert "drift_score" in result
                assert "conviction_score" in result
                assert result["symbol"] == "RELIANCE"
    
    def test_analysis_state_creation(self, db_session):
        """Test that analysis creates proper AnalysisState"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'fetch_market_data'):
            with patch.object(quad_service, 'fetch_technical_data'):
                result = quad_service.analyze("RELIANCE")
                
                # Verify AnalysisState structure
                assert "decision_id" in result
                assert "timestamp" in result
                assert "symbol" in result
                assert len(result["decision_id"]) > 0
    
    def test_decision_history_tracking(self, db_session):
        """Test that decisions are tracked in history"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'fetch_market_data'):
            with patch.object(quad_service, 'fetch_technical_data'):
                # Run multiple analyses
                result1 = quad_service.analyze("RELIANCE")
                result2 = quad_service.analyze("TCS")
                
                # Get decision history
                history = quad_service.get_decision_history(limit=10)
                
                assert len(history) >= 2
                assert any(d["symbol"] == "RELIANCE" for d in history)
                assert any(d["symbol"] == "TCS" for d in history)
    
    def test_pillar_drift_tracking(self, db_session):
        """Test that pillar drift over time is tracked"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'fetch_market_data'):
            with patch.object(quad_service, 'fetch_technical_data'):
                # Run analysis twice
                result1 = quad_service.analyze("RELIANCE")
                result2 = quad_service.analyze("RELIANCE")
                
                # Get pillar drift
                drift = quad_service.get_pillar_drift("RELIANCE", days=7)
                
                assert drift is not None
                assert "quality_drift" in drift
                assert "urgency_drift" in drift
    
    def test_conviction_timeline(self, db_session):
        """Test conviction timeline generation"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'get_historical_analyses') as mock_history:
            mock_history.return_value = [
                {"timestamp": datetime.now(pytz.UTC), "conviction_score": 0.75},
                {"timestamp": datetime.now(pytz.UTC), "conviction_score": 0.80},
            ]
            
            timeline = quad_service.get_conviction_timeline("RELIANCE", days=30)
            
            assert len(timeline) == 2
            assert all("timestamp" in t for t in timeline)
            assert all("conviction_score" in t for t in timeline)
    
    def test_analysis_caching(self, db_session):
        """Test that recent analyses are cached"""
        quad_service = QUADService(db_session)
        
        with patch.object(quad_service, 'fetch_market_data') as mock_market:
            with patch.object(quad_service, 'fetch_technical_data') as mock_technical:
                # First analysis
                result1 = quad_service.analyze("RELIANCE", use_cache=True)
                
                # Second analysis (should use cache)
                result2 = quad_service.analyze("RELIANCE", use_cache=True)
                
                # Market data should only be fetched once
                assert mock_market.call_count == 1
                assert result1["decision_id"] == result2["decision_id"]
    
    def test_analysis_with_custom_weights(self, db_session):
        """Test analysis with custom pillar weights"""
        quad_service = QUADService(db_session)
        
        custom_weights = {
            "quality": 0.4,
            "urgency": 0.3,
            "alignment": 0.2,
            "drift": 0.1
        }
        
        with patch.object(quad_service, 'fetch_market_data'):
            with patch.object(quad_service, 'fetch_technical_data'):
                result = quad_service.analyze("RELIANCE", weights=custom_weights)
                
                assert result is not None
                # Conviction should reflect custom weights
                assert "conviction_score" in result
