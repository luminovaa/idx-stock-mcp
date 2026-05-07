"""MCP Tools: calculate_support_resistance, calculate_position_size."""

import json
import numpy as np
from ..data_sources.yfinance_client import fetch_stock_data
from ..utils.indicators import calculate_support_resistance_levels, calculate_ema, calculate_atr
from ..utils.cache import technical_cache, get_cache_key


async def calculate_support_resistance(symbol: str) -> str:
    """Calculate support and resistance levels for a stock.
    
    Uses pivot points, previous lows/highs, and moving averages
    to identify key price levels.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA')
    
    Returns:
        JSON with support/resistance levels, distances, and strength assessment
    """
    cache_key = get_cache_key("support", symbol)
    if cache_key in technical_cache:
        return technical_cache[cache_key]
    
    df = fetch_stock_data(symbol, period="6mo")
    if df is None or df.empty or len(df) < 50:
        return json.dumps({"error": f"Insufficient data for {symbol}"})
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    current_price = float(close.iloc[-1])
    
    # Calculate levels
    levels = calculate_support_resistance_levels(high, low, close)
    
    # Find all support levels below current price
    support_levels = []
    
    # Pivot S1
    if levels["s1"] < current_price:
        dist = round((current_price - levels["s1"]) / current_price * 100, 2)
        support_levels.append({"level": levels["s1"], "type": "pivot_s1", "distance_pct": dist})
    
    # Pivot S2
    if levels["s2"] < current_price:
        dist = round((current_price - levels["s2"]) / current_price * 100, 2)
        support_levels.append({"level": levels["s2"], "type": "pivot_s2", "distance_pct": dist})
    
    # EMA50
    if levels["ema50"] < current_price:
        dist = round((current_price - levels["ema50"]) / current_price * 100, 2)
        support_levels.append({"level": levels["ema50"], "type": "ema50", "distance_pct": dist})
    
    # EMA200
    if levels["ema200"] < current_price and not np.isnan(levels["ema200"]):
        dist = round((current_price - levels["ema200"]) / current_price * 100, 2)
        support_levels.append({"level": levels["ema200"], "type": "ema200", "distance_pct": dist})
    
    # Recent lows
    for i, low_val in enumerate(levels["recent_lows"]):
        if low_val < current_price:
            dist = round((current_price - low_val) / current_price * 100, 2)
            support_levels.append({"level": low_val, "type": f"recent_low_{i+1}", "distance_pct": dist})
    
    # Sort by distance (nearest first)
    support_levels.sort(key=lambda x: x["distance_pct"])
    
    # Find resistance levels above current price
    resistance_levels = []
    if levels["r1"] > current_price:
        dist = round((levels["r1"] - current_price) / current_price * 100, 2)
        resistance_levels.append({"level": levels["r1"], "type": "pivot_r1", "distance_pct": dist})
    if levels["r2"] > current_price:
        dist = round((levels["r2"] - current_price) / current_price * 100, 2)
        resistance_levels.append({"level": levels["r2"], "type": "pivot_r2", "distance_pct": dist})
    
    resistance_levels.sort(key=lambda x: x["distance_pct"])
    
    # Nearest support
    nearest_support = support_levels[0] if support_levels else None
    nearest_distance = nearest_support["distance_pct"] if nearest_support else None
    
    # Support strength (how many times price bounced near this level)
    support_tests = 0
    if nearest_support:
        threshold = nearest_support["level"] * 1.02  # within 2%
        support_tests = int((low <= threshold).sum())
    
    # Pass/fail for Gate 6
    passed = nearest_distance is not None and nearest_distance <= 5.0
    
    result = {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "support_levels": support_levels[:5],  # Top 5 nearest
        "resistance_levels": resistance_levels[:3],  # Top 3 nearest
        "nearest_support": nearest_support,
        "nearest_distance_pct": nearest_distance,
        "support_tests": support_tests,
        "passed": passed,
        "assessment": {
            "distance_ok": passed,
            "support_strong": support_tests >= 2,
            "above_ema200": current_price > levels["ema200"] if not np.isnan(levels["ema200"]) else None,
            "above_ema50": current_price > levels["ema50"] if not np.isnan(levels["ema50"]) else None,
        },
    }
    
    response = json.dumps(result, ensure_ascii=False)
    technical_cache[cache_key] = response
    return response


