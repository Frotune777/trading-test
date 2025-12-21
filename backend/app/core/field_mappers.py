"""
Field Mappers for Different Data Sources
Maps source-specific field names to standard schema
"""

from typing import Dict


class YahooFinanceMapper:
    """Maps Yahoo Finance (yfinance) fields to standard schema"""
    
    # Price data mapping
    PRICE_MAP: Dict[str, str] = {
        'currentPrice': 'last_price',
        'regularMarketPrice': 'last_price',
        'previousClose': 'previous_close',
        'regularMarketChange': 'change',
        'regularMarketChangePercent': 'change_percent',
        'regularMarketOpen': 'open',
        'regularMarketDayHigh': 'high',
        'dayHigh': 'high',
        'regularMarketDayLow': 'low',
        'dayLow': 'low',
        'volume': 'volume',
        'regularMarketVolume': 'volume',
        'marketCap': 'market_cap',
        'fiftyTwoWeekHigh': 'week_high_52',
        'fiftyTwoWeekLow': 'week_low_52',
    }
    
    # Company info mapping
    COMPANY_MAP: Dict[str, str] = {
        'symbol': 'symbol',
        'longName': 'company_name',
        'shortName': 'company_name',
        'sector': 'sector',
        'industry': 'industry',
        'marketCap': 'market_cap',
        'exchange': 'exchange',
    }
    
    # Fundamental data mapping
    FUNDAMENTAL_MAP: Dict[str, str] = {
        'trailingPE': 'pe_ratio',
        'forwardPE': 'pe_ratio',
        'priceToBook': 'pb_ratio',
        'returnOnEquity': 'roe',
        'bookValue': 'book_value',
        'dividendYield': 'dividend_yield',
        'trailingEps': 'eps',
        'epsTrailingTwelveMonths': 'eps',
        'debtToEquity': 'debt_to_equity',
        'currentRatio': 'current_ratio',
        'priceToSalesTrailing12Months': 'price_to_sales',
        'profitMargins': 'profit_margin',
    }


class NSEMapper:
    """Maps NSE fields to standard schema"""
    
    PRICE_MAP: Dict[str, str] = {
        'lastPrice': 'last_price',
        'LastTradedPrice': 'last_price',
        'pChange': 'change_percent',
        'PercentChange': 'change_percent',
        'change': 'change',
        'Change': 'change',
        'previousClose': 'previous_close',
        'PreviousClose': 'previous_close',
        'open': 'open',
        'Open': 'open',
        'dayHigh': 'high',
        'High': 'high',
        'dayLow': 'low',
        'Low': 'low',
        'totalTradedVolume': 'volume',
        'volume': 'volume',
        'vwap': 'vwap',
        'VWAP': 'vwap',
    }
    
    COMPANY_MAP: Dict[str, str] = {
        'symbol': 'symbol',
        'companyName': 'company_name',
        'industry': 'industry',
        'isin': 'isin',
    }


class ScreenerMapper:
    """Maps Screener.in fields to standard schema"""
    
    # Screener uses more human-readable names
    FUNDAMENTAL_MAP: Dict[str, str] = {
        'Stock P/E': 'pe_ratio',
        'Price to Book': 'pb_ratio',
        'ROE': 'roe',
        'ROCE': 'roce',
        'Dividend Yield': 'dividend_yield',
        'Book Value': 'book_value',
        'EPS': 'eps',
        'Debt to Equity': 'debt_to_equity',
        'Current Ratio': 'current_ratio',
        'Sales Growth': 'sales_growth',
        'Profit Growth': 'profit_growth',
        'Market Cap': 'market_cap',
    }
    
    COMPANY_MAP: Dict[str, str] = {
        'symbol': 'symbol',
        'company_name': 'company_name',
        'Name': 'company_name',
        'Sector': 'sector',
        'sector': 'sector',
        'Industry': 'industry',
        'industry': 'industry',
    }

    PRICE_MAP: Dict[str, str] = {
        'last_price': 'last_price',
        'Current Price': 'last_price',
        'CMP': 'last_price',
        'High': 'week_high_52',
        'Low': 'week_low_52',
        'market_cap': 'market_cap',
        'Market Cap': 'market_cap',
    }


# Reverse mappings for easy lookup
REVERSE_MAPPERS = {
    'yahoo': YahooFinanceMapper,
    'nse': NSEMapper,
    'screener': ScreenerMapper,
}
