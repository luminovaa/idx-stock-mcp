"""MCP Tools: get_technical_indicators, get_adx_trend."""

import json
import numpy as np
from ..data_sources.yfinance_client import fetch_stock_data
from ..utils.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_ema,
    calculate_bollinger_bands,
    calculate_stochastic,
    calculate_adx,
    calculate_atr,
)
from ..utils.cache import technical_cache, get_cache_key


async def get_technical_indicators(symbol: str) -> str:
    """Get comprehensive technical indicators for a stock.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA', 'TLKM')
    
    Returns:
        JSON with RSI, MACD, EMA, Bollinger Bands, Stochastic, Volume analysis
    """
    cache_key = get_cache_key("technical", symbol)
    if cache_key in technical_cache:
        return technical_cache[cache_key]
    
    df = fetch_stock_data(symbol, period="6mo")
    if df is None or df.empty or len(df) < 50:
        return json.dumps({"error": f"Insufficient data for {symbol}. Need at least 50 data points."})
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    
    # RSI
    rsi = calculate_rsi(close)
    
    # MACD
    macd = calculate_macd(close)
    
    # EMA
    ema20 = calculate_ema(close, 20)
    ema50 = calculate_ema(close, 50)
    ema200 = calculate_ema(close, 200) if len(close) >= 200 else None
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(close)
    
    # Stochastic
    stoch = calculate_stochastic(high, low, close)
    
    # Volume analysis
    vol_ma20 = volume.rolling(window=20).mean()
    
    # ATR
    atr = calculate_atr(high, low, close)
    
    # Build result
    current_price = float(close.iloc[-1])
    
    def safe_float(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return round(float(val), 2)
    
    result = {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "rsi": {
            "value": safe_float(rsi.iloc[-1]),
            "prev": safe_float(rsi.iloc[-2]),
            "signal": "oversold" if rsi.iloc[-1] < 30 else "overbought" if rsi.iloc[-1] > 70 else "neutral",
        },
        "macd": {
            "macd_line": safe_float(macd["macd_line"].iloc[-1]),
            "signal_line": safe_float(macd["signal_line"].iloc[-1]),
            "histogram": safe_float(macd["histogram"].iloc[-1]),
            "prev_histogram": safe_float(macd["histogram"].iloc[-2]),
            "signal": "bullish" if macd["macd_line"].iloc[-1] > macd["signal_line"].iloc[-1] else "bearish",
            "crossover": bool(
                macd["macd_line"].iloc[-1] > macd["signal_line"].iloc[-1] and
                macd["macd_line"].iloc[-2] <= macd["signal_line"].iloc[-2]
            ),
        },
        "ema": {
            "ema20": safe_float(ema20.iloc[-1]),
            "ema50": safe_float(ema50.iloc[-1]),
            "ema200": safe_float(ema200.iloc[-1]) if ema200 is not None else None,
            "price_vs_ema20": "above" if current_price > ema20.iloc[-1] else "below",
            "price_vs_ema50": "above" if current_price > ema50.iloc[-1] else "below",
            "golden_cross": bool(ema20.iloc[-1] > ema50.iloc[-1]),
        },
        "bollinger_bands": {
            "upper": safe_float(bb["upper"].iloc[-1]),
            "middle": safe_float(bb["middle"].iloc[-1]),
            "lower": safe_float(bb["lower"].iloc[-1]),
            "position": round((current_price - bb["lower"].iloc[-1]) / (bb["upper"].iloc[-1] - bb["lower"].iloc[-1]) * 100, 1) if bb["upper"].iloc[-1] != bb["lower"].iloc[-1] else 50,
        },
        "stochastic": {
            "k": safe_float(stoch["k"].iloc[-1]),
            "d": safe_float(stoch["d"].iloc[-1]),
            "signal": "oversold" if stoch["k"].iloc[-1] < 20 else "overbought" if stoch["k"].iloc[-1] > 80 else "neutral",
        },
        "volume": {
            "current": int(volume.iloc[-1]),
            "ma20": int(vol_ma20.iloc[-1]) if not np.isnan(vol_ma20.iloc[-1]) else 0,
            "ratio": round(float(volume.iloc[-1] / vol_ma20.iloc[-1]), 2) if vol_ma20.iloc[-1] > 0 else 0,
            "signal": "high" if volume.iloc[-1] > vol_ma20.iloc[-1] * 1.5 else "low" if volume.iloc[-1] < vol_ma20.iloc[-1] * 0.5 else "normal",
        },
        "atr": {
            "value": safe_float(atr.iloc[-1]),
            "pct": round(float(atr.iloc[-1] / current_price * 100), 2) if current_price > 0 else 0,
        },
    }
    
    response = json.dumps(result, ensure_ascii=False)
    technical_cache[cache_key] = response
    return response


async def get_adx_trend(symbol: str) -> str:
    """Get ADX trend strength analysis for a stock.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA')
    
    Returns:
        JSON with ADX value, +DI, -DI, trend direction and strength
    """
    cache_key = get_cache_key("adx", symbol)
    if cache_key in technical_cache:
        return technical_cache[cache_key]
    
    df = fetch_stock_data(symbol, period="3mo")
    if df is None or df.empty or len(df) < 30:
        return json.dumps({"error": f"Insufficient data for {symbol}. Need at least 30 data points."})
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    
    adx_data = calculate_adx(high, low, close)
    
    adx_current = float(adx_data["adx"].iloc[-1])
    plus_di = float(adx_data["plus_di"].iloc[-1])
    minus_di = float(adx_data["minus_di"].iloc[-1])
    adx_5d_ago = float(adx_data["adx"].iloc[-6]) if len(adx_data["adx"]) >= 6 else adx_current
    
    # Determine trend
    if plus_di > minus_di:
        trend_direction = "uptrend"
    elif minus_di > plus_di:
        trend_direction = "downtrend"
    else:
        trend_direction = "neutral"
    
    # ADX trend (rising/falling/flat)
    adx_change = adx_current - adx_5d_ago
    if adx_change > 2:
        adx_trend = "rising"
    elif adx_change < -2:
        adx_trend = "falling"
    else:
        adx_trend = "flat"
    
    # Strength assessment
    if adx_current >= 25:
        strength = "strong"
    elif adx_current >= 20:
        strength = "developing"
    else:
        strength = "weak/no_trend"
    
    # Price trend (20 days)
    price_20d_ago = float(close.iloc[-21]) if len(close) >= 21 else float(close.iloc[0])
    price_current = float(close.iloc[-1])
    price_change_20d = round((price_current - price_20d_ago) / price_20d_ago * 100, 2)
    
    result = {
        "symbol": symbol.upper(),
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "adx": round(adx_current, 2),
        "plus_di": round(plus_di, 2),
        "minus_di": round(minus_di, 2),
        "adx_5d_ago": round(adx_5d_ago, 2),
        "adx_trend": adx_trend,
        "trend_direction": trend_direction,
        "strength": strength,
        "price_change_20d_pct": price_change_20d,
        "passed": adx_current >= 20 and plus_di > minus_di,
        "analysis": {
            "has_trend": adx_current >= 20,
            "is_uptrend": plus_di > minus_di,
            "trend_strengthening": adx_trend == "rising" and plus_di > minus_di,
        },
    }
    
    response = json.dumps(result, ensure_ascii=False)
    technical_cache[cache_key] = response
    return response
