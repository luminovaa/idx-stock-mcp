"""Ajaib data source client.

Provides additional money flow and trading data for IDX stocks.
Note: Ajaib API access may require authentication.
"""

import os
import httpx
from typing import Optional


AJAIB_BASE_URL = "https://api.ajaib.co.id"


def get_api_key() -> str:
    """Get Ajaib API key from environment."""
    return os.getenv("AJAIB_API_KEY", "")


async def fetch_stock_detail(symbol: str) -> Optional[dict]:
    """Fetch stock detail from Ajaib.
    
    Returns: price, change, volume, market cap, etc.
    """
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{AJAIB_BASE_URL}/stocks/{symbol.upper()}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    except Exception:
        return None


async def fetch_net_buy_sell(symbol: str, days: int = 5) -> Optional[dict]:
    """Fetch net buy/sell data from Ajaib.
    
    Returns: daily net buy/sell values for the specified period
    """
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{AJAIB_BASE_URL}/stocks/{symbol.upper()}/flow",
                params={"days": days},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    except Exception:
        return None
