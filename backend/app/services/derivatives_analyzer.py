import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any

class DerivativesAnalyzer:
    """
    Analyzes Derivatives Data (Options & Futures).
    Features:
    - PCR (Put Call Ratio) Analysis
    - Max Pain Calculation
    - Futures Buildup Detection (Long/Short)
    """
    
    def __init__(self):
        pass

    def analyze_option_chain(self, chain_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Option Chain DataFrame.
        Expected columns: ['strike_price', 'option_type', 'open_interest', 'volume', 'last_price']
        Returns: Dict with PCR, Max Pain, Sentiment.
        """
        if chain_df.empty:
            return {'error': 'No option chain data', 'sentiment': 'NEUTRAL'}

        # Split CE and PE
        ce_df = chain_df[chain_df['option_type'] == 'CE']
        pe_df = chain_df[chain_df['option_type'] == 'PE']

        # 1. PCR (Open Interest)
        total_ce_oi = ce_df['open_interest'].sum()
        total_pe_oi = pe_df['open_interest'].sum()
        
        pcr_oi = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
        
        # PCR Interpretation
        sentiment = 'NEUTRAL'
        if pcr_oi > 1.2: sentiment = 'BULLISH' # Strong support
        elif pcr_oi < 0.6: sentiment = 'BEARISH' # Strong resistance
        elif pcr_oi > 1.5: sentiment = 'OVERSOLD' # Potential Reversal Up (or extremely bullish)
        
        # 2. Max Pain
        # Strike where option writers lose the least amount of money
        # Loss for Writer = (Spot - Strike) if ITM
        # We simulate Spot Price at each Strike
        strikes = sorted(chain_df['strike_price'].unique())
        min_loss = float('inf')
        max_pain_strike = 0
        
        # Simplified Max Pain: Minimize (Sum(Intrinsic Value * OI))
        # This is a heavy calculation if many strikes. We can optimize or fallback.
        # Let's do exact calc for top 20 active strikes to save time if needed or all if small.
        
        for strike in strikes:
            # Assume expiry price = strike
            # CE Loss: max(0, expiry - k) * OI
            ce_loss = np.sum(np.maximum(0, strike - ce_df['strike_price']) * ce_df['open_interest'])
            # PE Loss: max(0, k - expiry) * OI
            pe_loss = np.sum(np.maximum(0, pe_df['strike_price'] - strike) * pe_df['open_interest'])
            
            total_loss = ce_loss + pe_loss
            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = strike
                
        return {
            'total_ce_oi': int(total_ce_oi),
            'total_pe_oi': int(total_pe_oi),
            'pcr_oi': pcr_oi,
            'max_pain': max_pain_strike,
            'sentiment': sentiment
        }

    def analyze_futures_buildup(self, current_price: float, prev_price: float, current_oi: int, prev_oi: int) -> str:
        """
        Determine Futures Buildup Interpretation.
        """
        price_change = current_price - prev_price
        oi_change = current_oi - prev_oi
        
        if price_change > 0 and oi_change > 0:
            return "Long Buildup" # Price Up, OI Up (Bullish)
        elif price_change < 0 and oi_change > 0:
            return "Short Buildup" # Price Down, OI Up (Bearish)
        elif price_change < 0 and oi_change < 0:
            return "Long Unwinding" # Price Down, OI Down (Mildly Bearish)
        elif price_change > 0 and oi_change < 0:
            return "Short Covering" # Price Up, OI Down (Bullish)
            
        return "Neutral"
