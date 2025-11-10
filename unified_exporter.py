"""
Master Unified Exporter - Combines NSE + Screener + Validation
Replaces all individual export scripts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.hybrid_aggregator import HybridAggregator
import pandas as pd
from datetime import datetime
import json


class UnifiedExporter:
    """
    Export everything from NSE + Screener in one organized structure.
    
    Output structure:
    stock_data/
    ├── TCS/
    │   ├── metadata.json
    │   ├── market_data/
    │   │   ├── current_price.csv
    │   │   ├── historical_daily.csv
    │   │   ├── intraday_5m.csv
    │   │   ├── corporate_actions.csv
    │   │   └── option_chain.csv
    │   └── fundamentals/
    │       ├── key_metrics.csv
    │       ├── quarterly_results.csv
    │       ├── profit_loss.csv
    │       ├── balance_sheet.csv
    │       ├── cash_flow.csv
    │       ├── ratios.csv
    │       ├── shareholding.csv
    │       └── peer_comparison.csv
    """
    
    def __init__(self, output_dir: str = 'stock_data'):
        self.output_dir = Path(output_dir)
        self.aggregator = HybridAggregator()
    
    def export_complete(self, symbol: str):
        """Export everything for a symbol."""
        print(f"\n{'='*80}")
        print(f"📊 EXPORTING COMPLETE DATA FOR {symbol}")
        print(f"{'='*80}\n")
        
        # Get all data
        data = self.aggregator.get_complete_analysis(symbol)
        
        # Create folders
        symbol_dir = self.output_dir / symbol
        market_dir = symbol_dir / 'market_data'
        fundamental_dir = symbol_dir / 'fundamentals'
        
        for dir in [market_dir, fundamental_dir]:
            dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            'symbol': symbol,
            'export_timestamp': datetime.now().isoformat(),
            'files_created': [],
            'data_sources': data.get('data_sources', {})
        }
        
        # Export market data (NSE)
        print("📈 Exporting Market Data (NSE)...")
        self._export_market_data(data, market_dir, summary)
        
        # Export fundamentals (Screener)
        print("\n💰 Exporting Fundamentals (Screener)...")
        self._export_fundamentals(data, fundamental_dir, summary)
        
        # Save metadata
        self._save_metadata(symbol_dir, summary)
        
        # Print summary
        self._print_summary(symbol, summary)
        
        return symbol_dir
    
    def _export_market_data(self, data, market_dir, summary):
        """Export all NSE market data."""
        
        # Current price
        if data.get('price'):
            df = pd.DataFrame([data['price']])
            file = market_dir / 'current_price.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ Current Price")
        
        # Historical daily
        if data.get('historical_daily') is not None:
            df = data['historical_daily']
            file = market_dir / 'historical_daily.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ Historical Daily ({len(df)} days)")
        
        # Intraday
        if data.get('intraday') is not None:
            df = data['intraday']
            file = market_dir / 'intraday_5m.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ Intraday 5m ({len(df)} intervals)")
        
        # Corporate actions
        if data.get('corporate_actions') is not None:
            df = data['corporate_actions']
            file = market_dir / 'corporate_actions.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ Corporate Actions ({len(df)} events)")
        
        # Option chain
        if data.get('option_chain') is not None:
            df = data['option_chain']
            file = market_dir / 'option_chain.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ Option Chain ({len(df)} strikes)")
        
        # 52 week high/low
        if data.get('52week_high_low'):
            df = pd.DataFrame([data['52week_high_low']])
            file = market_dir / '52week_high_low.csv'
            df.to_csv(file, index=False)
            summary['files_created'].append(str(file.name))
            print(f"  ✅ 52 Week High/Low")
    
    def _export_fundamentals(self, data, fundamental_dir, summary):
        """Export all Screener fundamental data."""
        
        fundamental_items = {
            'key_metrics': 'Key Metrics',
            'quarterly_results': 'Quarterly Results',
            'profit_loss': 'Profit & Loss',
            'balance_sheet': 'Balance Sheet',
            'cash_flow': 'Cash Flow',
            'ratios': 'Financial Ratios',
            'shareholding': 'Shareholding Pattern',
            'peer_comparison': 'Peer Comparison'
        }
        
        for key, label in fundamental_items.items():
            item_data = data.get(key)
            
            if item_data is not None:
                if isinstance(item_data, dict):
                    # Convert dict to DataFrame
                    df = pd.DataFrame([item_data])
                else:
                    df = item_data
                
                file = fundamental_dir / f'{key}.csv'
                df.to_csv(file, index=False)
                summary['files_created'].append(str(file.name))
                
                if isinstance(df, pd.DataFrame):
                    print(f"  ✅ {label} ({df.shape[0]}x{df.shape[1]})")
                else:
                    print(f"  ✅ {label}")
    
    def _save_metadata(self, symbol_dir, summary):
        """Save export metadata."""
        metadata_file = symbol_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def _print_summary(self, symbol, summary):
        """Print export summary."""
        print(f"\n{'='*80}")
        print(f"✅ EXPORT COMPLETE FOR {symbol}")
        print(f"{'='*80}")
        print(f"\n📁 Location: {self.output_dir / symbol}")
        print(f"📊 Files Created: {len(summary['files_created'])}")
        print(f"📅 Timestamp: {summary['export_timestamp']}")
        print(f"\n🔍 Data Sources:")
        for source, available in summary['data_sources'].items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"   {source}: {status}")
    
    def export_to_excel(self, symbol: str, filename: str = None):
        """Export everything to a single Excel file with multiple sheets."""
        if filename is None:
            filename = f"{symbol}_complete_analysis.xlsx"
        
        print(f"\n📊 Exporting {symbol} to Excel: {filename}")
        
        data = self.aggregator.get_complete_analysis(symbol)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Market Data Sheets
            if data.get('price'):
                pd.DataFrame([data['price']]).to_excel(writer, sheet_name='Current_Price', index=False)
            
            if data.get('historical_daily') is not None:
                data['historical_daily'].to_excel(writer, sheet_name='Historical_Daily', index=False)
            
            if data.get('intraday') is not None:
                data['intraday'].to_excel(writer, sheet_name='Intraday_5m', index=False)
            
            if data.get('corporate_actions') is not None:
                data['corporate_actions'].to_excel(writer, sheet_name='Corporate_Actions', index=False)
            
            # Fundamental Sheets
            if data.get('key_metrics'):
                pd.DataFrame([data['key_metrics']]).to_excel(writer, sheet_name='Key_Metrics', index=False)
            
            if data.get('quarterly_results') is not None:
                data['quarterly_results'].to_excel(writer, sheet_name='Quarterly_Results', index=False)
            
            if data.get('profit_loss') is not None:
                data['profit_loss'].to_excel(writer, sheet_name='Profit_Loss', index=False)
            
            if data.get('balance_sheet') is not None:
                data['balance_sheet'].to_excel(writer, sheet_name='Balance_Sheet', index=False)
            
            if data.get('cash_flow') is not None:
                data['cash_flow'].to_excel(writer, sheet_name='Cash_Flow', index=False)
            
            if data.get('ratios') is not None:
                data['ratios'].to_excel(writer, sheet_name='Ratios', index=False)
            
            if data.get('shareholding') is not None:
                data['shareholding'].to_excel(writer, sheet_name='Shareholding', index=False)
            
            if data.get('peer_comparison') is not None:
                data['peer_comparison'].to_excel(writer, sheet_name='Peer_Comparison', index=False)
        
        print(f"✅ Saved to {filename}")
        return filename


def main():
    """Example usage."""
    exporter = UnifiedExporter()
    
    symbol = input("Enter stock symbol (e.g., TCS, INFY, RELIANCE): ").strip().upper()
    
    print("\nChoose export format:")
    print("1. CSV (organized folders)")
    print("2. Excel (single file)")
    print("3. Both")
    
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        exporter.export_complete(symbol)
    
    if choice in ['2', '3']:
        exporter.export_to_excel(symbol)


if __name__ == "__main__":
    main()