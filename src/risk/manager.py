"""
Risk Management — position sizing, performance metrics, and risk reporting.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calc_position_size(
    capital: float,
    risk_pct: float,
    stop_loss_pct: float,
) -> dict:
    """
    Calculate position size based on risk budget.

    Args:
        capital: total capital
        risk_pct: fraction of capital to risk (e.g. 0.02 = 2%)
        stop_loss_pct: stop-loss distance as fraction (e.g. 0.05 = 5%)

    Returns dict with risk_amount, position_size, stop_loss_pct.
    """
    risk_amount = capital * risk_pct
    position_size = risk_amount / stop_loss_pct if stop_loss_pct > 0 else 0.0
    return {
        "capital": capital,
        "risk_pct": risk_pct,
        "risk_amount": risk_amount,
        "stop_loss_pct": stop_loss_pct,
        "position_size": position_size,
    }


def calc_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05,
    periods_per_year: int = 252,
) -> float:
    """Annualized Sharpe ratio."""
    if returns.std() == 0:
        return 0.0
    excess = returns - risk_free_rate / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / excess.std())


def calc_max_drawdown(prices: pd.Series) -> dict:
    """
    Maximum drawdown from a price series.

    Returns dict with max_drawdown (negative float), peak_date, trough_date.
    """
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax
    trough_idx = drawdown.idxmin()
    peak_idx = prices.loc[:trough_idx].idxmax()
    return {
        "max_drawdown": float(drawdown.min()),
        "peak_date": str(peak_idx),
        "trough_date": str(trough_idx),
    }


def calc_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05,
    periods_per_year: int = 252,
) -> float:
    """Annualized Sortino ratio (downside deviation only)."""
    excess = returns - risk_free_rate / periods_per_year
    downside = excess[excess < 0]
    downside_std = np.sqrt((downside**2).mean()) if len(downside) > 0 else 0.0
    if downside_std == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * excess.mean() / downside_std)


def risk_report(
    portfolio: pd.DataFrame,
    risk_free_rate: float = 0.05,
) -> dict:
    """
    Generate a risk report for a portfolio.

    Expects portfolio DataFrame with 'total_value' or 'Close' column.
    """
    if "total_value" in portfolio.columns:
        prices = portfolio["total_value"]
    elif "Close" in portfolio.columns:
        prices = portfolio["Close"]
    else:
        prices = portfolio.iloc[:, 0]

    returns = prices.pct_change().dropna()

    sharpe = calc_sharpe_ratio(returns, risk_free_rate)
    sortino = calc_sortino_ratio(returns, risk_free_rate)
    dd = calc_max_drawdown(prices)

    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
    ann_return = (1 + total_return) ** (252 / len(prices)) - 1 if len(prices) > 1 else 0.0
    ann_vol = float(returns.std() * np.sqrt(252))

    return {
        "total_return": float(total_return),
        "annualized_return": float(ann_return),
        "annualized_volatility": ann_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": dd,
        "daily_return_mean": float(returns.mean()),
        "daily_return_std": float(returns.std()),
        "num_trading_days": len(returns),
    }
