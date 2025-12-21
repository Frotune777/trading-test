import pandas as pd
import numpy as np
from app.services.technical_analysis import TechnicalAnalysisService

class FeatureEngineeringPipeline:
    """
    PILLAR 4: Prediction Engine (P)
    Transforms raw OHLCV and fundamental data into a feature matrix.
    """

    def __init__(self, price_data: pd.DataFrame, fundamental_data: dict):
        self.df = price_data.copy()
        self.fundamentals = fundamental_data

    def generate_features(self) -> pd.DataFrame:
        """Execute all feature generation steps"""
        # 1. Technical Features (from quantitative engine)
        ta_service = TechnicalAnalysisService(self.df)
        self.df = ta_service.calculate_all()
        
        # 2. Return Features
        self._add_return_features()
        
        # 3. Time Features
        self._add_time_features()
        
        # 4. Fundamental Features
        self._add_fundamental_features()
        
        # 5. Target Variables (for training only)
        self._add_targets()
        
        return self.df.dropna()

    def _add_return_features(self):
        periods = [1, 5, 10, 20]
        for p in periods:
            self.df[f'return_{p}d'] = self.df['close'].pct_change(p)
        
        self.df['high_low_range'] = (self.df['high'] - self.df['low']) / self.df['close']
        self.df['gap_percent'] = (self.df['open'] - self.df['close'].shift(1)) / self.df['close'].shift(1)

    def _add_time_features(self):
        self.df.index = pd.to_datetime(self.df.index)
        self.df['day_of_week'] = self.df.index.dayofweek
        self.df['day_of_month'] = self.df.index.day
        self.df['month'] = self.df.index.month

    def _add_fundamental_features(self):
        # Map fundamental ratios to current price sequence (filled forward)
        # Note: In production, this would use point-in-time fundamental data
        for key, value in self.fundamentals.items():
            self.df[f'feat_{key.lower().replace(" ", "_")}'] = value

    def _add_targets(self):
        """Create prediction targets: 5-day future direction"""
        self.df['target_return_5d'] = self.df['close'].shift(-5) / self.df['close'] - 1
        self.df['target_direction_5d'] = (self.df['target_return_5d'] > 0.02).astype(int) # 1 if > 2% gain
