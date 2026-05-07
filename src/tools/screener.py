"""MCP Tools: get_stock_list, screen_stocks."""

import json
from ..data_sources.idx_client import fetch_stock_list
from ..data_sources.yfinance_client import fetch_stock_data, fetch_stock_info
from ..utils.indicators import calculate_rsi, calculate_adx, calculate_ema
from ..utils.cache import get_cache_key


async def get_stock_list(index: str = "LQ45") -> str:
    """Get list of stocks in an IDX index.
    
    Args:
        index: Index name - LQ45, IDX30, KOMPAS100, IDX80
    
    Returns:
        JSON with list of stock symbols in the index
    """
    stocks = await fetch_stock_list(index)
    
    if stocks is None:
        return json.dumps({"error": f"Could not fetch stock list for index {index}"})
    
    result = {
        "index": index.upper(),
        "count": len(stocks),
        "symbols": stocks,
    }
    
    return json.dumps(result, ensure_ascii=False)


async def screen_stocks(
    index: str = "LQ45",
    min_rsi: float = 30,
    max_rsi: float = 70,
    min_adx: float = 20,
    above_ema50: bool = True,
    limit: int = 20,
) -> str:
    """Screen stocks based on technical criteria.
    
    Filters stocks from an index based on technical indicators.
    Useful for finding candidates that might pass the gate system.
    
    Args:
        index: Index to screen (LQ45, IDX30)
        min_rsi: Minimum RSI value (default: 30)
        max_rsi: Maximum RSI value (default: 70)
        min_adx: Minimum ADX value for trend strength (default: 20)
        above_ema50: Only include stocks above EMA50 (default: True)
        limit: Maximum results to return (default: 20)
    
    Returns:
        JSON with filtered stock list and basic metrics
    """
    stocks = await fetch_stock_list(index)
    if stocks is None:
        return json.dumps({"error": f"Could not fetch stock list for {index}"})
    
    results = []
    errors = []
    
    for symbol in stocks:
        try:
            df = fetch_stock_data(symbol, period="3mo")
            if df is None or df.empty or len(df) < 30:
                continue
            
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            
            # Calculate indicators
            rsi = calculate_rsi(close)
            rsi_val = float(rsi.iloc[-1])
            
            adx_data = calculate_adx(high, low, close)
            adx_val = float(adx_data["adx"].iloc[-1])
            plus_di = float(adx_data["plus_di"].iloc[-1])
            minus_di = float(adx_data["minus_di"].iloc[-1])
            
            ema50 = calculate_ema(close, 50)
            ema50_val = float(ema50.iloc[-1])
            current_price = float(close.iloc[-1])
            
            # Apply filters
            if rsi_val < min_rsi or rsi_val > max_rsi:
                continue
            if adx_val < min_adx:
                continue
            if above_ema50 and current_price < ema50_val:
                continue
            
            # Price change
            prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
            change_pct = round((current_price - prev_close) / prev_close * 100, 2)
            
            results.append({
                "symbol": symbol,
                "price": round(current_price, 2),
                "change_pct": change_pct,
                "rsi": round(rsi_val, 1),
                "adx": round(adx_val, 1),
                "trend": "uptrend" if plus_di > minus_di else "downtrend",
                "above_ema50": current_price > ema50_val,
            })
            
            if len(results) >= limit:
                break
                
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            continue
    
    # Sort by ADX (strongest trend first)
    results.sort(key=lambda x: x["adx"], reverse=True)
    
    output = {
        "index": index.upper(),
        "criteria": {
            "rsi_range": f"{min_rsi}-{max_rsi}",
            "min_adx": min_adx,
            "above_ema50": above_ema50,
        },
        "total_screened": len(stocks),
        "passed": len(results),
        "results": results[:limit],
    }
    
    if errors:
        output["errors_count"] = len(errors)
    
    return json.dumps(output, ensure_ascii=False)
