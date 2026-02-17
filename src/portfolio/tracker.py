"""Portfolio tracker for Japanese mutual funds."""

import logging
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Nicolas's fund portfolio
FUNDS = {
    "03311187": "eMAXIS Slim 米国株式(S&P500)",
    "04311181": "iFreeNEXT FANG+インデックス",
    "04312257": "iFreeNEXT 全世界半導体株インデックス",
    "9I312261": "楽天・ゴールド・ファンド",
}


def fetch_fund_nav(fund_code: str) -> Optional[float]:
    """Fetch latest NAV for a Japanese mutual fund.

    Tries Yahoo Finance Japan and Minkabu as sources.

    Args:
        fund_code: Fund code (e.g. '03311187').

    Returns:
        NAV as float or None if unavailable.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    # Try Minkabu (itf.minkabu.jp)
    try:
        url = f"https://itf.minkabu.jp/fund/{fund_code}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            match = re.search(r'class="[^"]*fsi[^"]*"[^>]*>([0-9,]+)', resp.text)
            if not match:
                match = re.search(r'基準価額[^0-9]*([0-9,]+)\s*円', resp.text)
            if match:
                nav = float(match.group(1).replace(",", ""))
                logger.info(f"Fund {fund_code} NAV: {nav}")
                return nav
    except Exception as e:
        logger.warning(f"Minkabu fetch failed for {fund_code}: {e}")

    # Try Yahoo Finance JP
    try:
        url = f"https://finance.yahoo.co.jp/quote/{fund_code}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            match = re.search(r'>([0-9,]+)</span>\s*円', resp.text)
            if match:
                nav = float(match.group(1).replace(",", ""))
                logger.info(f"Fund {fund_code} NAV (Yahoo): {nav}")
                return nav
    except Exception as e:
        logger.warning(f"Yahoo fetch failed for {fund_code}: {e}")

    logger.error(f"Could not fetch NAV for fund {fund_code}")
    return None


def portfolio_snapshot() -> dict:
    """Fetch NAV for all tracked funds.

    Returns:
        Dict mapping fund_code -> {name, nav, status}.
    """
    result = {}
    for code, name in FUNDS.items():
        nav = fetch_fund_nav(code)
        result[code] = {
            "name": name,
            "nav": nav,
            "status": "ok" if nav is not None else "error",
        }
    return result
