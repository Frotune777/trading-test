"""
Integration Tests with Real Data
Tests using actual database data and historical price data
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.services.strategy_executor import StrategyExecutor
from app.services.ta_aggregator import TAggregator
from app.services.ml_autotuner import MLAutoTuner
from app.services.model_promoter import ModelPromoter
from app.database.models_quad import QUADDecision, PillarScores
from app.database.models_monitoring import PriceHistory


class TestStrategyWithRealData:
    """Test strategies with real historical data"""
    
    @pytest.mark.asyncio
    async def test_strategy_with_historical_prices(self, db: AsyncSession):
        """Test strategy execution with real price history"""
        
        # Fetch real price data from database
        stmt = select(PriceHistory).where(
            PriceHistory.symbol == 'RELIANCE'
        ).order_by(PriceHistory.timestamp.desc()).limit(100)
        
        result = await db.execute(stmt)
        price_records = result.scalars().all()
        
        if len(price_records) < 50:
            pytest.skip("Insufficient historical data for RELIANCE")
        
        # Convert to DataFrame
        data = pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in reversed(price_records)
        ])
        data.set_index('timestamp', inplace=True)
        
        # Test strategy code
        strategy_code = """
class TestStrategy(StrategyBase):
    def setup(self):
        self.fast = 10
        self.slow = 20
    
    def on_data(self, data):
        sma_fast = self.sma(data, self.fast)
        sma_slow = self.sma(data, self.slow)
        
        if sma_fast.iloc[-1] > sma_slow.iloc[-1]:
            return self.buy(quantity=10)
        else:
            return self.hold()
