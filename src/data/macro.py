"""Macro economic data fetcher using public APIs (no keys required)."""

import logging
from typing import Optional

import requests
import yfinance as yf

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (SENTINEL-v2)"}
_TIMEOUT = 15


def fetch_fear_greed_index() -> Optional[dict]:
    """Fetch CNN Fear & Greed Index via unofficial API.

    Returns:
        Dict with 'score' (0-100) and 'rating' (e.g. 'Greed'), or None.
    """
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        fg = data.get("fear_and_greed", {})
        return {
            "score": round(fg.get("score", 0), 1),
            "rating": fg.get("rating", "Unknown"),
        }
    except Exception as e:
        logger.error(f"Fear & Greed fetch failed: {e}")
        return None


def _yf_last_price(symbol: str) -> Optional[float]:
    """Helper: get last price from Yahoo Finance."""
    try:
        t = yf.Ticker(symbol)
        price = getattr(t.fast_info, "last_price", None)
        return round(price, 4) if price is not None else None
    except Exception as e:
        logger.error(f"YF fetch failed for {symbol}: {e}")
        return None


def fetch_treasury_yield() -> Optional[float]:
    """Fetch US 10-Year Treasury yield (^TNX)."""
    return _yf_last_price("^TNX")


def fetch_dollar_index() -> Optional[float]:
    """Fetch US Dollar Index (DX-Y.NYB)."""
    return _yf_last_price("DX-Y.NYB")


def fetch_vix() -> Optional[float]:
    """Fetch CBOE Volatility Index (^VIX)."""
    return _yf_last_price("^VIX")


def fetch_usdjpy() -> Optional[float]:
    """Fetch USD/JPY exchange rate."""
    return _yf_last_price("JPY=X")


def fetch_cpi_latest() -> Optional[dict]:
    """Fetch latest CPI data from BLS API (no key required).

    Returns:
        Dict with 'value', 'year', 'period', 'periodName', or None.
    """
    try:
        url = "https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        series = data.get("Results", {}).get("series", [{}])[0]
        latest = series.get("data", [{}])[0]
        return {
            "value": float(latest.get("value", 0)),
            "year": latest.get("year"),
            "period": latest.get("period"),
            "periodName": latest.get("periodName"),
        }
    except Exception as e:
        logger.error(f"CPI fetch failed: {e}")
        return None


def fetch_fed_funds_rate() -> Optional[float]:
    """Fetch effective Federal Funds Rate via Yahoo Finance (^IRX as proxy, 13-week T-bill)."""
    return _yf_last_price("^IRX")


def macro_snapshot() -> dict:
    """Fetch all macro indicators and return as a dict."""
    return {
        "fear_greed": fetch_fear_greed_index(),
        "us10y_yield": fetch_treasury_yield(),
        "dollar_index": fetch_dollar_index(),
        "vix": fetch_vix(),
        "usdjpy": fetch_usdjpy(),
        "cpi": fetch_cpi_latest(),
        "fed_funds_rate": fetch_fed_funds_rate(),
    }
