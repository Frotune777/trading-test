
from typing import List, Dict, Optional
import pandas as pd
import logging
from datetime import datetime

from .mtf_analyzer import MTFDataManager
from .technical_analysis import TechnicalAnalysisService
from .screener_engine import ScreenerEngine
from .signal_generator import SignalGenerator
from .fundamental_analysis import FundamentalAnalysisService
from .derivatives_analyzer import DerivativesAnalyzer
from .market_regime import MarketRegime
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
        
        # New Core Services
        self.fundamental_analyzer = FundamentalAnalysisService()
        self.derivatives_analyzer = DerivativesAnalyzer()
        self.market_regime = None # Will init with Nifty data
        
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
        
        # 0. Market Regime Score (10%)
        regime_score, regime_details = self._calculate_regime_score()
        logger.info(f"Market Regime: {regime_details['regime']} ({regime_score})")

        results = []
        
        for symbol in candidates:
            try:
                # 1. Technical Scoring & Signal Gen
                # Returns (Total Tech Score, Details with components, Signals)
                raw_tech_score, tech_details, tech_signals = self._calculate_technical_score(symbol)
                
                # Extract Components
                trend_score = tech_details.get('trend_component', 50)
                mom_score = tech_details.get('momentum_component', 50)
                
                # 2. Fundamental Scoring (30%)
                fund_score, fund_details = self._calculate_fundamental_score(symbol, strategy)
                
                # 3. Derivatives Scoring (10%)
                deriv_score, deriv_details = self._calculate_derivatives_score(symbol)
                
                # 4. Smart Score Calculation (5 Pillars)
                # Weights: Tech(30), Fund(30), Mom(20), Deriv(10), Regime(10)
                w_tech = 0.30
                w_fund = 0.30
                w_mom = 0.20
                w_deriv = 0.10
                w_regime = 0.10
                
                smart_score = (
                    (trend_score * w_tech) +
                    (fund_score * w_fund) +
                    (mom_score * w_mom) +
                    (deriv_score * w_deriv) +
                    (regime_score * w_regime)
                )
                smart_score = round(smart_score, 2)
                
                # Decision & Action
                generated_action = 'HOLD'
                stop_loss = None
                target_price = None
                
                if tech_signals:
                    latest_sig = tech_signals[-1]
                    generated_action = latest_sig['action']
                    stop_loss = latest_sig['stop_loss']
                    target_price = latest_sig['target_price']
                
                # Determine Final Action based on Score + Signal
                final_action = self._determine_action(smart_score)
                # Override if strong contradictory signal? For now, stick to score-based primary.
                     
                # Explanation
                explanation = self._generate_explanation(
                    symbol, 
                    tech_details, fund_details, deriv_details, regime_details,
                    smart_score, final_action
                )
                
                recommendation = {
                    'symbol': symbol,
                    'smart_score': smart_score,
                    'action': final_action,
                    'technical_score': raw_tech_score, # Legacy field
                    'fundamental_score': fund_score,
                    'technical_details': tech_details,
                    'fundamental_details': fund_details,
                    'derivatives_details': deriv_details,
                    'market_regime': regime_details,
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

    def _generate_explanation(self, symbol, tech, fund, deriv, regime, score, action):
        """Generate 'Why this stock?' explanation."""
        reasons = []
        
        # 1. Action & Score Context
        reasons.append(f"**{symbol}** is rated **{action}** (Score: {score}).")
        
        # 2. Market Context
        reasons.append(f"Market is **{regime.get('regime', 'NEUTRAL')}**.")
        
        # 3. Technical Drive
        trend = tech.get('trend', 'NEUTRAL')
        rsi = tech.get('rsi', 50)
        reasons.append(f"Trend is **{trend}** (RSI: {rsi}).")
        
        # 4. Fundamental Strength
        if fund.get('profitability_score', 0) > 70:
            reasons.append("Strong profitability metrics.")
        elif fund.get('valuation_score', 0) > 70:
            reasons.append("Attractive valuation.")
            
        # 5. Derivatives Insight
        pcr = deriv.get('pcr', 1.0)
        sentiment = deriv.get('sentiment', 'NEUTRAL')
        if sentiment != 'NEUTRAL':
             reasons.append(f"Derivatives suggest **{sentiment}** sentiment (PCR: {pcr}).")

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
        
        # Breakdown for 5-pillar model
        # Trend (30 + 30 weekly = 60 max) -> Normalize to 100
        details['trend_component'] = (trend_score + weekly_score) / 60.0 * 100.0
        # Momentum (RSI 20 + MACD 20 = 40 max) -> Normalize to 100
        details['momentum_component'] = (mom_score + macd_score) / 40.0 * 100.0
        
        return min(100.0, total_tech), details, signals

    def _calculate_fundamental_score(self, symbol: str, strategy: str) -> tuple[float, Dict]:
        """
        Calculate fundamental score (0-100) using FundamentalAnalysisService.
        """
        if self.company_data is None: return 0.0, {}
        
        row = self.company_data[self.company_data['symbol'] == symbol]
        if row.empty: return 0.0, {}
        
        metrics = row.iloc[0].to_dict()
        return self.fundamental_analyzer.calculate_score(metrics)

    def _calculate_derivatives_score(self, symbol: str) -> tuple[float, Dict]:
        """
        Calculate derivatives score (0-100) based on Option Chain and Futures.
        """
        try:
            # 1. Fetch Option Chain from DB
            records = self.db.get_latest_option_chain(symbol)
            if not records:
                return 50.0, {'sentiment': 'NEUTRAL', 'message': 'No derivatives data'}
            
            df = pd.DataFrame(records)
            analysis = self.derivatives_analyzer.analyze_option_chain(df)
            
            # Simple scoring logic for Smart Score
            # Neutral = 50, Bullish > 50, Bearish < 50
            derivatives_score = 50.0
            sentiment = analysis.get('sentiment', 'NEUTRAL')
            pcr = analysis.get('pcr_oi', 1.0)
            
            if sentiment == 'BULLISH': derivatives_score = 75.0
            if sentiment == 'OVERSOLD': derivatives_score = 85.0
            if sentiment == 'BEARISH': derivatives_score = 25.0
            
            # Adjust by PCR
            if pcr > 1.0: derivatives_score += (pcr - 1.0) * 10
            elif pcr < 1.0: derivatives_score -= (1.0 - pcr) * 10
            
            # Cap at 0-100
            derivatives_score = max(0.0, min(100.0, derivatives_score))
            
            return derivatives_score, analysis
        except Exception as e:
            logger.error(f"Error in derivatives scoring for {symbol}: {e}")
            return 50.0, {'sentiment': 'NEUTRAL', 'error': str(e)}

    def _calculate_regime_score(self) -> tuple[float, Dict]:
        """
        Calculate market regime score (0-100).
        """
        if not self.market_regime:
            # Init on demand
            nifty_data = self.mtf.get_mtf_data('NIFTY 50', ['1d']) # or simple history get
            # Fallback if NIFTY 50 symbol differs in DB
            if '1d' not in nifty_data or nifty_data['1d'].empty:
                 return 50.0, {'regime': 'UNKNOWN'}
            self.market_regime = MarketRegime(nifty_data['1d'])
            
        return self.market_regime.determine_regime()['market_score'], self.market_regime.determine_regime()

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
