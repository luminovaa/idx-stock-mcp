"""MCP Tools: get_money_flow, get_broker_summary."""

import json
import numpy as np
from ..data_sources.yfinance_client import fetch_stock_data
from ..data_sources.idx_client import fetch_broker_summary, fetch_foreign_flow
from ..data_sources.ajaib_client import fetch_net_buy_sell
from ..utils.indicators import calculate_obv, calculate_mfi
from ..utils.cache import money_flow_cache, get_cache_key


async def get_money_flow(symbol: str) -> str:
    """Get money flow analysis (OBV, MFI, foreign flow, volume analysis).
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA')
    
    Returns:
        JSON with OBV, MFI, volume ratio, foreign flow data
    """
    cache_key = get_cache_key("money_flow", symbol)
    if cache_key in money_flow_cache:
        return money_flow_cache[cache_key]
    
    df = fetch_stock_data(symbol, period="3mo")
    if df is None or df.empty or len(df) < 20:
        return json.dumps({"error": f"Insufficient data for {symbol}"})
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    
    # OBV
    obv = calculate_obv(close, volume)
    obv_current = float(obv.iloc[-1])
    obv_20d_ago = float(obv.iloc[-21]) if len(obv) >= 21 else float(obv.iloc[0])
    obv_trend = "rising" if obv_current > obv_20d_ago else "falling"
    
    # MFI
    mfi = calculate_mfi(high, low, close, volume)
    mfi_current = float(mfi.iloc[-1]) if not np.isnan(mfi.iloc[-1]) else 50
    
    # Volume analysis
    vol_ma20 = volume.rolling(window=20).mean()
    vol_ratio = float(volume.iloc[-1] / vol_ma20.iloc[-1]) if vol_ma20.iloc[-1] > 0 else 1.0
    
    # Volume trend (5 days)
    vol_5d_avg = float(volume.tail(5).mean())
    vol_20d_avg = float(vol_ma20.iloc[-1]) if not np.isnan(vol_ma20.iloc[-1]) else vol_5d_avg
    
    # Foreign flow (from IDX)
    foreign_data = await fetch_foreign_flow(symbol, days=20)
    foreign_net_5d = None
    foreign_net_20d = None
    
    if foreign_data and isinstance(foreign_data, list):
        # Sum up foreign net values
        recent_5 = foreign_data[-5:] if len(foreign_data) >= 5 else foreign_data
        foreign_net_5d = sum(item.get("foreignNet", 0) for item in recent_5)
        foreign_net_20d = sum(item.get("foreignNet", 0) for item in foreign_data)
    
    # Ajaib net buy/sell
    ajaib_data = await fetch_net_buy_sell(symbol, days=5)
    
    # Price vs OBV divergence check
    price_change_20d = (float(close.iloc[-1]) - float(close.iloc[-21])) / float(close.iloc[-21]) * 100 if len(close) >= 21 else 0
    obv_change_20d = ((obv_current - obv_20d_ago) / abs(obv_20d_ago) * 100) if obv_20d_ago != 0 else 0
    
    # Detect divergence
    divergence = "none"
    if price_change_20d < -2 and obv_change_20d > 5:
        divergence = "bullish_divergence"  # Price down but OBV up = accumulation
    elif price_change_20d > 2 and obv_change_20d < -5:
        divergence = "bearish_divergence"  # Price up but OBV down = distribution
    
    # Smart money score (0-5 scale)
    smart_money_score = 2.5  # neutral baseline
    if obv_trend == "rising":
        smart_money_score += 0.5
    if mfi_current > 50:
        smart_money_score += 0.5
    if vol_ratio > 1.2:
        smart_money_score += 0.3
    if foreign_net_5d and foreign_net_5d > 0:
        smart_money_score += 0.5
    if divergence == "bullish_divergence":
        smart_money_score += 0.7
    elif divergence == "bearish_divergence":
        smart_money_score -= 0.7
    if foreign_net_5d and foreign_net_5d < 0:
        smart_money_score -= 0.5
    if obv_trend == "falling":
        smart_money_score -= 0.5
    
    smart_money_score = max(0, min(5, smart_money_score))
    
    result = {
        "symbol": symbol.upper(),
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "obv": {
            "current": round(obv_current, 0),
            "20d_ago": round(obv_20d_ago, 0),
            "trend": obv_trend,
            "change_pct": round(obv_change_20d, 2),
        },
        "mfi": {
            "value": round(mfi_current, 2),
            "signal": "overbought" if mfi_current > 80 else "oversold" if mfi_current < 20 else "neutral",
            "money_flowing_in": mfi_current > 50,
        },
        "volume": {
            "current": int(volume.iloc[-1]),
            "ma20": int(vol_20d_avg),
            "ratio": round(vol_ratio, 2),
            "5d_avg": int(vol_5d_avg),
            "signal": "high" if vol_ratio > 1.5 else "low" if vol_ratio < 0.5 else "normal",
        },
        "foreign_flow": {
            "net_5d": foreign_net_5d,
            "net_20d": foreign_net_20d,
            "direction": "inflow" if (foreign_net_5d and foreign_net_5d > 0) else "outflow" if (foreign_net_5d and foreign_net_5d < 0) else "unknown",
        },
        "divergence": divergence,
        "smart_money_score": round(smart_money_score, 1),
        "smart_money_signal": "accumulation" if smart_money_score >= 3.5 else "distribution" if smart_money_score <= 1.5 else "neutral",
    }
    
    if ajaib_data:
        result["ajaib_flow"] = ajaib_data
    
    response = json.dumps(result, ensure_ascii=False)
    money_flow_cache[cache_key] = response
    return response


async def get_broker_summary(symbol: str, date: str = None) -> str:
    """Get broker summary (top buyers and sellers) for a stock.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA')
        date: Trading date in YYYY-MM-DD format (default: latest)
    
    Returns:
        JSON with top buyer/seller brokers and net values
    """
    cache_key = get_cache_key("broker", symbol, date or "latest")
    if cache_key in money_flow_cache:
        return money_flow_cache[cache_key]
    
    data = await fetch_broker_summary(symbol, trade_date=date)
    
    if data is None:
        return json.dumps({
            "symbol": symbol.upper(),
            "date": date or "latest",
            "error": "Broker summary data not available. IDX API may be unreachable.",
            "note": "Try using get_money_flow for alternative flow analysis via OBV/MFI.",
        })
    
    result = {
        "symbol": symbol.upper(),
        "date": date or "latest",
        "data": data,
    }
    
    response = json.dumps(result, ensure_ascii=False)
    money_flow_cache[cache_key] = response
    return response
