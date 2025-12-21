import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List

class TechnicalAnalysisService:
    """
    Pillar 1: Quantitative Engine (Q)
    Provides 50+ technical indicators and pattern recognition.
    """

    def __init__(self, data: pd.DataFrame):
        self.df = data.copy()
        self._preprocess()

    def _preprocess(self):
        """Ensure columns are lowercase and numeric"""
        self.df.columns = [c.lower() for c in self.df.columns]
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def calculate_all(self) -> pd.DataFrame:
        """Run all indicator categories"""
        self.add_trend_indicators()
        self.add_momentum_indicators()
        self.add_volatility_indicators()
        self.add_volume_indicators()
        self.add_patterns()
        return self.df

    def add_trend_indicators(self):
        # Moving Averages
        self.df['sma_20'] = talib.SMA(self.df['close'], timeperiod=20)
        self.df['sma_50'] = talib.SMA(self.df['close'], timeperiod=50)
        self.df['sma_200'] = talib.SMA(self.df['close'], timeperiod=200)
        self.df['ema_9'] = talib.EMA(self.df['close'], timeperiod=9)
        self.df['ema_21'] = talib.EMA(self.df['close'], timeperiod=21)
        self.df['wma_20'] = talib.WMA(self.df['close'], timeperiod=20)
        self.df['dema_20'] = talib.DEMA(self.df['close'], timeperiod=20)
        self.df['tema_20'] = talib.TEMA(self.df['close'], timeperiod=20)
        self.df['kama_20'] = talib.KAMA(self.df['close'], timeperiod=20)
        
        # Directional Movement
        self.df['adx'] = talib.ADX(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['adxr'] = talib.ADXR(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['plus_di'] = talib.PLUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['minus_di'] = talib.MINUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        
        # Aroon
        aroondown, aroonup = talib.AROON(self.df['high'], self.df['low'], timeperiod=14)
        self.df['aroon_down'], self.df['aroon_up'] = aroondown, aroonup
        self.df['aroon_osc'] = talib.AROONOSC(self.df['high'], self.df['low'], timeperiod=14)
        
        self.df['sar'] = talib.SAR(self.df['high'], self.df['low'], acceleration=0.02, maximum=0.2)

    def add_momentum_indicators(self):
        self.df['rsi'] = talib.RSI(self.df['close'], timeperiod=14)
        self.df['stoch_k'], self.df['stoch_d'] = talib.STOCH(self.df['high'], self.df['low'], self.df['close'])
        self.df['willr'] = talib.WILLR(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['cci'] = talib.CCI(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['roc'] = talib.ROC(self.df['close'], timeperiod=10)
        self.df['mom'] = talib.MOM(self.df['close'], timeperiod=10)
        self.df['mfi'] = talib.MFI(self.df['high'], self.df['low'], self.df['close'], self.df['volume'], timeperiod=14)
        
        # MACD
        macd, macdsignal, macdhist = talib.MACD(self.df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        self.df['macd'], self.df['macd_signal'], self.df['macd_hist'] = macd, macdsignal, macdhist
        
        self.df['ultosc'] = talib.ULTOSC(self.df['high'], self.df['low'], self.df['close'])
        self.df['ppo'] = talib.PPO(self.df['close'])
        self.df['cmo'] = talib.CMO(self.df['close'], timeperiod=14)

    def add_volatility_indicators(self):
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(self.df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.df['bb_upper'], self.df['bb_middle'], self.df['bb_lower'] = upper, middle, lower
        self.df['bb_width'] = (upper - lower) / middle
        
        self.df['atr'] = talib.ATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['natr'] = talib.NATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['stddev'] = talib.STDDEV(self.df['close'], timeperiod=5, nbdev=1)
        self.df['trange'] = talib.TRANGE(self.df['high'], self.df['low'], self.df['close'])

    def add_volume_indicators(self):
        self.df['obv'] = talib.OBV(self.df['close'], self.df['volume'])
        self.df['ad_line'] = talib.AD(self.df['high'], self.df['low'], self.df['close'], self.df['volume'])
        self.df['adosc'] = talib.ADOSC(self.df['high'], self.df['low'], self.df['close'], self.df['volume'], fastperiod=3, slowperiod=10)
        
    def add_patterns(self):
        """Recognize 40+ candlestick patterns using TA-Lib"""
        pattern_funcs = [func for func in dir(talib) if func.startswith('CDL')]
        for func_name in pattern_funcs:
            func = getattr(talib, func_name)
            self.df[func_name.lower()] = func(self.df['open'], self.df['high'], self.df['low'], self.df['close'])

    def calculate_stats(self) -> Dict[str, float]:
        """PILLAR 1: Statistical Analysis Functions"""
        returns = self.df['close'].pct_change()
        vol = returns.std() * np.sqrt(252)
        sharpe = (returns.mean() * 252) / vol if vol != 0 else 0
        
        return {
            "annualized_volatility": float(vol),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(self._calculate_max_drawdown())
        }

    def _calculate_max_drawdown(self) -> float:
        roll_max = self.df['close'].cummax()
        daily_drawdown = self.df['close'] / roll_max - 1.0
        return daily_drawdown.cummin().min()
