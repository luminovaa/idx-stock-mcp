"""MCP Tool: get_macro_data - Fetch macro economic and global market data."""

import json
import numpy as np
from ..data_sources.yfinance_client import fetch_market_index
from ..data_sources.alphavantage_client import fetch_forex_rate
from ..utils.cache import macro_cache, get_cache_key


async def get_macro_data() -> str:
    """Get macro economic and global market data relevant to IDX.
    
    Returns:
        JSON with IHSG, S&P500, Hang Seng, USD/IDR, and trend analysis
    """
    cache_key = get_cache_key("macro", "global")
    if cache_key in macro_cache:
        return macro_cache[cache_key]
    
    # Fetch market indices
    ihsg = fetch_market_index("^JKSE", period="3mo")
    sp500 = fetch_market_index("^GSPC", period="3mo")
    hsi = fetch_market_index("^HSI", period="3mo")
    usdidr = fetch_market_index("USDIDR=X", period="3mo")
    
    def analyze_index(df, name: str) -> dict:
        if df is None or df.empty:
            return {"name": name, "error": "Data not available"}
        
        close = df["Close"]
        current = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else current
        change_1d = round((current - prev) / prev * 100, 2)
        
        # 5-day change
        price_5d = float(close.iloc[-6]) if len(close) >= 6 else float(close.iloc[0])
        change_5d = round((current - price_5d) / price_5d * 100, 2)
        
        # 20-day change
        price_20d = float(close.iloc[-21]) if len(close) >= 21 else float(close.iloc[0])
        change_20d = round((current - price_20d) / price_20d * 100, 2)
        
        # Trend determination
        if change_20d > 3:
            trend = "uptrend"
        elif change_20d < -3:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        # SMA20
        sma20 = float(close.tail(20).mean())
        above_sma20 = current > sma20
        
        return {
            "name": name,
            "current": round(current, 2),
            "change_1d_pct": change_1d,
            "change_5d_pct": change_5d,
            "change_20d_pct": change_20d,
            "trend": trend,
            "above_sma20": above_sma20,
            "date": df.index[-1].strftime("%Y-%m-%d"),
        }
    
    # USD/IDR analysis
    usdidr_analysis = {}
    if usdidr is not None and not usdidr.empty:
        usd_close = usdidr["Close"]
        usd_current = float(usd_close.iloc[-1])
        usd_prev = float(usd_close.iloc[-2]) if len(usd_close) > 1 else usd_current
        usd_20d = float(usd_close.iloc[-21]) if len(usd_close) >= 21 else float(usd_close.iloc[0])
        
        usdidr_analysis = {
            "rate": round(usd_current, 2),
            "change_1d_pct": round((usd_current - usd_prev) / usd_prev * 100, 2),
            "change_20d_pct": round((usd_current - usd_20d) / usd_20d * 100, 2),
            "idr_direction": "weakening" if usd_current > usd_20d else "strengthening",
            "impact_on_idx": "negative" if usd_current > usd_20d * 1.02 else "positive" if usd_current < usd_20d * 0.98 else "neutral",
        }
    
    # Overall market sentiment
    ihsg_data = analyze_index(ihsg, "IHSG (^JKSE)")
    sp500_data = analyze_index(sp500, "S&P 500 (^GSPC)")
    hsi_data = analyze_index(hsi, "Hang Seng (^HSI)")
    
    # Determine global sentiment
    bullish_count = sum(1 for d in [ihsg_data, sp500_data, hsi_data] if d.get("trend") == "uptrend")
    bearish_count = sum(1 for d in [ihsg_data, sp500_data, hsi_data] if d.get("trend") == "downtrend")
    
    if bullish_count >= 2:
        global_sentiment = "risk_on"
    elif bearish_count >= 2:
        global_sentiment = "risk_off"
    else:
        global_sentiment = "mixed"
    
    result = {
        "timestamp": ihsg.index[-1].strftime("%Y-%m-%d") if ihsg is not None and not ihsg.empty else "unknown",
        "indices": {
            "ihsg": ihsg_data,
            "sp500": sp500_data,
            "hang_seng": hsi_data,
        },
        "forex": {
            "usd_idr": usdidr_analysis,
        },
        "global_sentiment": global_sentiment,
        "summary": {
            "bullish_indices": bullish_count,
            "bearish_indices": bearish_count,
            "idr_status": usdidr_analysis.get("idr_direction", "unknown"),
        },
        "note": "Global sentiment 'risk_on' = supportive for IDX. 'risk_off' = headwind. IDR weakening = negative for most stocks except exporters.",
    }
    
    response = json.dumps(result, ensure_ascii=False)
    macro_cache[cache_key] = response
    return response