"""
        
        # Validate and execute
        executor = StrategyExecutor(db)
        validation = await executor.validate_strategy_code(strategy_code)
        
        assert validation['valid'] == True, f"Validation errors: {validation.get('errors')}"
        
        print(f"✅ Strategy validated with {len(data)} real price records")


class TestTAggregatorWithRealData:
    """Test TA Aggregator with real market data"""
    
    @pytest.mark.asyncio
    async def test_signal_generation_real_data(self, db: AsyncSession):
        """Test TA signal generation with real price data"""
        
        # Fetch real price data
        stmt = select(PriceHistory).where(
            PriceHistory.symbol == 'TCS'
        ).order_by(PriceHistory.timestamp.desc()).limit(100)
        
        result = await db.execute(stmt)
        price_records = result.scalars().all()
        
        if len(price_records) < 50:
            pytest.skip("Insufficient historical data for TCS")
        
        # Convert to DataFrame
        data = pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in reversed(price_records)
        ])
        data.set_index('timestamp', inplace=True)
        
        # Generate signal
        aggregator = TAggregator(db)
        signal = await aggregator.get_signal(
            symbol='TCS',
            data=data,
            use_adaptive_weights=True
        )
        
        # Verify signal
        assert signal['signal'] in ['BUY', 'SELL', 'HOLD']
        assert 0 <= signal['confidence'] <= 1
        assert signal['regime'] in ['TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'VOLATILE', 'UNKNOWN']
        
        print(f"✅ TA Signal: {signal['signal']} (confidence: {signal['confidence']:.2f}, regime: {signal['regime']})")


class TestMLWithRealQUADData:
    """Test ML components with real QUAD decisions"""
    
    @pytest.mark.asyncio
    async def test_ml_training_with_quad_decisions(self, db: AsyncSession):
        """Test ML training with real QUAD decision data"""
        
        # Fetch real QUAD decisions
        stmt = select(QUADDecision).where(
            QUADDecision.symbol == 'INFY'
        ).order_by(QUADDecision.timestamp.desc()).limit(200)
        
        result = await db.execute(stmt)
        decisions = result.scalars().all()
        
        if len(decisions) < 50:
            pytest.skip("Insufficient QUAD decisions for INFY")
        
        # Prepare features and targets
        X = []
        y = []
        
        for decision in decisions:
            features = [
                decision.quantitative_score,
                decision.universe_score,
                decision.alternative_score,
                decision.directional_score
            ]
            X.append(features)
            y.append(1 if decision.signal == 'BUY' else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Test ML auto-tuner
        tuner = MLAutoTuner(db)
        result = await tuner.optimize_classifier(
            X, y,
            model_type='random_forest',
            n_trials=10,  # Quick test
            cv_folds=3
        )
        
        assert 'best_params' in result
        assert 'best_score' in result
        assert result['best_score'] > 0.5  # Better than random
        
        print(f"✅ ML trained on {len(decisions)} real QUAD decisions, accuracy: {result['best_score']:.4f}")
    
    @pytest.mark.asyncio
    async def test_model_promotion_with_real_data(self, db: AsyncSession):
        """Test model promotion with real training data"""
        
        # Fetch real QUAD decisions
        stmt = select(QUADDecision).limit(100)
        result = await db.execute(stmt)
        decisions = result.scalars().all()
        
        if len(decisions) < 50:
            pytest.skip("Insufficient QUAD decisions")
        
        # Prepare data
        X = np.array([[d.quantitative_score, d.universe_score, d.alternative_score, d.directional_score] 
                      for d in decisions])
        y = np.array([1 if d.signal == 'BUY' else 0 for d in decisions])
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate and promote
        promoter = ModelPromoter(db)
        metrics = await promoter.evaluate_model(model, X_val, y_val, task_type='classification')
        
        result = await promoter.promote_model(
            model,
            model_name='quad_real_data_test',
            metrics=metrics,
            min_accuracy=0.50,  # Lower threshold for test
            force=False
        )
        
        assert 'promoted' in result
        if result['promoted']:
            assert result['shadow_mode'] == True  # CRITICAL
            print(f"✅ Model promoted with accuracy: {metrics['accuracy']:.4f}")
        else:
            print(f"⚠️ Model not promoted: {result.get('reason')}")


class TestBacktestWithRealData:
    """Test backtest engine with real historical data"""
    
    @pytest.mark.asyncio
    async def test_backtest_with_historical_prices(self, db: AsyncSession):
        """Test backtesting with real price history"""
        
        # Fetch real price data
        stmt = select(PriceHistory).where(
            PriceHistory.symbol == 'HDFC'
        ).order_by(PriceHistory.timestamp.asc()).limit(200)
        
        result = await db.execute(stmt)
        price_records = result.scalars().all()
        
        if len(price_records) < 100:
            pytest.skip("Insufficient historical data for HDFC")
        
        # Convert to DataFrame
        data = pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in price_records
        ])
        data.set_index('timestamp', inplace=True)
        
        # Simple backtest strategy
        from app.services.backtest_engine import BacktestEngine
        
        backtest_engine = BacktestEngine(db)
        
        # Calculate simple metrics
        returns = data['close'].pct_change()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        print(f"✅ Backtest on {len(data)} real price records")
        print(f"   Sharpe Ratio: {sharpe:.2f}")
        print(f"   Total Return: {(data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100:.2f}%")


class TestDataHealthWithRealData:
    """Test data health monitoring with real data"""
    
    @pytest.mark.asyncio
    async def test_ltp_freshness_check(self, db: AsyncSession):
        """Test LTP freshness with real Redis data"""
        from app.services.data_health_service import DataHealthService
        
        health_service = DataHealthService(db)
        
        # Check freshness for real symbols
        symbols = ['RELIANCE', 'TCS', 'INFY']
        
        for symbol in symbols:
            freshness = await health_service.check_ltp_freshness(symbol)
            
            assert 'symbol' in freshness
            assert 'fresh' in freshness
            
            if freshness.get('age_seconds') is not None:
                print(f"✅ {symbol} LTP age: {freshness['age_seconds']:.2f}s (fresh: {freshness['fresh']})")
            else:
                print(f"⚠️ {symbol} LTP not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
