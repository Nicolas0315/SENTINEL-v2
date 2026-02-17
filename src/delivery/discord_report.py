"""Discord-formatted report generation."""

import logging
from datetime import datetime

from src.data.fetcher import ALL_TICKERS, US_STOCKS, CRYPTO, INDICES, fetch_current_snapshot
from src.data.macro import macro_snapshot
from src.data.crypto import fetch_crypto_snapshot
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

    # Macro indicators
    macro = macro_snapshot()
    lines.append("\n**🏛️ Macro Indicators**")
    fg = macro.get("fear_greed")
    if fg:
        lines.append(f"• Fear & Greed: **{fg['score']}** ({fg['rating']})")
    if macro.get("us10y_yield") is not None:
        lines.append(f"• US 10Y Yield: **{macro['us10y_yield']:.2f}%**")
    if macro.get("dollar_index") is not None:
        lines.append(f"• Dollar Index: **{macro['dollar_index']:.2f}**")
    if macro.get("vix") is not None:
        lines.append(f"• VIX: **{macro['vix']:.2f}**")
    if macro.get("usdjpy") is not None:
        lines.append(f"• USD/JPY: **{macro['usdjpy']:.2f}**")
    if macro.get("fed_funds_rate") is not None:
        lines.append(f"• Fed Funds (13w proxy): **{macro['fed_funds_rate']:.2f}%**")
    cpi = macro.get("cpi")
    if cpi:
        lines.append(f"• CPI: **{cpi['value']}** ({cpi.get('periodName', '')} {cpi.get('year', '')})")

    # Crypto snapshot
    crypto_snap = fetch_crypto_snapshot()
    lines.append("\n**🪙 Crypto Overview**")
    for label, key in [("BTC", "btc"), ("WLD", "wld")]:
        coin = crypto_snap.get(key)
        if coin and coin.get("price_usd") is not None:
            emoji = "🟢" if coin["change_24h_pct"] >= 0 else "🔴"
            lines.append(f"{emoji} **{label}**: ${coin['price_usd']:,.2f} ({coin['change_24h_pct']:+.2f}%)")
    btc_fg = crypto_snap.get("btc_fear_greed")
    if btc_fg:
        lines.append(f"• BTC Fear & Greed: **{btc_fg['value']}** ({btc_fg['classification']})")

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