async def calculate_position_size(symbol: str, capital: float, risk_pct: float = 2.0) -> str:
    """Calculate position size based on risk management rules.
    
    Uses the 2% risk rule: never risk more than risk_pct% of capital on a single trade.
    
    Args:
        symbol: IDX stock symbol (e.g., 'BBCA')
        capital: Total portfolio capital in IDR (e.g., 10000000 for Rp 10 juta)
        risk_pct: Maximum risk per trade as percentage (default: 2%)
    
    Returns:
        JSON with position size, stop loss, risk/reward analysis
    """
    df = fetch_stock_data(symbol, period="3mo")
    if df is None or df.empty or len(df) < 20:
        return json.dumps({"error": f"Insufficient data for {symbol}"})
    
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    current_price = float(close.iloc[-1])
    
    # ATR for stop loss calculation
    atr = calculate_atr(high, low, close)
    atr_value = float(atr.iloc[-1])
    atr_pct = atr_value / current_price * 100
    
    # Stop loss: 2x ATR below current price (or nearest support)
    stop_loss = round(current_price - (2 * atr_value), 2)
    sl_distance = current_price - stop_loss
    sl_pct = round(sl_distance / current_price * 100, 2)
    
    # Take profit: 2x the risk (R:R = 1:2)
    take_profit_1 = round(current_price + (2 * sl_distance), 2)  # 1:2 R:R
    take_profit_2 = round(current_price + (3 * sl_distance), 2)  # 1:3 R:R
    
    # Position sizing (2% rule)
    max_risk_amount = capital * (risk_pct / 100)
    risk_per_share = sl_distance
    
    if risk_per_share <= 0:
        return json.dumps({"error": "Invalid stop loss calculation"})
    
    # IDX stocks trade in lots of 100 shares
    max_shares = int(max_risk_amount / risk_per_share)
    max_lots = max_shares // 100
    
    # Actual position
    position_value = max_lots * 100 * current_price
    position_pct = round(position_value / capital * 100, 2)
    
    # Cap at 20% of portfolio
    if position_pct > 20:
        max_lots = int((capital * 0.20) / (100 * current_price))
        position_value = max_lots * 100 * current_price
        position_pct = round(position_value / capital * 100, 2)
    
    # Risk/Reward ratio
    reward_1 = take_profit_1 - current_price
    risk_reward_1 = round(reward_1 / sl_distance, 1) if sl_distance > 0 else 0
    reward_2 = take_profit_2 - current_price
    risk_reward_2 = round(reward_2 / sl_distance, 1) if sl_distance > 0 else 0
    
    # Beta (vs IHSG)
    from ..data_sources.yfinance_client import fetch_market_index
    ihsg = fetch_market_index("^JKSE", period="3mo")
    beta = None
    if ihsg is not None and not ihsg.empty and len(ihsg) >= 20:
        stock_returns = close.pct_change().dropna()
        ihsg_returns = ihsg["Close"].pct_change().dropna()
        # Align dates
        common_idx = stock_returns.index.intersection(ihsg_returns.index)
        if len(common_idx) >= 20:
            s_ret = stock_returns.loc[common_idx]
            m_ret = ihsg_returns.loc[common_idx]
            cov = np.cov(s_ret, m_ret)
            beta = round(float(cov[0][1] / cov[1][1]), 2) if cov[1][1] != 0 else 1.0
    
    # Max drawdown (6 months)
    rolling_max = close.cummax()
    drawdown = (close - rolling_max) / rolling_max * 100
    max_drawdown = round(float(drawdown.min()), 2)
    
    result = {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "capital": capital,
        "risk_pct": risk_pct,
        "position": {
            "lots": max_lots,
            "shares": max_lots * 100,
            "value": round(position_value, 2),
            "pct_of_portfolio": position_pct,
        },
        "stop_loss": {
            "price": stop_loss,
            "distance_pct": sl_pct,
            "max_loss": round(max_lots * 100 * sl_distance, 2),
        },
        "take_profit": {
            "tp1": take_profit_1,
            "tp1_pct": round((take_profit_1 - current_price) / current_price * 100, 2),
            "tp2": take_profit_2,
            "tp2_pct": round((take_profit_2 - current_price) / current_price * 100, 2),
        },
        "risk_reward": {
            "rr_tp1": f"1:{risk_reward_1}",
            "rr_tp2": f"1:{risk_reward_2}",
        },
        "risk_metrics": {
            "atr": round(atr_value, 2),
            "atr_pct": round(atr_pct, 2),
            "beta": beta,
            "max_drawdown_6mo": max_drawdown,
        },
        "rules_check": {
            "risk_under_2pct": position_value * sl_pct / 100 <= capital * risk_pct / 100,
            "position_under_20pct": position_pct <= 20,
            "rr_above_1_5": risk_reward_1 >= 1.5,
        },
    }
    
    response = json.dumps(result, ensure_ascii=False)
    return response
