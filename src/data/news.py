"""News fetcher via RSS feeds (no API keys required)."""

import logging
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (SENTINEL-v2)"}
_TIMEOUT = 15


def _parse_rss(xml_text: str) -> list[dict]:
    """Parse RSS XML into list of {title, url, published}."""
    items = []
    try:
        root = ElementTree.fromstring(xml_text)
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "published": pub_date,
                })
    except ElementTree.ParseError as e:
        logger.error(f"RSS parse error: {e}")
    return items


def fetch_google_news(query: str, num: int = 10) -> list[dict]:
    """Fetch Google News RSS for a query.

    Args:
        query: Search query string.
        num: Max number of results.

    Returns:
        List of {title, url, published}.
    """
    try:
        url = "https://news.google.com/rss/search"
        params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        return _parse_rss(resp.text)[:num]
    except Exception as e:
        logger.error(f"Google News fetch failed for '{query}': {e}")
        return []


def fetch_market_headlines(num: int = 10) -> list[dict]:
    """Fetch market-related headlines from multiple queries.

    Returns:
        List of {title, url, published} sorted by recency.
    """
    queries = ["stock market", "Federal Reserve", "crypto market"]
    all_items: list[dict] = []
    for q in queries:
        all_items.extend(fetch_google_news(q, num=5))

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict] = []
    for item in all_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique[:num]
