"""Chart pattern recognition for price series."""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detect_double_bottom(prices: pd.Series, period: int = 75, tolerance: float = 0.03) -> dict:
    """Detect double bottom (W) pattern.

    Inspired by quant-trading Bollinger Bands Pattern Recognition.

    Args:
        prices: Close price series.
        period: Lookback window for pattern search.
        tolerance: Price tolerance for matching bottoms (fraction).

    Returns:
        Dict with detected (bool), signal (BUY/HOLD), confidence, details.
    """
    if len(prices) < period:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    recent = prices.iloc[-period:].values
    n = len(recent)

    # Find local minima
    minima = []
    for i in range(1, n - 1):
        if recent[i] < recent[i - 1] and recent[i] < recent[i + 1]:
            minima.append((i, recent[i]))

    if len(minima) < 2:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    # Check last two minima for double bottom
    for i in range(len(minima) - 1, 0, -1):
        idx2, val2 = minima[i]
        idx1, val1 = minima[i - 1]

        # Bottoms should be at similar levels
        if abs(val1 - val2) / max(val1, val2) < tolerance:
            # There should be a peak between them
            between = recent[idx1:idx2 + 1]
            peak = np.max(between)
            if peak > val1 * (1 + tolerance):
                # Current price should be above the neckline (peak between bottoms)
                current = recent[-1]
                if current > peak:
                    conf = min(((current - peak) / peak) * 1000, 80)
                    return {
                        "detected": True,
                        "signal": "BUY",
                        "confidence": round(conf, 1),
                        "pattern": "double_bottom",
                        "bottom1": round(float(val1), 2),
                        "bottom2": round(float(val2), 2),
                        "neckline": round(float(peak), 2),
                    }

    return {"detected": False, "signal": "HOLD", "confidence": 0}


def detect_double_top(prices: pd.Series, period: int = 75, tolerance: float = 0.03) -> dict:
    """Detect double top (M) pattern — inverse of double bottom.

    Returns:
        Dict with detected, signal (SELL/HOLD), confidence, details.
    """
    if len(prices) < period:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    recent = prices.iloc[-period:].values
    n = len(recent)

    # Find local maxima
    maxima = []
    for i in range(1, n - 1):
        if recent[i] > recent[i - 1] and recent[i] > recent[i + 1]:
            maxima.append((i, recent[i]))

    if len(maxima) < 2:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    for i in range(len(maxima) - 1, 0, -1):
        idx2, val2 = maxima[i]
        idx1, val1 = maxima[i - 1]

        if abs(val1 - val2) / max(val1, val2) < tolerance:
            between = recent[idx1:idx2 + 1]
            trough = np.min(between)
            if trough < val1 * (1 - tolerance):
                current = recent[-1]
                if current < trough:
                    conf = min(((trough - current) / trough) * 1000, 80)
                    return {
                        "detected": True,
                        "signal": "SELL",
                        "confidence": round(conf, 1),
                        "pattern": "double_top",
                        "top1": round(float(val1), 2),
                        "top2": round(float(val2), 2),
                        "neckline": round(float(trough), 2),
                    }

    return {"detected": False, "signal": "HOLD", "confidence": 0}


def detect_head_and_shoulders(prices: pd.Series, period: int = 100, tolerance: float = 0.03) -> dict:
    """Detect head and shoulders pattern.

    Looks for three peaks where the middle one (head) is highest,
    and the two shoulders are at similar levels.

    Returns:
        Dict with detected, signal (SELL/HOLD), confidence, details.
    """
    if len(prices) < period:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    recent = prices.iloc[-period:].values
    n = len(recent)

    # Find local maxima (smoothed to avoid noise)
    smoothed = pd.Series(recent).rolling(3, center=True).mean().fillna(method="bfill").fillna(method="ffill").values
    maxima = []
    for i in range(2, n - 2):
        if smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]:
            if smoothed[i] > smoothed[i - 2] and smoothed[i] > smoothed[i + 2]:
                maxima.append((i, recent[i]))

    if len(maxima) < 3:
        return {"detected": False, "signal": "HOLD", "confidence": 0}

    # Check last 3 peaks
    for i in range(len(maxima) - 1, 1, -1):
        right_idx, right_val = maxima[i]
        head_idx, head_val = maxima[i - 1]
        left_idx, left_val = maxima[i - 2]

        # Head must be highest
        if head_val > left_val and head_val > right_val:
            # Shoulders at similar levels
            if abs(left_val - right_val) / max(left_val, right_val) < tolerance:
                # Neckline: troughs between shoulders and head
                trough1 = np.min(recent[left_idx:head_idx + 1])
                trough2 = np.min(recent[head_idx:right_idx + 1])
                neckline = (trough1 + trough2) / 2

                current = recent[-1]
                if current < neckline:
                    conf = min(((neckline - current) / neckline) * 500, 85)
                    return {
                        "detected": True,
                        "signal": "SELL",
                        "confidence": round(conf, 1),
                        "pattern": "head_and_shoulders",
                        "left_shoulder": round(float(left_val), 2),
                        "head": round(float(head_val), 2),
                        "right_shoulder": round(float(right_val), 2),
                        "neckline": round(float(neckline), 2),
                    }

    return {"detected": False, "signal": "HOLD", "confidence": 0}


