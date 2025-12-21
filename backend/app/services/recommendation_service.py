
from typing import List, Dict, Optional
import pandas as pd
import logging
from datetime import datetime

from .mtf_analyzer import MTFDataManager
from .technical_analysis import TechnicalAnalysisService
from .screener_engine import ScreenerEngine
from .signal_generator import SignalGenerator
from ..database.db_manager import DatabaseManager
from ..data_sources.nse_complete import NSEComplete

logger = logging.getLogger(__name__)

class RecommendationService:
    """
    Orchestrates Fundamental and Technical analysis to generate stock recommendations.
    """
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db = DatabaseManager(db_path)
        self.nse = NSEComplete()
        self.mtf = MTFDataManager(self.db, self.nse)
        # ScreenerEngine needs data, will init on demand or load all
        self.company_data = None
        
    def _load_fundamental_data(self):
        """Load fundamental data for all companies."""
        # Simple join of company info + latest metrics
        # For now, we mock/fetch basic
        companies = self.db.get_all_companies()
        data = []
        for c in companies:
            # Fetch fundamentals
            f = self.db.get_latest_fundamentals(c['symbol'])
            if f:
                f['symbol'] = c['symbol']
                data.append(f)
        return pd.DataFrame(data)

    def generate_recommendations(self, strategy: str = 'balanced', limit: int = 10) -> List[Dict]:
        """
        Generate recommendations based on strategy.
        Strategies: 'growth', 'value', 'momentum', 'balanced'
        """
        logger.info(f"Generating recommendations for strategy: {strategy}")
        
        # Load data if needed
        if self.company_data is None:
            self.company_data = self._load_fundamental_data()
            self.screener = ScreenerEngine(self.company_data)
        
        # 1. Fundamental Screening
        candidates = self._apply_fundamental_filters(strategy)
        logger.info(f"Fundamental screen returned {len(candidates)} candidates")
        
        results = []
        
        for symbol in candidates:
            try:
                # 2. Technical Scoring
                tech_score, tech_details, tech_signals = self._calculate_technical_score(symbol)
                
                # 3. Fundamental Scoring
                fund_score, fund_details = self._calculate_fundamental_score(symbol, strategy)
                
                # 4. Smart Score (Weighted Average)
                # Balanced: 50/50, Growth: 40/60, Momentum: 70/30
                w_tech, w_fund = self._get_weights(strategy)
                smart_score = round((tech_score * w_tech) + (fund_score * w_fund), 2)
                
                # Decision
                # Use SignalGenerator for actionable levels
                # We need the daily analyzed df which is internal to calculate_technical_score currently
                # Let's clean this up. _calculate_technical_score should probably return the df or the signals.
                
                # Signal Generator Integration
                # Since we already ran TA in _calculate_technical_score, let's optimize.
                # However, _calculate_technical_score recreates TA service.
                # For cleaner code, let's allow _calculate_technical_score to return signals too.
                
                # Update: _calculate_technical_score now returns (score, details, signals)
                tech_score, tech_details, tech_signals = self._calculate_technical_score(symbol)
                
                # Refine Action based on Signals if available
                generated_action = 'HOLD'
                stop_loss = None
                target_price = None
                
                if tech_signals:
                    # Prioritize the most recent signal
                    latest_sig = tech_signals[-1] # List of dicts
                    generated_action = latest_sig['action']
                    stop_loss = latest_sig['stop_loss']
                    target_price = latest_sig['target_price']
                
                # Combine Smart Score action with Signal Action
                # If Smart Score says BUY and Signal says BUY -> STRONG BUY
                smart_action = self._determine_action(smart_score)
                
                # Final Action Logic
                final_action = smart_action
                if smart_action == 'HOLD' and generated_action != 'HOLD':
                     # If neutral score but specific signal (e.g. oversold), maybe upgrade to WATCH/ACCUMULATE?
                     # For simplicity, stick to smart_action unless strong conflict.
                     pass
                     
                # Explanation
                explanation = self._generate_explanation(symbol, tech_score, fund_score, tech_details, fund_details, final_action)
                
                recommendation = {
                    'symbol': symbol,
                    'smart_score': smart_score,
                    'action': final_action,
                    'technical_score': tech_score,
                    'fundamental_score': fund_score,
                    'technical_details': tech_details,
                    'fundamental_details': fund_details,
                    'explanation': explanation,
                    'strategy': strategy
                }
                
                if stop_loss: recommendation['stop_loss'] = stop_loss
                if target_price: recommendation['target_price'] = target_price
                
                results.append(recommendation)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
                
        # Sort by Smart Score descending
        results.sort(key=lambda x: x['smart_score'], reverse=True)
        return results[:limit]

    def _generate_explanation(self, symbol, tech_score, fund_score, tech_details, fund_details, action):
        """Generate 'Why this stock?' explanation."""
        reasons = []
        
        # Action context
        if action in ['STRONG_BUY', 'BUY']:
            reasons.append(f"**{symbol}** is a **{action}** candidate.")
        elif action in ['STRONG_SELL', 'SELL']:
             reasons.append(f"**{symbol}** shows weakness (**{action}**).")
        else:
            reasons.append(f"**{symbol}** is currently in a **HOLD** phase.")
            
        # Fundamental Highlights
        good_funds = []
        if fund_details.get('roe', 0) > 15: good_funds.append(f"strong ROE ({fund_details['roe']}%)")
        if fund_details.get('profit_margin', 0) > 15: good_funds.append(f"healthy margins ({fund_details['profit_margin']}%)")
        if fund_details.get('sales_growth', 0) > 10: good_funds.append(f"robust growth ({fund_details['sales_growth']}%)")
        
        if good_funds:
            reasons.append(f"Fundamentally, it boasts {', '.join(good_funds)}.")
        elif fund_score < 40:
            reasons.append("Fundamentals appear weak relative to peers.")

        # Technical Highlights
        trend = tech_details.get('trend', 'NEUTRAL')
        reasons.append(f"Technically, the trend is **{trend}**.")
        
        if tech_details.get('ma_alignment'):
            reasons.append("Moving averages are aligned for an uptrend.")
            
        rsi = tech_details.get('rsi')
        if rsi:
            if rsi > 70: reasons.append(f"RSI is overbought ({rsi}), suggesting caution.")
            elif rsi < 30: reasons.append(f"RSI is oversold ({rsi}), potential bounce.")
            else: reasons.append(f"Momentum is stable (RSI {rsi}).")
            
        return " ".join(reasons)
    
    def _apply_fundamental_filters(self, strategy: str) -> List[str]:
        """Get initial list of stocks based on strategy."""
        if self.company_data is None or self.company_data.empty:
            return []
            
        conditions = []
        if strategy == 'value':
            conditions.append({"field": "pe_ratio", "operator": "<", "value": 25})
            conditions.append({"field": "roe", "operator": ">", "value": 15})
        elif strategy == 'growth':
            conditions.append({"field": "sales_growth", "operator": ">", "value": 15})
            conditions.append({"field": "profit_growth", "operator": ">", "value": 15})
            
        filtered_df = self.screener.run_screen(conditions)
        return filtered_df['symbol'].tolist()

    def _calculate_fundamental_score(self, symbol: str, strategy: str) -> tuple[float, Dict]:
        """
        Calculate fundamental score (0-100).
        """
        if self.company_data is None: return 0.0, {}
        
        row = self.company_data[self.company_data['symbol'] == symbol]
        if row.empty: return 0.0, {}
        
        metrics = row.iloc[0].to_dict()
        score = 50.0
        
        # Scoring logic
        if metrics.get('roe', 0) > 20: score += 10
        if metrics.get('pe_ratio', 100) < 20: score += 10
        if metrics.get('debt_to_equity', 1) < 0.5: score += 10
        if metrics.get('sales_growth', 0) > 10: score += 10
        if metrics.get('profit_margin', 0) > 15: score += 10
        
        return min(100.0, score), metrics

    def _calculate_technical_score(self, symbol: str) -> tuple[float, Dict, List[Dict]]:
        """
        Calculate technical score (0-100) using MTF analysis.
        Uses Daily, Weekly, and Hourly data.
        """
        score = 50.0 # Neutral starting point
        details = {'signals': [], 'trend': 'NEUTRAL'}
        
        # Fetch Data
        timeframes = ['1d', '1w'] 
        data = self.mtf.get_mtf_data(symbol, timeframes)
        
        if '1d' not in data or data['1d'].empty:
            return 0.0, {'error': 'No daily data'}, []
            
        # Daily Analysis (TA-Lib)
        daily_ta = TechnicalAnalysisService(data['1d'])
        daily_ta.add_trend_indicators()
        daily_ta.add_momentum_indicators()
        df = daily_ta.df
        
        # Signal Generation
        sig_gen = SignalGenerator(df)
        signals = sig_gen.generate_signals()
        
        if df.empty: return 0.0, {}, []
        
        current = df.iloc[-1]
        
        # 1. Trend (Moving Averages) (30 pts)
        # Price > SMA200 (+10), SMA50 > SMA200 (+10), Price > SMA50 (+10)
        trend_score = 0
        if current['close'] > current['sma_200']: trend_score += 10
        if current['sma_50'] > current['sma_200']: trend_score += 10
        if current['close'] > current['sma_50']: trend_score += 10
        
        # 2. Momentum (RSI) (20 pts)
        # RSI 40-60 (Neutral), 60-80 (Bullish +20), >80 (Overbought +10), <30 (Oversold -10)
        mom_score = 0
        rsi = current['rsi']
        if 50 < rsi < 70: mom_score = 20
        elif rsi >= 70: mom_score = 10 # Caution
        elif rsi <= 30: mom_score = 10 # Bounce potential
        elif 40 <= rsi <= 50: mom_score = 5
        
        # 3. MACD (20 pts)
        # Histogram Positive (+10), MACD > Signal (+10)
        macd_score = 0
        if current['macd_hist'] > 0: macd_score += 10
        if current['macd'] > current['macd_signal']: macd_score += 10
        
        # 4. Weekly Trend (MTF Confirmation) (30 pts)
        # If Weekly close > Weekly SMA20
        weekly_score = 0
        if '1w' in data and not data['1w'].empty:
            w_ta = TechnicalAnalysisService(data['1w'])
            w_ta.add_trend_indicators()
            w_curr = w_ta.df.iloc[-1]
            if w_curr['close'] > w_curr['sma_20']: weekly_score = 30
            
        total_tech = trend_score + mom_score + macd_score + weekly_score
        
        # Store details
        details['rsi'] = round(rsi, 2)
        details['trend'] = 'BULLISH' if total_tech > 60 else 'BEARISH' if total_tech < 40 else 'NEUTRAL'
        details['ma_alignment'] = trend_score == 30
        
        return min(100.0, total_tech), details, signals

    def _calculate_fundamental_score(self, symbol: str, strategy: str) -> tuple[float, Dict]:
        """
        Calculate fundamental score (0-100).
        """
        # Fetch processed fundamental data
        # For now, mock or simple db fetch
        # Ideally: self.screener.get_score(symbol)
        
        # Placeholder logic
        return 60.0, {'metrics': 'Standard'}

    def _get_weights(self, strategy: str):
        if strategy == 'technical': return 0.8, 0.2
        if strategy == 'fundamental': return 0.2, 0.8
        return 0.5, 0.5 # Balanced

    def _determine_action(self, score: float) -> str:
        if score >= 80: return 'STRONG_BUY'
        if score >= 65: return 'BUY'
        if score <= 20: return 'STRONG_SELL'
        if score <= 35: return 'SELL'
        return 'HOLD'
