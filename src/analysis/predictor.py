"""Prediction engine with blind prediction and backtesting."""

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

logger = logging.getLogger(__name__)


def blind_predict(ticker: str, as_of_date: Optional[str] = None) -> dict:
    """Predict next-week direction using only data up to as_of_date.

    Args:
        ticker: Yahoo Finance ticker symbol.
        as_of_date: Cutoff date string 'YYYY-MM-DD'. Uses today if None.

    Returns:
        Dict with keys: ticker, as_of_date, direction (UP/DOWN/FLAT),
        confidence (0-100), indicators, reasoning.
    """
    if as_of_date is None:
        as_of_date = datetime.now().strftime("%Y-%m-%d")

    cutoff = pd.Timestamp(as_of_date)
    # Fetch enough history for indicators (need ~100 days for MA75 + buffer)
    start = (cutoff - timedelta(days=200)).strftime("%Y-%m-%d")
    end = (cutoff + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": "No data"}

        # Ensure we only use data up to cutoff
        data = data[data.index <= cutoff]
        if len(data) < 30:
            return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": "Insufficient data"}

        close = data["Close"].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Calculate indicators
        rsi = calc_rsi(close)
        macd_line, signal_line, hist = calc_macd(close)
        upper, middle, lower = calc_bollinger(close)
        mas = calc_moving_averages(close)

        rsi_val = rsi.iloc[-1]
        macd_val = macd_line.iloc[-1]
        sig_val = signal_line.iloc[-1]
        hist_val = hist.iloc[-1]
        last_price = close.iloc[-1]

        # Scoring system: each indicator contributes a score
        score = 0.0
        reasons = []

        # RSI signal
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

        # MACD signal
        if macd_val > sig_val:
            score += 1
            if hist_val > hist.iloc[-2]:
                score += 1
                reasons.append("MACD bullish & strengthening")
            else:
                reasons.append("MACD bullish")
        else:
            score -= 1
            if hist_val < hist.iloc[-2]:
                score -= 1
                reasons.append("MACD bearish & weakening")
            else:
                reasons.append("MACD bearish")

        # Bollinger position
        bb_pos = (last_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) if (upper.iloc[-1] - lower.iloc[-1]) > 0 else 0.5
        if bb_pos < 0.2:
            score += 1.5
            reasons.append(f"Near lower Bollinger band ({bb_pos:.2f})")
        elif bb_pos > 0.8:
            score -= 1.5
            reasons.append(f"Near upper Bollinger band ({bb_pos:.2f})")

        # MA trend
        if 5 in mas and 25 in mas:
            ma5 = mas[5].iloc[-1]
            ma25 = mas[25].iloc[-1]
            if ma5 > ma25:
                score += 1
                reasons.append("Short MA above medium MA (bullish)")
            else:
                score -= 1
                reasons.append("Short MA below medium MA (bearish)")

        # Price momentum (5-day return)
        if len(close) >= 6:
            mom5 = (close.iloc[-1] / close.iloc[-6] - 1) * 100
            if mom5 > 3:
                score -= 0.5  # Mean reversion bias
                reasons.append(f"5d momentum +{mom5:.1f}% (possible pullback)")
            elif mom5 < -3:
                score += 0.5
                reasons.append(f"5d momentum {mom5:.1f}% (possible bounce)")

        # Convert score to direction and confidence
        max_score = 7.0
        normalized = score / max_score  # -1 to 1
        confidence = min(abs(normalized) * 100, 95)

        if normalized > 0.1:
            direction = "UP"
        elif normalized < -0.1:
            direction = "DOWN"
        else:
            direction = "FLAT"

        return {
            "ticker": ticker,
            "as_of_date": as_of_date,
            "direction": direction,
            "confidence": round(confidence, 1),
            "score": round(score, 2),
            "indicators": {
                "rsi": round(float(rsi_val), 2),
                "macd": round(float(macd_val), 4),
                "macd_signal": round(float(sig_val), 4),
                "bb_position": round(float(bb_pos), 3),
                "price": round(float(last_price), 2),
            },
            "reasoning": reasons,
        }
    except Exception as e:
        logger.error(f"blind_predict failed for {ticker}: {e}")
        return {"ticker": ticker, "as_of_date": as_of_date, "direction": "FLAT", "confidence": 0, "error": str(e)}


def evaluate_prediction(ticker: str, prediction_date: str, actual_date: str) -> dict:
    """Compare prediction with actual outcome.

    Args:
        ticker: Ticker symbol.
        prediction_date: Date prediction was made ('YYYY-MM-DD').
        actual_date: Date to check actual result ('YYYY-MM-DD').

    Returns:
        Dict with prediction, actual direction, and hit/miss.
    """
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
        }
    except Exception as e:
        logger.error(f"evaluate_prediction failed: {e}")
        return {"error": str(e), "prediction": pred}


def backtest(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Run blind predictions over a date range and calculate accuracy.

    Predictions are made weekly (every Monday) looking one week ahead.

    Returns:
        DataFrame with columns: date, predicted, actual, hit, confidence.
    """
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
            })
        current += timedelta(days=7)

    df = pd.DataFrame(results)
    if not df.empty:
        accuracy = df["hit"].mean() * 100
        logger.info(f"Backtest {ticker}: {len(df)} predictions, accuracy={accuracy:.1f}%")
    return df