def detect_support_resistance(prices: pd.Series, period: int = 100, num_levels: int = 3) -> dict:
    """Detect support and resistance levels using local extrema clustering.

    Returns:
        Dict with support_levels, resistance_levels, and signal.
    """
    if len(prices) < period:
        return {"support_levels": [], "resistance_levels": [], "signal": "HOLD", "confidence": 0}

    recent = prices.iloc[-period:].values
    current = recent[-1]
    n = len(recent)

    # Collect local extrema
    local_min = []
    local_max = []
    window = 5
    for i in range(window, n - window):
        if recent[i] == np.min(recent[i - window:i + window + 1]):
            local_min.append(recent[i])
        if recent[i] == np.max(recent[i - window:i + window + 1]):
            local_max.append(recent[i])

    if not local_min and not local_max:
        return {"support_levels": [], "resistance_levels": [], "signal": "HOLD", "confidence": 0}

    # Cluster nearby levels (within 1.5% of each other)
    def cluster_levels(levels, max_levels):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for lev in levels[1:]:
            if abs(lev - clusters[-1][-1]) / max(abs(clusters[-1][-1]), 1e-10) < 0.015:
                clusters[-1].append(lev)
            else:
                clusters.append([lev])
        # Sort by cluster size (most touches = strongest)
        clusters.sort(key=len, reverse=True)
        return [round(float(np.mean(c)), 2) for c in clusters[:max_levels]]

    supports = cluster_levels([l for l in local_min if l < current], num_levels)
    resistances = cluster_levels([l for l in local_max if l > current], num_levels)

    # Signal based on proximity
    signal = "HOLD"
    confidence = 0
    if supports:
        nearest_support = max(supports)
        dist_to_support = (current - nearest_support) / current
        if dist_to_support < 0.02:
            signal = "BUY"
            confidence = min((1 - dist_to_support / 0.02) * 60, 60)
    if resistances:
        nearest_resistance = min(resistances)
        dist_to_resistance = (nearest_resistance - current) / current
        if dist_to_resistance < 0.02:
            signal = "SELL"
            confidence = min((1 - dist_to_resistance / 0.02) * 60, 60)

    return {
        "support_levels": supports,
        "resistance_levels": resistances,
        "signal": signal,
        "confidence": round(confidence, 1),
    }


def analyze_patterns(prices: pd.Series) -> dict:
    """Run all pattern detections and return combined result.

    Returns:
        Dict with individual pattern results and an aggregate signal/score.
    """
    results = {
        "double_bottom": detect_double_bottom(prices),
        "double_top": detect_double_top(prices),
        "head_and_shoulders": detect_head_and_shoulders(prices),
        "support_resistance": detect_support_resistance(prices),
    }

    # Aggregate: sum up directional signals
    score = 0.0
    reasons = []
    for name, r in results.items():
        if r.get("detected") or r.get("signal") != "HOLD":
            sig = r["signal"]
            conf = r.get("confidence", 0)
            weight = conf / 100.0
            if sig == "BUY":
                score += weight
                reasons.append(f"{name}: BUY (conf={conf})")
            elif sig == "SELL":
                score -= weight
                reasons.append(f"{name}: SELL (conf={conf})")

    if score > 0.1:
        overall = "BUY"
    elif score < -0.1:
        overall = "SELL"
    else:
        overall = "HOLD"

    results["aggregate"] = {
        "signal": overall,
        "score": round(score, 3),
        "reasons": reasons,
    }
    return results
