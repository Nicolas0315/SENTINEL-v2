"""Crypto market data fetcher using public APIs (no keys required)."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (SENTINEL-v2)"}
_TIMEOUT = 15
_CG_BASE = "https://api.coingecko.com/api/v3"


def _coingecko_price(coin_id: str) -> Optional[dict]:
    """Fetch price data from CoinGecko for a single coin.

    Returns:
        Dict with 'price_usd', 'change_24h_pct', 'market_cap', or None.
    """
    try:
        url = f"{_CG_BASE}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
        }
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get(coin_id, {})
        return {
            "price_usd": data.get("usd"),
            "change_24h_pct": round(data.get("usd_24h_change", 0), 2),
            "market_cap": data.get("usd_market_cap"),
        }
    except Exception as e:
        logger.error(f"CoinGecko fetch failed for {coin_id}: {e}")
        return None


def fetch_btc_price() -> Optional[dict]:
    """Fetch current BTC price and 24h change."""
    return _coingecko_price("bitcoin")


def fetch_wld_price() -> Optional[dict]:
    """Fetch current WLD (Worldcoin) price and 24h change."""
    return _coingecko_price("worldcoin-wld")


def fetch_btc_fear_greed() -> Optional[dict]:
    """Fetch Bitcoin Fear & Greed Index from alternative.me.

    Returns:
        Dict with 'value' (0-100) and 'classification', or None.
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        entry = resp.json().get("data", [{}])[0]
        return {
            "value": int(entry.get("value", 0)),
            "classification": entry.get("value_classification", "Unknown"),
        }
    except Exception as e:
        logger.error(f"BTC Fear & Greed fetch failed: {e}")
        return None


def fetch_crypto_snapshot() -> dict:
    """Fetch all crypto indicators."""
    return {
        "btc": fetch_btc_price(),
        "wld": fetch_wld_price(),
        "btc_fear_greed": fetch_btc_fear_greed(),
    }
