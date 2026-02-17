"""Discord-formatted report generation."""

import logging
from datetime import datetime

from src.data.fetcher import ALL_TICKERS, US_STOCKS, CRYPTO, INDICES, fetch_current_snapshot
from src.portfolio.tracker import portfolio_snapshot

logger = logging.getLogger(__name__)


def daily_market_summary() -> str:
    """Generate daily market summary for Discord."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    snapshot = fetch_current_snapshot(ALL_TICKERS)

    lines = [f"📊 **SENTINEL Market Summary** — {now}\n"]

    # Group by category
    categories = {
        "🇺🇸 US Stocks": US_STOCKS,
        "🪙 Crypto": CRYPTO,
        "📈 Indices": INDICES,
        "💱 FX/Bonds/Gold": ["JPY=X", "^TNX", "GC=F"],
        "🇯🇵 Japan": ["6600.T"],
    }

    for cat_name, tickers in categories.items():
        lines.append(f"\n**{cat_name}**")
        for t in tickers:
            if t in snapshot:
                s = snapshot[t]
                emoji = "🟢" if s["change_pct"] >= 0 else "🔴"
                lines.append(f"{emoji} `{t:8s}` {s['price']:>10,.2f}  ({s['change_pct']:+.2f}%)")
            else:
                lines.append(f"⚪ `{t:8s}` N/A")

    return "\n".join(lines)


def prediction_report(predictions: list[dict]) -> str:
    """Format prediction results for Discord.

    Args:
        predictions: List of prediction dicts from blind_predict.
    """
    lines = ["🔮 **SENTINEL Predictions**\n"]
    for p in predictions:
        ticker = p.get("ticker", "?")
        direction = p.get("direction", "?")
        confidence = p.get("confidence", 0)
        emoji = {"UP": "📈", "DOWN": "📉", "FLAT": "➡️"}.get(direction, "❓")
        lines.append(f"{emoji} **{ticker}**: {direction} (confidence: {confidence}%)")
        reasons = p.get("reasoning", [])
        if reasons:
            for r in reasons[:3]:
                lines.append(f"  • {r}")
    return "\n".join(lines)


def portfolio_report() -> str:
    """Generate portfolio report for Discord."""
    lines = ["💼 **Fund Portfolio**\n"]
    snap = portfolio_snapshot()
    for code, info in snap.items():
        name = info["name"]
        nav = info["nav"]
        if nav is not None:
            lines.append(f"• **{name}**: ¥{nav:,.0f}")
        else:
            lines.append(f"• **{name}**: 取得不可")
    return "\n".join(lines)
