"""Alpha Vantage data source client."""

import os
import httpx
from typing import Optional

BASE_URL = "https://www.alphavantage.co/query"


def get_api_key() -> str:
    """Get Alpha Vantage API key from environment."""
    key = os.getenv("ALPHAVANTAGE_API_KEY", "")
    if not key:
        raise ValueError("ALPHAVANTAGE_API_KEY not set in environment")
    return key


async def fetch_fundamental_overview(symbol: str) -> Optional[dict]:
    """Fetch company fundamental overview.
    
    Returns: earnings, PE ratio, PB ratio, dividend yield, etc.
    Note: Alpha Vantage uses full symbol format (e.g., 'BBCA.JK' for IDX)
    """
    try:
        api_key = get_api_key()
        idx_symbol = f"{symbol.upper()}.JKT" if not symbol.endswith(".JKT") else symbol
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(BASE_URL, params={
                "function": "OVERVIEW",
                "symbol": idx_symbol,
                "apikey": api_key,
            })
            data = response.json()
            
            if "Symbol" not in data:
                return None
            return data
    except Exception:
        return None


async def fetch_income_statement(symbol: str) -> Optional[dict]:
    """Fetch income statement data."""
    try:
        api_key = get_api_key()
        idx_symbol = f"{symbol.upper()}.JKT" if not symbol.endswith(".JKT") else symbol
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(BASE_URL, params={
                "function": "INCOME_STATEMENT",
                "symbol": idx_symbol,
                "apikey": api_key,
            })
            data = response.json()
            
            if "annualReports" not in data:
                return None
            return data
    except Exception:
        return None


async def fetch_balance_sheet(symbol: str) -> Optional[dict]:
    """Fetch balance sheet data."""
    try:
        api_key = get_api_key()
        idx_symbol = f"{symbol.upper()}.JKT" if not symbol.endswith(".JKT") else symbol
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(BASE_URL, params={
                "function": "BALANCE_SHEET",
                "symbol": idx_symbol,
                "apikey": api_key,
            })
            data = response.json()
            
            if "annualReports" not in data:
                return None
            return data
    except Exception:
        return None


async def fetch_forex_rate(from_currency: str = "USD", to_currency: str = "IDR") -> Optional[dict]:
    """Fetch real-time forex exchange rate."""
    try:
        api_key = get_api_key()
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(BASE_URL, params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "apikey": api_key,
            })
            data = response.json()
            
            if "Realtime Currency Exchange Rate" not in data:
                return None
            return data["Realtime Currency Exchange Rate"]
    except Exception:
        return None
