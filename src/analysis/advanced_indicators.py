"""Advanced technical indicators.

Ported/inspired from quant-trading repository:
- Awesome Oscillator backtest.py
- Parabolic SAR backtest.py
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calc_awesome_oscillator(high: pd.Series, low: pd.Series, fast: int = 5, slow: int = 34) -> pd.Series:
    """Calculate Awesome Oscillator (AO).

    AO = SMA(median_price, fast) - SMA(median_price, slow)
    where median_price = (High + Low) / 2

    Based on quant-trading Awesome Oscillator implementation.
    """
    median_price = (high + low) / 2
    ao = median_price.rolling(window=fast).mean() - median_price.rolling(window=slow).mean()
    return ao


def calc_parabolic_sar(high: pd.Series, low: pd.Series, close: pd.Series,
                       initial_af: float = 0.02, step_af: float = 0.02,
                       end_af: float = 0.2) -> pd.Series:
    """Calculate Parabolic SAR.

    Ported from quant-trading Parabolic SAR backtest.py.
    """
    n = len(close)
    if n < 3:
        return pd.Series(np.nan, index=close.index)

    sar = np.zeros(n)
    trend = np.zeros(n)
    ep = np.zeros(n)
    af = np.zeros(n)
    real_sar = np.full(n, np.nan)

    h = high.values
    l = low.values
    c = close.values

    # Initialize
    trend[1] = 1.0 if c[1] > c[0] else -1.0
    sar[1] = h[0] if trend[1] > 0 else l[0]
    real_sar[1] = sar[1]
    ep[1] = h[1] if trend[1] > 0 else l[1]
    af[1] = initial_af

    for i in range(2, n):
        temp = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])

        if trend[i - 1] < 0:
            sar[i] = max(temp, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            trend[i] = 1 if sar[i] < h[i] else trend[i - 1] - 1
        else:
            sar[i] = min(temp, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            trend[i] = -1 if sar[i] > l[i] else trend[i - 1] + 1

        if trend[i] < 0:
            ep[i] = min(l[i], ep[i - 1]) if trend[i] != -1 else l[i]
        else:
            ep[i] = max(h[i], ep[i - 1]) if trend[i] != 1 else h[i]

        if abs(trend[i]) == 1:
            real_sar[i] = ep[i - 1]
            af[i] = initial_af
        else:
            real_sar[i] = sar[i]
            if ep[i] == ep[i - 1]:
                af[i] = af[i - 1]
            else:
                af[i] = min(end_af, af[i - 1] + step_af)

    return pd.Series(real_sar, index=close.index, name="parabolic_sar")


def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                    k_period: int = 14, d_period: int = 3) -> tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator (%K and %D).

    %K = (Close - Low_n) / (High_n - Low_n) * 100
    %D = SMA(%K, d_period)

    Returns:
        Tuple of (%K, %D) series.
    """
    low_n = low.rolling(window=k_period).min()
    high_n = high.rolling(window=k_period).max()
    denom = high_n - low_n
    denom = denom.replace(0, np.nan)
    k = ((close - low_n) / denom) * 100
    d = k.rolling(window=d_period).mean()
    return k, d


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR).

    TR = max(H-L, |H-Cprev|, |L-Cprev|)
    ATR = EMA(TR, period)
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    return atr


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On Balance Volume (OBV).

    OBV adds volume on up days and subtracts on down days.
    """
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    obv = (volume * direction).cumsum()
    return obv


def generate_advanced_signals(df: pd.DataFrame) -> dict:
    """Generate signals from advanced indicators.

    Expects columns: High, Low, Close, Volume.

    Returns:
        Dict with individual indicator signals and aggregate.
    """
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    close = df["Close"].squeeze()
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    signals = {}
    score = 0.0
    reasons = []

    # Awesome Oscillator
    ao = calc_awesome_oscillator(high, low)
    ao_val = ao.iloc[-1]
    if not np.isnan(ao_val):
        if ao_val > 0 and ao.iloc[-2] <= 0:
            signals["ao"] = {"value": round(float(ao_val), 4), "signal": "BUY", "reason": "AO crossed above zero"}
            score += 1.5
            reasons.append("AO bullish crossover")
        elif ao_val < 0 and ao.iloc[-2] >= 0:
            signals["ao"] = {"value": round(float(ao_val), 4), "signal": "SELL", "reason": "AO crossed below zero"}
            score -= 1.5
            reasons.append("AO bearish crossover")
        elif ao_val > 0:
            signals["ao"] = {"value": round(float(ao_val), 4), "signal": "BUY", "reason": "AO positive"}
            score += 0.5
            reasons.append("AO positive")
        else:
            signals["ao"] = {"value": round(float(ao_val), 4), "signal": "SELL", "reason": "AO negative"}
            score -= 0.5
            reasons.append("AO negative")

    # Parabolic SAR
    psar = calc_parabolic_sar(high, low, close)
    psar_val = psar.iloc[-1]
    last_price = close.iloc[-1]
    if not np.isnan(psar_val):
        if last_price > psar_val:
            signals["psar"] = {"value": round(float(psar_val), 2), "signal": "BUY", "reason": "Price above SAR (uptrend)"}
            score += 1
            reasons.append("PSAR uptrend")
        else:
            signals["psar"] = {"value": round(float(psar_val), 2), "signal": "SELL", "reason": "Price below SAR (downtrend)"}
            score -= 1
            reasons.append("PSAR downtrend")

    # Stochastic
    k, d = calc_stochastic(high, low, close)
    k_val = k.iloc[-1]
    d_val = d.iloc[-1]
    if not np.isnan(k_val):
        if k_val < 20 and d_val < 20:
            signals["stochastic"] = {"k": round(float(k_val), 1), "d": round(float(d_val), 1), "signal": "BUY", "reason": "Oversold"}
            score += 1.5
            reasons.append(f"Stochastic oversold (K={k_val:.1f})")
        elif k_val > 80 and d_val > 80:
            signals["stochastic"] = {"k": round(float(k_val), 1), "d": round(float(d_val), 1), "signal": "SELL", "reason": "Overbought"}
            score -= 1.5
            reasons.append(f"Stochastic overbought (K={k_val:.1f})")
        elif k_val > d_val:
            signals["stochastic"] = {"k": round(float(k_val), 1), "d": round(float(d_val), 1), "signal": "BUY", "reason": "K above D"}
            score += 0.5
            reasons.append("Stochastic K>D")
        else:
            signals["stochastic"] = {"k": round(float(k_val), 1), "d": round(float(d_val), 1), "signal": "SELL", "reason": "K below D"}
            score -= 0.5
            reasons.append("Stochastic K<D")

    # ATR (volatility, no directional signal but affects confidence)
    atr = calc_atr(high, low, close)
    atr_val = atr.iloc[-1]
    if not np.isnan(atr_val):
        atr_pct = atr_val / last_price * 100
        signals["atr"] = {"value": round(float(atr_val), 4), "pct": round(float(atr_pct), 2), "signal": "INFO"}

    # OBV
    if "Volume" in df.columns:
        volume = df["Volume"].squeeze()
        if isinstance(volume, pd.DataFrame):
            volume = volume.iloc[:, 0]
        obv = calc_obv(close, volume)
        obv_trend = obv.iloc[-1] - obv.iloc[-5] if len(obv) >= 5 else 0
        price_trend = close.iloc[-1] - close.iloc[-5] if len(close) >= 5 else 0
        if obv_trend > 0 and price_trend > 0:
            signals["obv"] = {"signal": "BUY", "reason": "OBV confirms uptrend"}
            score += 1
            reasons.append("OBV confirms uptrend")
        elif obv_trend < 0 and price_trend < 0:
            signals["obv"] = {"signal": "SELL", "reason": "OBV confirms downtrend"}
            score -= 1
            reasons.append("OBV confirms downtrend")
        elif obv_trend > 0 and price_trend <= 0:
            signals["obv"] = {"signal": "BUY", "reason": "OBV divergence (bullish)"}
            score += 1.5
            reasons.append("OBV bullish divergence")
        elif obv_trend < 0 and price_trend >= 0:
            signals["obv"] = {"signal": "SELL", "reason": "OBV divergence (bearish)"}
            score -= 1.5
            reasons.append("OBV bearish divergence")

    signals["aggregate"] = {"score": round(score, 2), "reasons": reasons}
    return signals
