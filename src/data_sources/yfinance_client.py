"""yfinance data source client for IDX stocks."""

import yfinance as yf
import pandas as pd
from typing import Optional


def get_idx_symbol(symbol: str) -> str:
    """Convert symbol to IDX format (append .JK if not present)."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".JK"):
        symbol = f"{symbol}.JK"
    return symbol


def fetch_stock_data(symbol: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV data from yfinance.
    
    Args:
        symbol: Stock symbol (e.g., 'BBCA' or 'BBCA.JK')
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
        interval: Data interval (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
    
    Returns:
        DataFrame with OHLCV data or None if failed
    """
    try:
        ticker = yf.Ticker(get_idx_symbol(symbol))
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def fetch_stock_info(symbol: str) -> Optional[dict]:
    """Fetch stock info (fundamental data) from yfinance.
    
    Returns dict with keys like: sector, industry, marketCap, trailingPE, 
    priceToBook, returnOnEquity, debtToEquity, profitMargins, etc.
    """
    try:
        ticker = yf.Ticker(get_idx_symbol(symbol))
        info = ticker.info
        if not info or "symbol" not in info:
            return None
        return info
    except Exception:
        return None


def fetch_market_index(index_symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
    """Fetch market index data.
    
    Common indices:
        ^JKSE - IHSG (Jakarta Composite)
        ^GSPC - S&P 500
        ^HSI  - Hang Seng
        USDIDR=X - USD/IDR exchange rate
    """
    try:
        ticker = yf.Ticker(index_symbol)
        df = ticker.history(period=period)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def fetch_multiple_stocks(symbols: list[str], period: str = "6mo") -> dict[str, pd.DataFrame]:
    """Fetch data for multiple stocks at once."""
    results = {}
    idx_symbols = [get_idx_symbol(s) for s in symbols]
    
    try:
        data = yf.download(idx_symbols, period=period, group_by="ticker", progress=False)
        for orig_symbol, idx_symbol in zip(symbols, idx_symbols):
            if len(idx_symbols) == 1:
                df = data
            else:
                df = data[idx_symbol] if idx_symbol in data.columns.get_level_values(0) else pd.DataFrame()
            if not df.empty:
                results[orig_symbol.upper()] = df
    except Exception:
        pass
    
    return results
