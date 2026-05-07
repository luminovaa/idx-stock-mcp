"""MCP Tool: get_stock_price - Fetch stock price and OHLCV data."""

import json
from datetime import datetime
from ..data_sources.yfinance_client import fetch_stock_data, fetch_stock_info
from ..utils.cache import price_cache, get_cache_key


async def get_stock_price(symbol: str, period: str = "1mo") -> str:
    """Get current stock price and historical OHLCV data.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA', 'TLKM', 'BBRI')
        period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y
    
    Returns:
        JSON string with current price, change, and OHLCV history
    """
    cache_key = get_cache_key("price", symbol, period)
    if cache_key in price_cache:
        return price_cache[cache_key]
    
    df = fetch_stock_data(symbol, period=period)
    if df is None or df.empty:
        return json.dumps({"error": f"No data found for {symbol}"})
    
    # Current price info
    latest = df.iloc[-1]
    prev_close = df.iloc[-2]["Close"] if len(df) > 1 else latest["Close"]
    change = latest["Close"] - prev_close
    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
    
    # Get additional info
    info = fetch_stock_info(symbol)
    
    result = {
        "symbol": symbol.upper(),
        "current_price": round(float(latest["Close"]), 2),
        "open": round(float(latest["Open"]), 2),
        "high": round(float(latest["High"]), 2),
        "low": round(float(latest["Low"]), 2),
        "close": round(float(latest["Close"]), 2),
        "volume": int(latest["Volume"]),
        "change": round(float(change), 2),
        "change_pct": round(float(change_pct), 2),
        "prev_close": round(float(prev_close), 2),
        "period": period,
        "data_points": len(df),
        "date_range": {
            "start": df.index[0].strftime("%Y-%m-%d"),
            "end": df.index[-1].strftime("%Y-%m-%d"),
        },
        "period_high": round(float(df["High"].max()), 2),
        "period_low": round(float(df["Low"].min()), 2),
        "avg_volume_20d": int(df["Volume"].tail(20).mean()) if len(df) >= 20 else int(df["Volume"].mean()),
    }
    
    if info:
        result["company_name"] = info.get("longName", info.get("shortName", ""))
        result["sector"] = info.get("sector", "")
        result["industry"] = info.get("industry", "")
        result["market_cap"] = info.get("marketCap", 0)
    
    # Recent 5 days OHLCV
    recent = df.tail(5)
    result["recent_5d"] = []
    for idx, row in recent.iterrows():
        result["recent_5d"].append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })
    
    response = json.dumps(result, ensure_ascii=False)
    price_cache[cache_key] = response
    return response
