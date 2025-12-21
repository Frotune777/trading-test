"""
Technical analysis examples using historical data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hybrid_aggregator import HybridAggregator
from data_sources.nse_complete import NSEComplete
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)


def calculate_moving_averages(df, periods=[20, 50, 200]):
    """Calculate simple moving averages."""
    for period in periods:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
    return df


def calculate_rsi(df, period=14):
    """Calculate RSI indicator."""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df


def example_moving_averages():
    """Calculate and display moving averages."""
    print("\n" + "="*70)
    print("TECHNICAL ANALYSIS: Moving Averages")
    print("="*70)
    
    aggregator = HybridAggregator()
    
    # Get 1 year of daily data
    data = aggregator.get_stock_data('TCS')
    df = data.get('historical_prices')
    
    if df is None or df.empty:
        print("No historical data available")
        return
    
    # Calculate MAs
    df = calculate_moving_averages(df, periods=[20, 50, 200])
    
    # Get latest values
    latest = df.iloc[-1]
    
    print(f"\n📊 TCS Moving Averages:\n")
    print(f"Current Price: ₹{latest['Close']:.2f}")
    print(f"SMA 20:        ₹{latest['SMA_20']:.2f}")
    print(f"SMA 50:        ₹{latest['SMA_50']:.2f}")
    print(f"SMA 200:       ₹{latest['SMA_200']:.2f}")
    
    # Trend analysis
    if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
        print("\n✅ Trend: Bullish (Price > SMA20 > SMA50)")
    elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
        print("\n❌ Trend: Bearish (Price < SMA20 < SMA50)")
    else:
        print("\n⚠️  Trend: Neutral")


def example_intraday_analysis():
    """Analyze intraday data."""
    print("\n" + "="*70)
    print("INTRADAY ANALYSIS: 5-Minute Data")
    print("="*70)
    
    nse = NSEComplete()
    
    # Get today's 5-minute data
    df = nse.get_intraday_data('NIFTY BANK', interval='5m')
    
    if df is None or df.empty:
        print("No intraday data available")
        return
    
    print(f"\n📊 NIFTY BANK Intraday Stats:\n")
    print(f"Open:    {df['Open'].iloc[0]:.2f}")
    print(f"High:    {df['High'].max():.2f}")
    print(f"Low:     {df['Low'].min():.2f}")
    print(f"Current: {df['Close'].iloc[-1]:.2f}")
    print(f"Range:   {df['High'].max() - df['Low'].min():.2f}")
    
    # Volume analysis
    avg_volume = df['Volume'].mean()
    current_volume = df['Volume'].iloc[-1]
    
    print(f"\n📊 Volume Analysis:")
    print(f"Average Volume: {avg_volume:,.0f}")
    print(f"Current Volume: {current_volume:,.0f}")
    
    if current_volume > avg_volume * 1.5:
        print("⚠️  High volume detected!")


def example_rsi_analysis():
    """Calculate RSI indicator."""
    print("\n" + "="*70)
    print("RSI INDICATOR ANALYSIS")
    print("="*70)
    
    aggregator = HybridAggregator()
    
    data = aggregator.get_stock_data('TCS')
    df = data.get('historical_prices')
    
    if df is None or df.empty:
        print("No historical data available")
        return
    
    # Calculate RSI
    df = calculate_rsi(df, period=14)
    
    latest_rsi = df['RSI'].iloc[-1]
    
    print(f"\n📊 TCS RSI(14): {latest_rsi:.2f}")
    
    if latest_rsi > 70:
        print("⚠️  Overbought (RSI > 70)")
    elif latest_rsi < 30:
        print("✅ Oversold (RSI < 30)")
    else:
        print("➡️  Neutral (30 < RSI < 70)")


if __name__ == '__main__':
    example_moving_averages()
    example_intraday_analysis()
    example_rsi_analysis()