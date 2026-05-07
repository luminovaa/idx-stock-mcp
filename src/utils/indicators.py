"""Technical indicator calculations using ta library."""

import pandas as pd
import ta


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)."""
    return ta.momentum.RSIIndicator(close=close, window=period).rsi()


def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    macd = ta.trend.MACD(close=close, window_slow=slow, window_fast=fast, window_sign=signal)
    return {
        "macd_line": macd.macd(),
        "signal_line": macd.macd_signal(),
        "histogram": macd.macd_diff(),
    }


def calculate_ema(close: pd.Series, period: int) -> pd.Series:
    """Calculate EMA (Exponential Moving Average)."""
    return ta.trend.EMAIndicator(close=close, window=period).ema_indicator()


def calculate_bollinger_bands(close: pd.Series, period: int = 20, std: int = 2) -> dict:
    """Calculate Bollinger Bands."""
    bb = ta.volatility.BollingerBands(close=close, window=period, window_dev=std)
    return {
        "upper": bb.bollinger_hband(),
        "middle": bb.bollinger_mavg(),
        "lower": bb.bollinger_lband(),
    }


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14, smooth: int = 3) -> dict:
    """Calculate Stochastic Oscillator."""
    stoch = ta.momentum.StochasticOscillator(high=high, low=low, close=close, window=period, smooth_window=smooth)
    return {
        "k": stoch.stoch(),
        "d": stoch.stoch_signal(),
    }


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> dict:
    """Calculate ADX (Average Directional Index)."""
    adx = ta.trend.ADXIndicator(high=high, low=low, close=close, window=period)
    return {
        "adx": adx.adx(),
        "plus_di": adx.adx_pos(),
        "minus_di": adx.adx_neg(),
    }


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate ATR (Average True Range)."""
    return ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate OBV (On Balance Volume)."""
    return ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()


def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """Calculate MFI (Money Flow Index)."""
    return ta.volume.MFIIndicator(high=high, low=low, close=close, volume=volume, window=period).money_flow_index()


def calculate_support_resistance_levels(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
    """Calculate support and resistance levels using pivot points."""
    # Classic Pivot Points
    pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3
    s1 = 2 * pivot - high.iloc[-1]
    s2 = pivot - (high.iloc[-1] - low.iloc[-1])
    r1 = 2 * pivot - low.iloc[-1]
    r2 = pivot + (high.iloc[-1] - low.iloc[-1])

    # Previous lows as support
    recent_lows = low.tail(20).nsmallest(3).tolist()

    # MA support
    ema50 = calculate_ema(close, 50).iloc[-1]
    ema200 = calculate_ema(close, 200).iloc[-1]

    return {
        "pivot": round(pivot, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "recent_lows": [round(l, 2) for l in recent_lows],
        "ema50": round(ema50, 2),
        "ema200": round(ema200, 2),
    }
