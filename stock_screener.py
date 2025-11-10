"""
Fundamental Stock Screener using Screener.in data
Filter stocks based on ROE, P/E, Debt, Growth, etc.
"""

from core.hybrid_aggregator import HybridAggregator
import pandas as pd
from typing import List
import time
import re


class FundamentalScreener:
    """Screen stocks based on fundamental criteria."""
    
    def __init__(self):
        self.aggregator = HybridAggregator()
    
    def screen_stocks(
        self,
        symbols: List[str],
        min_roe: float = None,
        max_pe: float = None,
        min_roce: float = None,
        min_div_yield: float = None
    ) -> pd.DataFrame:
        """
        Screen stocks based on fundamental filters.
        
        Args:
            symbols: List of stock symbols to screen
            min_roe: Minimum ROE% (e.g., 15)
            max_pe: Maximum P/E ratio (e.g., 30)
            min_roce: Minimum ROCE% (e.g., 15)
            min_div_yield: Minimum dividend yield% (e.g., 1.0)
        
        Returns:
            DataFrame with filtered stocks
        """
        results = []
        
        print(f"\n🔍 Screening {len(symbols)} stocks...\n")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
            
            try:
                data = self.aggregator.get_fundamental_data(symbol)
                
                if not data or not data.get('key_metrics'):
                    print(f"  ⚠️  No data available")
                    continue
                
                metrics = data['key_metrics']
                
                # Extract numeric values
                roe = self._extract_number(metrics.get('ROE', '0'))
                pe = self._extract_number(metrics.get('Stock P/E', '999'))
                roce = self._extract_number(metrics.get('ROCE', '0'))
                div_yield = self._extract_number(metrics.get('Dividend Yield', '0'))
                
                # Apply filters
                passed = True
                
                if min_roe and roe < min_roe:
                    print(f"  ❌ ROE {roe}% < {min_roe}%")
                    passed = False
                
                if max_pe and pe > max_pe:
                    print(f"  ❌ P/E {pe} > {max_pe}")
                    passed = False
                
                if min_roce and roce < min_roce:
                    print(f"  ❌ ROCE {roce}% < {min_roce}%")
                    passed = False
                
                if min_div_yield and div_yield < min_div_yield:
                    print(f"  ❌ Div Yield {div_yield}% < {min_div_yield}%")
                    passed = False
                
                if passed:
                    print(f"  ✅ Passed - ROE:{roe}% P/E:{pe} ROCE:{roce}%")
                    
                    results.append({
                        'Symbol': symbol,
                        'Company': data.get('company_info', {}).get('company_name', symbol),
                        'Market Cap': metrics.get('Market Cap', 'N/A'),
                        'Current Price': metrics.get('Current Price', 'N/A'),
                        'P/E': pe,
                        'ROE %': roe,
                        'ROCE %': roce,
                        'Div Yield %': div_yield,
                        'Book Value': metrics.get('Book Value', 'N/A')
                    })
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            # Rate limiting
            time.sleep(1)
        
        if results:
            df = pd.DataFrame(results)
            return df.sort_values('ROE %', ascending=False)
        else:
            return pd.DataFrame()
    
    def _extract_number(self, value: str) -> float:
        """Extract numeric value from string like '15.5%' or '₹1,234'."""
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols, commas, %, etc.
        cleaned = re.sub(r'[₹,\s%]', '', str(value))
        try:
            return float(cleaned)
        except:
            return 0.0


def main():
    """Example usage."""
    screener = FundamentalScreener()
    
    # IT sector stocks
    it_stocks = ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS']
    
    print("\n🔍 Screening IT Stocks...")
    print("Criteria: ROE > 15%, P/E < 30, ROCE > 15%\n")
    
    filtered = screener.screen_stocks(
        symbols=it_stocks,
        min_roe=15,
        max_pe=30,
        min_roce=15
    )
    
    print("\n" + "="*100)
    print("✅ FILTERED RESULTS")
    print("="*100)
    if not filtered.empty:
        print(filtered.to_string(index=False))
        
        # Save to Excel
        filtered.to_excel('screened_it_stocks.xlsx', index=False)
        print(f"\n💾 Saved to screened_it_stocks.xlsx")
    else:
        print("No stocks matched the criteria")


if __name__ == "__main__":
    main()