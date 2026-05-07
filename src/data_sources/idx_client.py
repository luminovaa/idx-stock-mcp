"""IDX (Indonesia Stock Exchange) data source client.

Provides broker summary, foreign flow, and stock list data.
Uses publicly available IDX data endpoints.
"""

import httpx
from typing import Optional
from datetime import date, timedelta


IDX_BASE_URL = "https://www.idx.co.id/primary/TradingSummary"
IDX_STOCK_URL = "https://www.idx.co.id/primary/StockData"


async def fetch_broker_summary(symbol: str, trade_date: Optional[str] = None) -> Optional[dict]:
    """Fetch broker summary for a stock.
    
    Args:
        symbol: Stock symbol (e.g., 'BBCA')
        trade_date: Date in YYYY-MM-DD format (default: latest trading day)
    
    Returns:
        Dict with top buyers, top sellers, and net values
    """
    if trade_date is None:
        trade_date = date.today().strftime("%Y-%m-%d")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Try IDX API endpoint
            response = await client.get(
                f"{IDX_BASE_URL}/GetBrokerSummary",
                params={
                    "code": symbol.upper(),
                    "date": trade_date,
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data
    except Exception:
        return None


async def fetch_foreign_flow(symbol: str, days: int = 20) -> Optional[dict]:
    """Fetch foreign (asing) net buy/sell flow.
    
    Args:
        symbol: Stock symbol
        days: Number of days to look back
    
    Returns:
        Dict with daily foreign flow data
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 10)  # extra buffer for non-trading days
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{IDX_BASE_URL}/GetForeignFlow",
                params={
                    "code": symbol.upper(),
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data
    except Exception:
        return None


async def fetch_stock_list(index: str = "LQ45") -> Optional[list[str]]:
    """Fetch list of stocks in an index.
    
    Args:
        index: Index name (LQ45, IDX30, KOMPAS100, IDX80, ISSI)
    
    Returns:
        List of stock symbols
    """
    # Hardcoded common indices as fallback
    # These are updated periodically
    INDICES = {
        "LQ45": [
            "ACES", "ADRO", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI",
            "BBTN", "BMRI", "BRPT", "BUKA", "CPIN", "EMTK", "ESSA", "EXCL",
            "GGRM", "GOTO", "HRUM", "ICBP", "INCO", "INDF", "INKP", "INTP",
            "ITMG", "KLBF", "MAPI", "MDKA", "MEDC", "MIKA", "PGAS", "PGEO",
            "PTBA", "SMGR", "SMRA", "TBIG", "TINS", "TLKM", "TOWR", "TPIA",
            "UNTR", "UNVR", "WIKA",
        ],
        "IDX30": [
            "ADRO", "AMRT", "ASII", "BBCA", "BBNI", "BBRI", "BMRI", "BRPT",
            "CPIN", "EMTK", "ESSA", "GOTO", "HRUM", "ICBP", "INCO", "INDF",
            "INKP", "ITMG", "KLBF", "MDKA", "MEDC", "PGAS", "PTBA", "SMGR",
            "TBIG", "TLKM", "TOWR", "TPIA", "UNTR", "UNVR",
        ],
    }
    
    index = index.upper()
    
    # Try API first
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{IDX_STOCK_URL}/GetStockList",
                params={"index": index},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return [item.get("Code", item.get("code", "")) for item in data if item]
    except Exception:
        pass
    
    # Fallback to hardcoded
    return INDICES.get(index, INDICES.get("LQ45"))
