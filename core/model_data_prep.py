# core/model_data_prep.py
"""
Model Data Preparation Engine
Prepares data for different financial models
Production-ready with data quality checks
Version: 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelDataPrep:
    """
    Prepare data for financial models
    Handles data aggregation, cleaning, and validation
    """
    
    def __init__(self, nse, db):
        self.nse = nse
        self.db = db
    
    # ========================================================================
    # PRICE PREDICTION MODEL DATA
    # ========================================================================
    
    def prepare_price_prediction_data(
        self,
        symbol: str,
        lookback_days: int = 365
    ) -> Dict:
        """
        Prepare data for price prediction models (LSTM, ARIMA, etc.)
        
        Required Data:
        - Historical prices (OHLCV)
        - Company fundamentals
        - Corporate actions (splits, dividends)
        - FII/DII activity
        - Market indicators (Index P/E)
        
        Returns:
            Dict with all required features
        """
        
        logger.info(f"Preparing price prediction data for {symbol}")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            # 1. Historical Prices (Core data)
            price_history = self.db.get_price_history(symbol, days=lookback_days)
            if price_history.empty:
                logger.warning(f"No price history for {symbol}")
                data['data_quality']['price_history'] = 'MISSING'
            else:
                data['features']['price_history'] = price_history
                data['data_quality']['price_history'] = 'OK'
                
                # Calculate technical features
                data['features']['returns'] = price_history['close'].pct_change()
                data['features']['log_returns'] = np.log(price_history['close'] / price_history['close'].shift(1))
                data['features']['volatility'] = data['features']['returns'].rolling(20).std()
            
            # 2. Company Information
            company_info = self.db.get_company(symbol)
            snapshot = self.db.get_snapshot(symbol)
            
            if company_info:
                data['features']['company_info'] = {
                    'sector': company_info.get('sector'),
                    'industry': company_info.get('industry'),
                    'market_cap': snapshot.get('market_cap') if snapshot else None,
                    'pe_ratio': snapshot.get('pe_ratio') if snapshot else None,
                    'pb_ratio': snapshot.get('pb_ratio') if snapshot else None
                }
                data['data_quality']['company_info'] = 'OK'
            else:
                data['data_quality']['company_info'] = 'MISSING'
            
            # 3. Corporate Actions
            try:
                # Get corporate actions for the period
                end_date = datetime.now().strftime('%d-%m-%Y')
                start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%d-%m-%Y')
                
                corp_actions = self.nse.get_corporate_action(
                    from_date_str=start_date,
                    to_date_str=end_date
                )
                
                if corp_actions is not None and not corp_actions.empty:
                    # Filter for this symbol
                    symbol_actions = corp_actions[corp_actions['symbol'] == symbol] if 'symbol' in corp_actions.columns else pd.DataFrame()
                    data['features']['corporate_actions'] = symbol_actions
                    data['data_quality']['corporate_actions'] = 'OK'
                else:
                    data['data_quality']['corporate_actions'] = 'NO_DATA'
            except Exception as e:
                logger.error(f"Error fetching corporate actions: {e}")
                data['data_quality']['corporate_actions'] = 'ERROR'
            
            # 4. FII/DII Activity
            try:
                fii_dii = self.nse.fii_dii_activity()
                if fii_dii is not None:
                    data['features']['fii_dii_activity'] = fii_dii
                    data['data_quality']['fii_dii'] = 'OK'
                else:
                    data['data_quality']['fii_dii'] = 'NO_DATA'
            except Exception as e:
                logger.error(f"Error fetching FII/DII: {e}")
                data['data_quality']['fii_dii'] = 'ERROR'
            
            # 5. Market Indicators
            try:
                index_pe = self.nse.get_index_pe_ratio()
                index_pb = self.nse.get_index_pb_ratio()
                
                data['features']['market_indicators'] = {
                    'index_pe': index_pe,
                    'index_pb': index_pb
                }
                data['data_quality']['market_indicators'] = 'OK'
            except Exception as e:
                logger.error(f"Error fetching market indicators: {e}")
                data['data_quality']['market_indicators'] = 'ERROR'
            
            # Overall data quality score
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing price prediction data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # VOLATILITY MODEL DATA
    # ========================================================================
    
    def prepare_volatility_model_data(
        self,
        symbol: str,
        lookback_days: int = 180
    ) -> Dict:
        """
        Prepare data for volatility models (GARCH, Stochastic Vol, etc.)
        
        Required Data:
        - Live option chain (IV surface)
        - Futures data (term structure)
        - Historical prices (realized volatility)
        - Market depth (liquidity)
        """
        
        logger.info(f"Preparing volatility data for {symbol}")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            # 1. Historical Prices for Realized Volatility
            price_history = self.db.get_price_history(symbol, days=lookback_days)
            
            if not price_history.empty:
                returns = price_history['close'].pct_change().dropna()
                
                # Calculate realized volatility
                data['features']['realized_volatility'] = {
                    'daily_vol': returns.std(),
                    'annualized_vol': returns.std() * np.sqrt(252),
                    'rolling_vol_20d': returns.rolling(20).std(),
                    'rolling_vol_60d': returns.rolling(60).std(),
                    'price_history': price_history
                }
                data['data_quality']['price_history'] = 'OK'
            else:
                data['data_quality']['price_history'] = 'MISSING'
            
            # 2. Live Option Chain (Implied Volatility)
            try:
                option_chain = self.nse.get_live_option_chain(symbol)
                
                if option_chain is not None:
                    data['features']['option_chain'] = option_chain
                    data['data_quality']['option_chain'] = 'OK'
                else:
                    data['data_quality']['option_chain'] = 'NO_DATA'
            except Exception as e:
                logger.error(f"Error fetching option chain: {e}")
                data['data_quality']['option_chain'] = 'ERROR'
            
            # 3. Futures Data
            try:
                futures = self.nse.futures_data(symbol)
                
                if futures is not None:
                    data['features']['futures_data'] = futures
                    data['data_quality']['futures'] = 'OK'
                else:
                    data['data_quality']['futures'] = 'NO_DATA'
            except Exception as e:
                logger.error(f"Error fetching futures: {e}")
                data['data_quality']['futures'] = 'ERROR'
            
            # 4. Market Depth
            try:
                market_depth = self.nse.get_market_depth(symbol)
                
                if market_depth is not None:
                    data['features']['market_depth'] = market_depth
                    data['data_quality']['market_depth'] = 'OK'
                else:
                    data['data_quality']['market_depth'] = 'NO_DATA'
            except Exception as e:
                logger.error(f"Error fetching market depth: {e}")
                data['data_quality']['market_depth'] = 'ERROR'
            
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing volatility data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # SENTIMENT ANALYSIS DATA
    # ========================================================================
    
    def prepare_sentiment_data(
        self,
        symbol: str,
        lookback_days: int = 90
    ) -> Dict:
        """
        Prepare data for sentiment analysis
        
        Required Data:
        - FII/DII activity (institutional sentiment)
        - Bulk deals (large investor activity)
        - Insider trading (management confidence)
        - Gainers/Losers (market mood)
        - Advance/Decline (breadth)
        """
        
        logger.info(f"Preparing sentiment data for {symbol}")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            # Date range
            end_date = datetime.now().strftime('%d-%m-%Y')
            start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%d-%m-%Y')
            
            # 1. FII/DII Activity
            try:
                fii_dii = self.nse.fii_dii_activity()
                data['features']['fii_dii'] = fii_dii
                data['data_quality']['fii_dii'] = 'OK' if fii_dii is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['fii_dii'] = 'ERROR'
            
            # 2. Bulk Deals
            try:
                bulk_deals = self.nse.get_bulk_deals(from_date=start_date, to_date=end_date)
                
                if bulk_deals is not None and not bulk_deals.empty:
                    symbol_deals = bulk_deals[bulk_deals['symbol'] == symbol] if 'symbol' in bulk_deals.columns else pd.DataFrame()
                    data['features']['bulk_deals'] = symbol_deals
                    data['data_quality']['bulk_deals'] = 'OK'
                else:
                    data['data_quality']['bulk_deals'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['bulk_deals'] = 'ERROR'
            
            # 3. Insider Trading
            try:
                insider = self.nse.get_insider_trading(from_date=start_date, to_date=end_date)
                
                if insider is not None and not insider.empty:
                    symbol_insider = insider[insider['symbol'] == symbol] if 'symbol' in insider.columns else pd.DataFrame()
                    data['features']['insider_trading'] = symbol_insider
                    data['data_quality']['insider_trading'] = 'OK'
                else:
                    data['data_quality']['insider_trading'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['insider_trading'] = 'ERROR'
            
            # 4. Gainers/Losers (Market Sentiment)
            try:
                gainers_losers = self.nse.get_gainers_losers()
                data['features']['gainers_losers'] = gainers_losers
                data['data_quality']['gainers_losers'] = 'OK' if gainers_losers is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['gainers_losers'] = 'ERROR'
            
            # 5. Advance/Decline
            try:
                adv_dec = self.nse.get_advance_decline()
                data['features']['advance_decline'] = adv_dec
                data['data_quality']['advance_decline'] = 'OK' if adv_dec is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['advance_decline'] = 'ERROR'
            
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing sentiment data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # PORTFOLIO OPTIMIZATION DATA
    # ========================================================================
    
    def prepare_portfolio_data(
        self,
        symbols: List[str],
        lookback_days: int = 365
    ) -> Dict:
        """
        Prepare data for portfolio optimization (Markowitz, Black-Litterman, etc.)
        
        Required Data:
        - Historical prices (correlation, covariance)
        - Index details (benchmark)
        - Company info (constraints)
        - Corporate actions (adjustments)
        """
        
        logger.info(f"Preparing portfolio data for {len(symbols)} stocks")
        
        data = {
            'symbols': symbols,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            # 1. Collect historical prices for all symbols
            price_data = {}
            
            for symbol in symbols:
                prices = self.db.get_price_history(symbol, days=lookback_days)
                if not prices.empty:
                    price_data[symbol] = prices[['date', 'close']].set_index('date')
            
            if price_data:
                # Combine into single DataFrame
                combined_prices = pd.concat(price_data, axis=1)
                combined_prices.columns = list(price_data.keys())
                
                # Calculate returns
                returns = combined_prices.pct_change().dropna()
                
                data['features']['price_matrix'] = combined_prices
                data['features']['returns_matrix'] = returns
                data['features']['correlation_matrix'] = returns.corr()
                data['features']['covariance_matrix'] = returns.cov()
                
                # Portfolio statistics
                data['features']['mean_returns'] = returns.mean()
                data['features']['volatility'] = returns.std()
                data['features']['sharpe_ratios'] = returns.mean() / returns.std()
                
                data['data_quality']['price_data'] = 'OK'
            else:
                data['data_quality']['price_data'] = 'MISSING'
            
            # 2. Company Information
            company_data = {}
            for symbol in symbols:
                info = self.db.get_company(symbol)
                snapshot = self.db.get_snapshot(symbol)
                if info:
                    company_data[symbol] = {
                        'sector': info.get('sector'),
                        'industry': info.get('industry'),
                        'market_cap': snapshot.get('market_cap') if snapshot else None
                    }
            
            data['features']['company_data'] = company_data
            data['data_quality']['company_data'] = 'OK' if company_data else 'MISSING'
            
            # 3. Index Details (Benchmark)
            try:
                nifty50 = self.nse.get_index_details('NIFTY 50', list_only=False)
                data['features']['benchmark'] = nifty50
                data['data_quality']['benchmark'] = 'OK' if nifty50 is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['benchmark'] = 'ERROR'
            
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing portfolio data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # OPTIONS TRADING DATA
    # ========================================================================
    
    def prepare_options_trading_data(
        self,
        symbol: str,
        expiry: Optional[str] = None
    ) -> Dict:
        """
        Prepare data for options trading strategies
        
        Required Data:
        - Live option chain
        - Historical option chain
        - Underlying price history
        - Most active options
        """
        
        logger.info(f"Preparing options trading data for {symbol}")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            # 1. Live Option Chain
            try:
                live_chain = self.nse.get_live_option_chain(symbol, expiry_date=expiry)
                data['features']['live_option_chain'] = live_chain
                data['data_quality']['live_chain'] = 'OK' if live_chain is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['live_chain'] = 'ERROR'
            
            # 2. Static Option Chain (for structure)
            try:
                static_chain = self.nse.get_option_chain(symbol)
                data['features']['option_chain'] = static_chain
                data['data_quality']['static_chain'] = 'OK' if static_chain is not None else 'NO_DATA'
            except Exception as e:
                data['data_quality']['static_chain'] = 'ERROR'
            
            # 3. Underlying Price History
            price_history = self.db.get_price_history(symbol, days=90)
            if not price_history.empty:
                data['features']['price_history'] = price_history
                data['data_quality']['price_history'] = 'OK'
            else:
                data['data_quality']['price_history'] = 'MISSING'
            
            # 4. Most Active Options
            try:
                active_calls = self.nse.most_active_stock_calls()
                active_puts = self.nse.most_active_stock_puts()
                
                data['features']['most_active'] = {
                    'calls': active_calls,
                    'puts': active_puts
                }
                data['data_quality']['most_active'] = 'OK'
            except Exception as e:
                data['data_quality']['most_active'] = 'ERROR'
            
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing options data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # EVENT-DRIVEN STRATEGY DATA
    # ========================================================================
    
    def prepare_event_driven_data(
        self,
        symbol: str,
        lookback_days: int = 180
    ) -> Dict:
        """
        Prepare data for event-driven strategies
        
        Required Data:
        - Corporate actions (dividends, splits, etc.)
        - Upcoming results calendar
        - Corporate announcements
        - Insider trading
        """
        
        logger.info(f"Preparing event-driven data for {symbol}")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'data_quality': {},
            'features': {}
        }
        
        try:
            end_date = datetime.now().strftime('%d-%m-%Y')
            start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%d-%m-%Y')
            
            # 1. Corporate Actions
            try:
                corp_actions = self.nse.get_corporate_action(
                    from_date_str=start_date,
                    to_date_str=end_date
                )
                
                if corp_actions is not None and not corp_actions.empty:
                    symbol_actions = corp_actions[corp_actions['symbol'] == symbol] if 'symbol' in corp_actions.columns else pd.DataFrame()
                    data['features']['corporate_actions'] = symbol_actions
                    data['data_quality']['corporate_actions'] = 'OK'
                else:
                    data['data_quality']['corporate_actions'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['corporate_actions'] = 'ERROR'
            
            # 2. Upcoming Results
            try:
                results_cal = self.nse.get_upcoming_results_calendar()
                
                if results_cal is not None and not results_cal.empty:
                    symbol_results = results_cal[results_cal['symbol'] == symbol] if 'symbol' in results_cal.columns else pd.DataFrame()
                    data['features']['upcoming_results'] = symbol_results
                    data['data_quality']['upcoming_results'] = 'OK'
                else:
                    data['data_quality']['upcoming_results'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['upcoming_results'] = 'ERROR'
            
            # 3. Corporate Announcements
            try:
                announcements = self.nse.get_corporate_announcement(
                    from_date_str=start_date,
                    to_date_str=end_date
                )
                
                if announcements is not None and not announcements.empty:
                    symbol_announcements = announcements[announcements['symbol'] == symbol] if 'symbol' in announcements.columns else pd.DataFrame()
                    data['features']['announcements'] = symbol_announcements
                    data['data_quality']['announcements'] = 'OK'
                else:
                    data['data_quality']['announcements'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['announcements'] = 'ERROR'
            
            # 4. Insider Trading
            try:
                insider = self.nse.get_insider_trading(from_date=start_date, to_date=end_date)
                
                if insider is not None and not insider.empty:
                    symbol_insider = insider[insider['symbol'] == symbol] if 'symbol' in insider.columns else pd.DataFrame()
                    data['features']['insider_trading'] = symbol_insider
                    data['data_quality']['insider_trading'] = 'OK'
                else:
                    data['data_quality']['insider_trading'] = 'NO_DATA'
            except Exception as e:
                data['data_quality']['insider_trading'] = 'ERROR'
            
            # 5. Price history around events
            price_history = self.db.get_price_history(symbol, days=lookback_days)
            if not price_history.empty:
                data['features']['price_history'] = price_history
                data['data_quality']['price_history'] = 'OK'
            else:
                data['data_quality']['price_history'] = 'MISSING'
            
            data['quality_score'] = self._calculate_quality_score(data['data_quality'])
            
            return data
        
        except Exception as e:
            logger.error(f"Error preparing event-driven data: {e}")
            data['error'] = str(e)
            return data
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_quality_score(self, quality_dict: Dict) -> float:
        """
        Calculate overall data quality score
        
        Returns:
            Float between 0 and 1
        """
        if not quality_dict:
            return 0.0
        
        scores = {
            'OK': 1.0,
            'NO_DATA': 0.5,
            'MISSING': 0.0,
            'ERROR': 0.0
        }
        
        total_score = sum(scores.get(status, 0) for status in quality_dict.values())
        max_score = len(quality_dict)
        
        return total_score / max_score if max_score > 0 else 0.0
    
    def export_for_talib(self, price_history: pd.DataFrame) -> Dict:
        """
        Export price data in format ready for TA-Lib
        
        Returns:
            Dict with numpy arrays for TA-Lib functions
        """
        if price_history.empty:
            return {}
        
        return {
            'open': price_history['open'].values,
            'high': price_history['high'].values,
            'low': price_history['low'].values,
            'close': price_history['close'].values,
            'volume': price_history['volume'].values
        }