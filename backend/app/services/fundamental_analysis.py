from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class FundamentalAnalysisService:
    """
    Formalized service for Fundamental Analysis.
    Normalizes metrics into comparable 0-100 scores across 4 pillars:
    1. Growth (Sales, Profit)
    2. Profitability (ROE, Margins)
    3. Valuation (PE, PEG)
    4. Solvency (Debt/Equity, Current Ratio)
    """

    def calculate_score(self, metrics: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate comprehensive fundamental score (0-100).
        Returns: (Total Score, Details Dict)
        """
        if not metrics:
            return 0.0, {"error": "No data"}

        details = {}

        # 1. Growth Score (25%)
        # Benchmarks: Sales Growth > 15%, Profit Growth > 15%
        g_score = 0
        sales_g = metrics.get('sales_growth', 0)
        profit_g = metrics.get('profit_growth', 0)
        
        if sales_g > 20: g_score += 50
        elif sales_g > 10: g_score += 30
        elif sales_g > 0: g_score += 10
        
        if profit_g > 20: g_score += 50
        elif profit_g > 10: g_score += 30
        elif profit_g > 0: g_score += 10
        
        details['growth_score'] = min(100, g_score)

        # 2. Profitability Score (25%)
        # Benchmarks: ROE > 15%, OPM > 20%
        p_score = 0
        roe = metrics.get('roe', 0)
        opm = metrics.get('opm_percent', 0) or metrics.get('profit_margin', 0)
        
        if roe > 20: p_score += 50
        elif roe > 15: p_score += 40
        elif roe > 10: p_score += 20
        
        if opm > 20: p_score += 50
        elif opm > 15: p_score += 30
        elif opm > 10: p_score += 10
        
        details['profitability_score'] = min(100, p_score)

        # 3. Valuation Score (25%)
        # Benchmarks: PE < 25 (sector dependent ideally, but absolute for now), PEG < 1
        v_score = 0
        pe = metrics.get('pe_ratio', 100)
        peg = metrics.get('peg_ratio', 5) # Default high if missing
        
        if 0 < pe < 15: v_score += 60
        elif 15 <= pe < 25: v_score += 40
        elif 25 <= pe < 40: v_score += 20
        
        if 0 < peg < 1: v_score += 40
        elif 1 <= peg < 1.5: v_score += 20
        
        # Penalize negative PE
        if pe < 0: v_score = 0
        
        details['valuation_score'] = min(100, v_score)

        # 4. Solvency Score (25%)
        # Benchmarks: D/E < 0.5, Current Ratio > 1.5
        s_score = 0
        de = metrics.get('debt_to_equity', 10)
        cr = metrics.get('current_ratio', 0)
        
        if de < 0.1: s_score += 60
        elif de < 0.5: s_score += 50
        elif de < 1.0: s_score += 30
        
        if cr > 1.5: s_score += 40
        elif cr > 1.0: s_score += 20
        
        details['solvency_score'] = min(100, s_score)

        # Weighted Average
        total_score = (
            details['growth_score'] * 0.25 +
            details['profitability_score'] * 0.25 +
            details['valuation_score'] * 0.25 +
            details['solvency_score'] * 0.25
        )
        
        return round(total_score, 1), details
