"""Technical analysis indicators and signal generation."""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index.

    Args:
        series: Price series (typically Close).
        period: RSI lookback period.

    Returns:
        RSI series (0-100).
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD, Signal line, and Histogram.

    Returns:
        Tuple of (macd_line, signal_line, histogram).
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands.

    Returns:
        Tuple of (upper, middle, lower).
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def calc_moving_averages(
    series: pd.Series,
    periods: list[int] | None = None,
) -> dict[int, pd.Series]:
    """Calculate simple moving averages for given periods.

    Returns:
        Dict mapping period -> SMA series.
    """
    if periods is None:
        periods = [5, 25, 75]
    return {p: series.rolling(window=p).mean() for p in periods}


def generate_signals(df: pd.DataFrame) -> dict:
    """Generate trading signals from a single-ticker OHLCV DataFrame.

    Expects columns: Open, High, Low, Close, Volume.

    Returns:
        Dict with signal summaries per indicator and an overall signal.
    """
    close = df["Close"].squeeze()
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    signals: dict = {}
    last = close.iloc[-1]

    # RSI
    rsi = calc_rsi(close)
    rsi_val = rsi.iloc[-1]
    if rsi_val < 30:
        signals["rsi"] = {"value": round(rsi_val, 2), "signal": "BUY", "reason": "Oversold"}
    elif rsi_val > 70:
        signals["rsi"] = {"value": round(rsi_val, 2), "signal": "SELL", "reason": "Overbought"}
    else:
        signals["rsi"] = {"value": round(rsi_val, 2), "signal": "HOLD", "reason": "Neutral"}

    # MACD
    macd_line, signal_line, hist = calc_macd(close)
    macd_val = macd_line.iloc[-1]
    sig_val = signal_line.iloc[-1]
    if macd_val > sig_val and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        signals["macd"] = {"value": round(macd_val, 4), "signal": "BUY", "reason": "Bullish crossover"}
    elif macd_val < sig_val and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        signals["macd"] = {"value": round(macd_val, 4), "signal": "SELL", "reason": "Bearish crossover"}
    else:
        direction = "above" if macd_val > sig_val else "below"
        signals["macd"] = {"value": round(macd_val, 4), "signal": "HOLD", "reason": f"MACD {direction} signal"}

    # Bollinger Bands
    upper, middle, lower = calc_bollinger(close)
    if last <= lower.iloc[-1]:
        signals["bollinger"] = {"signal": "BUY", "reason": "Price at lower band"}
    elif last >= upper.iloc[-1]:
        signals["bollinger"] = {"signal": "SELL", "reason": "Price at upper band"}
    else:
        signals["bollinger"] = {"signal": "HOLD", "reason": "Price within bands"}

    # Moving averages (5 vs 25)
    mas = calc_moving_averages(close)
    if 5 in mas and 25 in mas:
        ma5 = mas[5].iloc[-1]
        ma25 = mas[25].iloc[-1]
        if ma5 > ma25:
            signals["ma_cross"] = {"signal": "BUY", "reason": f"MA5({ma5:.2f}) > MA25({ma25:.2f})"}
        else:
            signals["ma_cross"] = {"signal": "SELL", "reason": f"MA5({ma5:.2f}) < MA25({ma25:.2f})"}

    # Overall signal (majority vote)
    buy_count = sum(1 for s in signals.values() if s["signal"] == "BUY")
    sell_count = sum(1 for s in signals.values() if s["signal"] == "SELL")
    total = len(signals)
    if buy_count > sell_count and buy_count > total / 3:
        overall = "BUY"
    elif sell_count > buy_count and sell_count > total / 3:
        overall = "SELL"
    else:
        overall = "HOLD"

    signals["overall"] = {"signal": overall, "buy_count": buy_count, "sell_count": sell_count, "total": total}
    return signals
