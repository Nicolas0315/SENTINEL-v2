"""Enhanced prediction engine with pattern recognition and advanced indicators.

Integrates:
- Traditional technical indicators (RSI, MACD, Bollinger, MA) — weight: 40%
- Chart pattern recognition (double bottom/top, H&S, S/R) — weight: 30%
- Advanced momentum indicators (AO, PSAR, Stochastic, ATR, OBV) — weight: 30%
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from src.analysis.technical import (
    calc_bollinger,
    calc_macd,
    calc_moving_averages,
    calc_rsi,
    generate_signals,
)
from src.analysis.patterns import analyze_patterns
from src.analysis.advanced_indicators import (
    calc_awesome_oscillator,
    calc_parabolic_sar,
    calc_stochastic,
    calc_atr,
    calc_obv,
    generate_advanced_signals,
)

logger = logging.getLogger(__name__)

# Signal weights
WEIGHT_TECHNICAL = 0.40
WEIGHT_PATTERN = 0.30
WEIGHT_MOMENTUM = 0.30


def _calc_technical_score(close: pd.Series, data: pd.DataFrame) -> tuple[float, list[str]]:
    """Calculate technical indicator score (RSI, MACD, Bollinger, MA).

    Returns:
        Tuple of (normalized_score [-1, 1], reasons).
    """
    score = 0.0
    max_score = 7.0
    reasons = []

    rsi = calc_rsi(close)
    rsi_val = rsi.iloc[-1]
    if rsi_val < 30:
        score += 2
        reasons.append(f"RSI oversold ({rsi_val:.1f})")
    elif rsi_val < 40:
        score += 1
        reasons.append(f"RSI low ({rsi_val:.1f})")
    elif rsi_val > 70:
        score -= 2
        reasons.append(f"RSI overbought ({rsi_val:.1f})")
    elif rsi_val > 60:
        score -= 1
        reasons.append(f"RSI high ({rsi_val:.1f})")
    else:
        reasons.append(f"RSI neutral ({rsi_val:.1f})")

    macd_line, signal_line, hist = calc_macd(close)
    macd_val = macd_line.iloc[-1]
    sig_val = signal_line.iloc[-1]
    if macd_val > sig_val:
        score += 1
        if hist.iloc[-1] > hist.iloc[-2]:
            score += 1
            reasons.append("MACD bullish & strengthening")
        else:
            reasons.append("MACD bullish")
    else:
        score -= 1
        if hist.iloc[-1] < hist.iloc[-2]:
            score -= 1
            reasons.append("MACD bearish & weakening")
        else:
            reasons.append("MACD bearish")

    upper, middle, lower = calc_bollinger(close)
    last_price = close.iloc[-1]
    bb_range = upper.iloc[-1] - lower.iloc[-1]
    bb_pos = (last_price - lower.iloc[-1]) / bb_range if bb_range > 0 else 0.5
    if bb_pos < 0.2:
        score += 1.5
        reasons.append(f"Near lower Bollinger ({bb_pos:.2f})")
    elif bb_pos > 0.8:
        score -= 1.5
        reasons.append(f"Near upper Bollinger ({bb_pos:.2f})")

    mas = calc_moving_averages(close)
    if 5 in mas and 25 in mas:
        ma5 = mas[5].iloc[-1]
        ma25 = mas[25].iloc[-1]
        if ma5 > ma25:
            score += 1
            reasons.append("MA5 > MA25 (bullish)")
        else:
            score -= 1
            reasons.append("MA5 < MA25 (bearish)")

    # 5-day momentum with mean reversion bias
    if len(close) >= 6:
        mom5 = (close.iloc[-1] / close.iloc[-6] - 1) * 100
        if mom5 > 3:
            score -= 0.5
            reasons.append(f"5d momentum +{mom5:.1f}% (pullback risk)")
        elif mom5 < -3:
            score += 0.5
            reasons.append(f"5d momentum {mom5:.1f}% (bounce potential)")

    normalized = max(min(score / max_score, 1.0), -1.0)
    return normalized, reasons


def _calc_pattern_score(close: pd.Series) -> tuple[float, list[str]]:
    """Calculate pattern recognition score.

    Returns:
        Tuple of (normalized_score [-1, 1], reasons).
    """
    results = analyze_patterns(close)
    agg = results.get("aggregate", {})
    raw_score = agg.get("score", 0)
    reasons = agg.get("reasons", [])

    # Normalize: pattern scores typically range -1 to 1
    normalized = max(min(raw_score, 1.0), -1.0)
    return normalized, reasons


def _calc_momentum_score(data: pd.DataFrame) -> tuple[float, list[str]]:
    """Calculate advanced momentum indicator score.

    Returns:
        Tuple of (normalized_score [-1, 1], reasons).
    """
    adv = generate_advanced_signals(data)
    agg = adv.get("aggregate", {})
    raw_score = agg.get("score", 0)
    reasons = agg.get("reasons", [])

    # Max possible ~6.5, normalize
    max_score = 6.5
    normalized = max(min(raw_score / max_score, 1.0), -1.0)
    return normalized, reasons


def blind_predict(ticker: str, as_of_date: Optional[str] = None) -> dict:
    """Predict next-week direction using technical, pattern, and momentum signals.

    Weights: Technical 40%, Pattern 30%, Momentum 30%.

    Args:
        ticker: Yahoo Finance ticker symbol.
        as_of_date: Cutoff date string 'YYYY-MM-DD'. Uses today if None.

    Returns:
        Dict with ticker, as_of_date, direction (UP/DOWN/FLAT),
        confidence (0-100), component scores, and reasoning.
    """
    if as_of_date is None:
        as_of_date = datetime.now().strftime("%Y-%m-%d")

    cutoff = pd.Timestamp(as_of_date)
    start = (cutoff - timedelta(days=250)).strftime("%Y-%m-%d")
    end = (cutoff + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": "No data"}

        data = data[data.index <= cutoff]
        if len(data) < 30:
            return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": "Insufficient data"}

        close = data["Close"].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Component scores (each normalized to [-1, 1])
        tech_score, tech_reasons = _calc_technical_score(close, data)
        pattern_score, pattern_reasons = _calc_pattern_score(close)
        momentum_score, momentum_reasons = _calc_momentum_score(data)

        # Weighted composite
        composite = (
            WEIGHT_TECHNICAL * tech_score
            + WEIGHT_PATTERN * pattern_score
            + WEIGHT_MOMENTUM * momentum_score
        )

        # Confidence: based on agreement between components
        scores = [tech_score, pattern_score, momentum_score]
        signs = [1 if s > 0 else (-1 if s < 0 else 0) for s in scores]
        agreement = abs(sum(signs)) / 3.0  # 0 to 1

        base_confidence = abs(composite) * 100
        # Boost confidence when components agree, reduce when they disagree
        confidence = base_confidence * (0.5 + 0.5 * agreement)
        confidence = min(confidence, 95)

        if composite > 0.05:
            direction = "UP"
        elif composite < -0.05:
            direction = "DOWN"
        else:
            direction = "FLAT"

        all_reasons = tech_reasons + pattern_reasons + momentum_reasons

        return {
            "ticker": ticker,
            "as_of_date": as_of_date,
            "direction": direction,
            "confidence": round(confidence, 1),
            "composite_score": round(composite, 4),
            "components": {
                "technical": {"score": round(tech_score, 4), "weight": WEIGHT_TECHNICAL},
                "pattern": {"score": round(pattern_score, 4), "weight": WEIGHT_PATTERN},
                "momentum": {"score": round(momentum_score, 4), "weight": WEIGHT_MOMENTUM},
            },
            "indicators": {
                "price": round(float(close.iloc[-1]), 2),
            },
            "reasoning": all_reasons,
        }
    except Exception as e:
        logger.error(f"blind_predict failed for {ticker}: {e}")
        return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": str(e)}


def evaluate_prediction(ticker: str, prediction_date: str, actual_date: str) -> dict:
    """Compare prediction with actual outcome."""
    pred = blind_predict(ticker, as_of_date=prediction_date)

    start = prediction_date
    end = (pd.Timestamp(actual_date) + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty or len(data) < 2:
            return {"error": "Insufficient actual data", "prediction": pred}

        close = data["Close"].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        start_price = close.iloc[0]
        end_price = close.iloc[-1]
        actual_return = (end_price / start_price - 1) * 100

        if actual_return > 0.5:
            actual_dir = "UP"
        elif actual_return < -0.5:
            actual_dir = "DOWN"
        else:
            actual_dir = "FLAT"

        hit = pred["direction"] == actual_dir
        return {
            "ticker": ticker,
            "prediction_date": prediction_date,
            "actual_date": actual_date,
            "predicted": pred["direction"],
            "actual": actual_dir,
            "actual_return_pct": round(actual_return, 2),
            "hit": hit,
            "confidence": pred.get("confidence", 0),
            "composite_score": pred.get("composite_score", 0),
        }
    except Exception as e:
        logger.error(f"evaluate_prediction failed: {e}")
        return {"error": str(e), "prediction": pred}


def backtest(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Run blind predictions weekly and calculate accuracy."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    results = []

    current = start
    while current + timedelta(days=7) <= end:
        pred_date = current.strftime("%Y-%m-%d")
        actual_date = (current + timedelta(days=7)).strftime("%Y-%m-%d")

        result = evaluate_prediction(ticker, pred_date, actual_date)
        if "error" not in result:
            results.append({
                "date": pred_date,
                "predicted": result["predicted"],
                "actual": result["actual"],
                "actual_return_pct": result["actual_return_pct"],
                "hit": result["hit"],
                "confidence": result["confidence"],
                "composite_score": result.get("composite_score", 0),
            })
        current += timedelta(days=7)

    df = pd.DataFrame(results)
    if not df.empty:
        accuracy = df["hit"].mean() * 100
        logger.info(f"Backtest {ticker}: {len(df)} predictions, accuracy={accuracy:.1f}%")
    return df
