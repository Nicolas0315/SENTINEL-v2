"""Paper trading engine with JSON persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path(__file__).parent.parent.parent / "data" / "paper_portfolio.json"


class PaperTrader:
    """Simulated trading engine with virtual cash."""

    def __init__(self, initial_cash: float = 100_000.0):
        self.cash: float = initial_cash
        self.positions: dict[str, dict] = {}  # ticker -> {shares, avg_cost}
        self.transactions: list[dict] = []

    def _get_price(self, ticker: str) -> Optional[float]:
        """Fetch current market price for a ticker."""
        try:
            t = yf.Ticker(ticker)
            price = getattr(t.fast_info, "last_price", None)
            return float(price) if price is not None else None
        except Exception as e:
            logger.error(f"Failed to get price for {ticker}: {e}")
            return None

    def buy(self, ticker: str, shares: int, price: Optional[float] = None) -> dict:
        """Buy shares of a ticker.

        Args:
            ticker: Symbol to buy.
            shares: Number of shares.
            price: Override price (fetches market price if None).

        Returns:
            Transaction record.
        """
        if price is None:
            price = self._get_price(ticker)
            if price is None:
                return {"error": f"Cannot get price for {ticker}"}

        cost = price * shares
        if cost > self.cash:
            return {"error": f"Insufficient cash. Need ${cost:.2f}, have ${self.cash:.2f}"}

        self.cash -= cost
        if ticker in self.positions:
            pos = self.positions[ticker]
            total_shares = pos["shares"] + shares
            pos["avg_cost"] = (pos["avg_cost"] * pos["shares"] + cost) / total_shares
            pos["shares"] = total_shares
        else:
            self.positions[ticker] = {"shares": shares, "avg_cost": price}

        txn = {
            "type": "BUY",
            "ticker": ticker,
            "shares": shares,
            "price": round(price, 4),
            "cost": round(cost, 2),
            "timestamp": datetime.now().isoformat(),
        }
        self.transactions.append(txn)
        logger.info(f"BUY {shares} {ticker} @ ${price:.2f} = ${cost:.2f}")
        return txn

    def sell(self, ticker: str, shares: int, price: Optional[float] = None) -> dict:
        """Sell shares of a ticker.

        Args:
            ticker: Symbol to sell.
            shares: Number of shares.
            price: Override price (fetches market price if None).

        Returns:
            Transaction record.
        """
        if ticker not in self.positions or self.positions[ticker]["shares"] < shares:
            held = self.positions.get(ticker, {}).get("shares", 0)
            return {"error": f"Insufficient shares. Have {held}, want to sell {shares}"}

        if price is None:
            price = self._get_price(ticker)
            if price is None:
                return {"error": f"Cannot get price for {ticker}"}

        proceeds = price * shares
        self.cash += proceeds
        pos = self.positions[ticker]
        pnl = (price - pos["avg_cost"]) * shares
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del self.positions[ticker]

        txn = {
            "type": "SELL",
            "ticker": ticker,
            "shares": shares,
            "price": round(price, 4),
            "proceeds": round(proceeds, 2),
            "pnl": round(pnl, 2),
            "timestamp": datetime.now().isoformat(),
        }
        self.transactions.append(txn)
        logger.info(f"SELL {shares} {ticker} @ ${price:.2f} = ${proceeds:.2f} (PnL: ${pnl:.2f})")
        return txn

    def get_portfolio(self) -> dict:
        """Get current portfolio state with market values."""
        positions_detail = {}
        total_value = self.cash
        for ticker, pos in self.positions.items():
            current = self._get_price(ticker)
            mkt_val = current * pos["shares"] if current else 0
            total_value += mkt_val
            positions_detail[ticker] = {
                "shares": pos["shares"],
                "avg_cost": round(pos["avg_cost"], 4),
                "current_price": round(current, 4) if current else None,
                "market_value": round(mkt_val, 2),
                "unrealized_pnl": round((current - pos["avg_cost"]) * pos["shares"], 2) if current else None,
            }
        return {
            "cash": round(self.cash, 2),
            "positions": positions_detail,
            "total_value": round(total_value, 2),
        }

    def get_pnl(self) -> dict:
        """Calculate realized and unrealized P&L."""
        realized = sum(t.get("pnl", 0) for t in self.transactions if t["type"] == "SELL")
        unrealized = 0.0
        for ticker, pos in self.positions.items():
            current = self._get_price(ticker)
            if current:
                unrealized += (current - pos["avg_cost"]) * pos["shares"]
        return {
            "realized_pnl": round(realized, 2),
            "unrealized_pnl": round(unrealized, 2),
            "total_pnl": round(realized + unrealized, 2),
        }

    def save_state(self, path: Optional[str] = None) -> None:
        """Persist portfolio state to JSON."""
        p = Path(path) if path else DEFAULT_STATE_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "cash": self.cash,
            "positions": self.positions,
            "transactions": self.transactions,
        }
        p.write_text(json.dumps(state, indent=2, default=str))
        logger.info(f"State saved to {p}")

    def load_state(self, path: Optional[str] = None) -> None:
        """Load portfolio state from JSON."""
        p = Path(path) if path else DEFAULT_STATE_PATH
        if not p.exists():
            logger.warning(f"No state file at {p}")
            return
        state = json.loads(p.read_text())
        self.cash = state.get("cash", 100_000.0)
        self.positions = state.get("positions", {})
        self.transactions = state.get("transactions", [])
        logger.info(f"State loaded from {p}")
