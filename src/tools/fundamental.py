"""MCP Tool: get_fundamental_data - Fetch fundamental analysis data."""

import json
from ..data_sources.yfinance_client import fetch_stock_info
from ..data_sources.alphavantage_client import fetch_fundamental_overview
from ..utils.cache import fundamental_cache, get_cache_key


async def get_fundamental_data(symbol: str) -> str:
    """Get fundamental data for a stock (valuation, profitability, growth).
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA', 'BBRI', 'TLKM')
    
    Returns:
        JSON with PER, PBV, ROE, DER, margins, growth metrics
    """
    cache_key = get_cache_key("fundamental", symbol)
    if cache_key in fundamental_cache:
        return fundamental_cache[cache_key]
    
    # Primary: yfinance
    info = fetch_stock_info(symbol)
    
    # Secondary: Alpha Vantage (if available)
    av_data = await fetch_fundamental_overview(symbol)
    
    if info is None and av_data is None:
        return json.dumps({"error": f"No fundamental data found for {symbol}"})
    
    def safe_get(d, key, default=None):
        if d is None:
            return default
        val = d.get(key, default)
        if val == "None" or val == "":
            return default
        return val
    
    def safe_float(val, default=None):
        if val is None:
            return default
        try:
            return round(float(val), 2)
        except (ValueError, TypeError):
            return default
    
    # Build fundamental data from available sources
    result = {
        "symbol": symbol.upper(),
        "company_name": safe_get(info, "longName", safe_get(info, "shortName", symbol)),
        "sector": safe_get(info, "sector", "Unknown"),
        "industry": safe_get(info, "industry", "Unknown"),
        
        # Valuation
        "valuation": {
            "pe_ratio": safe_float(safe_get(info, "trailingPE")),
            "forward_pe": safe_float(safe_get(info, "forwardPE")),
            "pb_ratio": safe_float(safe_get(info, "priceToBook")),
            "ps_ratio": safe_float(safe_get(info, "priceToSalesTrailing12Months")),
            "ev_ebitda": safe_float(safe_get(info, "enterpriseToEbitda")),
            "market_cap": safe_get(info, "marketCap"),
            "enterprise_value": safe_get(info, "enterpriseValue"),
        },
        
        # Profitability
        "profitability": {
            "roe": safe_float(safe_get(info, "returnOnEquity"), default=None),
            "roa": safe_float(safe_get(info, "returnOnAssets"), default=None),
            "profit_margin": safe_float(safe_get(info, "profitMargins"), default=None),
            "operating_margin": safe_float(safe_get(info, "operatingMargins"), default=None),
            "gross_margin": safe_float(safe_get(info, "grossMargins"), default=None),
        },
        
        # Financial Health
        "financial_health": {
            "debt_to_equity": safe_float(safe_get(info, "debtToEquity"), default=None),
            "current_ratio": safe_float(safe_get(info, "currentRatio"), default=None),
            "quick_ratio": safe_float(safe_get(info, "quickRatio"), default=None),
            "total_debt": safe_get(info, "totalDebt"),
            "total_cash": safe_get(info, "totalCash"),
        },
        
        # Growth
        "growth": {
            "revenue_growth": safe_float(safe_get(info, "revenueGrowth"), default=None),
            "earnings_growth": safe_float(safe_get(info, "earningsGrowth"), default=None),
            "earnings_quarterly_growth": safe_float(safe_get(info, "earningsQuarterlyGrowth"), default=None),
        },
        
        # Dividend
        "dividend": {
            "dividend_yield": safe_float(safe_get(info, "dividendYield"), default=None),
            "dividend_rate": safe_float(safe_get(info, "dividendRate"), default=None),
            "payout_ratio": safe_float(safe_get(info, "payoutRatio"), default=None),
        },
        
        # Per Share
        "per_share": {
            "eps_trailing": safe_float(safe_get(info, "trailingEps"), default=None),
            "eps_forward": safe_float(safe_get(info, "forwardEps"), default=None),
            "book_value": safe_float(safe_get(info, "bookValue"), default=None),
            "revenue_per_share": safe_float(safe_get(info, "revenuePerShare"), default=None),
        },
    }
    
    # Enrich with Alpha Vantage data if available
    if av_data:
        if result["valuation"]["pe_ratio"] is None:
            result["valuation"]["pe_ratio"] = safe_float(safe_get(av_data, "TrailingPE"))
        if result["valuation"]["pb_ratio"] is None:
            result["valuation"]["pb_ratio"] = safe_float(safe_get(av_data, "PriceToBookRatio"))
        if result["profitability"]["roe"] is None:
            result["profitability"]["roe"] = safe_float(safe_get(av_data, "ReturnOnEquityTTM"))
        if result["growth"]["revenue_growth"] is None:
            result["growth"]["revenue_growth"] = safe_float(safe_get(av_data, "QuarterlyRevenueGrowthYOY"))
    
    # Convert ROE/margins from decimal to percentage if needed
    for key in ["roe", "roa", "profit_margin", "operating_margin", "gross_margin"]:
        val = result["profitability"].get(key)
        if val is not None and -1 <= val <= 1:
            result["profitability"][key] = round(val * 100, 2)
    
    for key in ["revenue_growth", "earnings_growth", "earnings_quarterly_growth"]:
        val = result["growth"].get(key)
        if val is not None and -1 <= val <= 1:
            result["growth"][key] = round(val * 100, 2)
    
    if result["dividend"]["dividend_yield"] is not None and result["dividend"]["dividend_yield"] <= 1:
        result["dividend"]["dividend_yield"] = round(result["dividend"]["dividend_yield"] * 100, 2)
    
    response = json.dumps(result, ensure_ascii=False)
    fundamental_cache[cache_key] = response
    return response
