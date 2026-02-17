"""Market data fetcher using Yahoo Finance API."""

import logging
from typing import Optional

import pandas as pd
import yfinance as yf
import requests

logger = logging.getLogger(__name__)

# Ticker universe
US_STOCKS = ["NVDA", "AAPL", "GOOGL", "META", "AMZN", "MSFT", "AVGO", "NFLX", "CRWD", "NOW"]
JP_STOCKS = ["6600.T"]  # KIOXIA
CRYPTO = ["BTC-USD", "WLD-USD"]  # Bitcoin, Worldcoin
COMMODITIES = ["GC=F"]  # Gold futures
INDICES = ["^GSPC", "^VIX", "^SOX"]  # S&P500, VIX, SOX
FX = ["JPY=X"]  # USD/JPY
BONDS = ["^TNX"]  # US 10Y Treasury

ALL_TICKERS = US_STOCKS + JP_STOCKS + CRYPTO + COMMODITIES + INDICES + FX + BONDS


def fetch_prices(
    tickers: list[str],
    period: str = "1mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch historical prices for given tickers.

    Args:
        tickers: List of Yahoo Finance ticker symbols.
        period: Data period (e.g. '1mo', '3mo', '1y').
        interval: Data interval (e.g. '1d', '1h').

    Returns:
        DataFrame with MultiIndex columns (Price, Ticker).
    """
    try:
        logger.info(f"Fetching prices for {len(tickers)} tickers, period={period}, interval={interval}")
        data = yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False)
        if data.empty:
            logger.warning("No data returned from yfinance")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        return pd.DataFrame()


def fetch_current_snapshot(tickers: list[str]) -> dict:
    """Fetch current price snapshot for given tickers.

    Returns:
        Dict mapping ticker -> {price, change, change_pct, volume, name}.
    """
    snapshot: dict = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = getattr(info, "last_price", None)
            prev = getattr(info, "previous_close", None)
            if price is not None:
                change = (price - prev) if prev else 0.0
                change_pct = (change / prev * 100) if prev else 0.0
                snapshot[ticker] = {
                    "price": round(price, 4),
                    "prev_close": round(prev, 4) if prev else None,
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 2),
                }
            else:
                logger.warning(f"No price for {ticker}")
        except Exception as e:
            logger.error(f"Failed to fetch snapshot for {ticker}: {e}")
    return snapshot


def fetch_fund_nav_yahoo(fund_code: str) -> Optional[float]:
    """Attempt to fetch Japanese mutual fund NAV from Yahoo Finance Japan.

    Args:
        fund_code: Fund code (e.g. '03311187').

    Returns:
        NAV as float or None if unavailable.
    """
    try:
        url = f"https://finance.yahoo.co.jp/quote/{fund_code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and "基準価額" in resp.text:
            # Simple extraction - look for price pattern
            import re
            match = re.search(r'class="[^"]*StyledNumber[^"]*"[^>]*>([0-9,]+)', resp.text)
            if match:
                return float(match.group(1).replace(",", ""))
        logger.warning(f"Could not parse NAV for fund {fund_code}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch fund NAV for {fund_code}: {e}")
        return None
