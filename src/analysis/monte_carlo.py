"""
Monte Carlo Simulation for price paths, VaR, and portfolio risk analysis.
"""

import logging

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def simulate_price_paths(
    current_price: float,
    mu: float,
    sigma: float,
    days: int = 30,
    n_simulations: int = 10_000,
    dt: float = 1 / 252,
) -> np.ndarray:
    """
    Geometric Brownian Motion price path simulation.

    Returns ndarray of shape (n_simulations, days+1) including the starting price.
    """
    z = np.random.standard_normal((n_simulations, days))
    daily_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    price_paths = np.zeros((n_simulations, days + 1))
    price_paths[:, 0] = current_price
    price_paths[:, 1:] = current_price * np.exp(np.cumsum(daily_returns, axis=1))
    return price_paths


def calc_var(
    simulations: np.ndarray,
    confidence: float = 0.95,
) -> dict:
    """
    Value at Risk from simulated terminal prices.

    Args:
        simulations: price paths array (n_simulations, days+1)
        confidence: confidence level (e.g. 0.95 for 95% VaR)

    Returns dict with var_absolute, var_pct, initial_price.
    """
    initial = simulations[:, 0].mean()
    terminal = simulations[:, -1]
    returns = (terminal - initial) / initial

    var_pct = np.percentile(returns, (1 - confidence) * 100)
    var_abs = initial * var_pct

    return {
        "var_pct": float(var_pct),
        "var_absolute": float(var_abs),
        "initial_price": float(initial),
        "confidence": confidence,
    }


def calc_expected_range(
    simulations: np.ndarray,
    lower_pct: float = 5.0,
    upper_pct: float = 95.0,
) -> dict:
    """Expected price range at terminal date (5th-95th percentile by default)."""
    terminal = simulations[:, -1]
    return {
        "lower": float(np.percentile(terminal, lower_pct)),
        "upper": float(np.percentile(terminal, upper_pct)),
        "median": float(np.median(terminal)),
        "mean": float(np.mean(terminal)),
    }


def portfolio_monte_carlo(
    tickers: list[str],
    weights: list[float],
    days: int = 30,
    n_simulations: int = 10_000,
    lookback_period: str = "1y",
) -> dict:
    """
    Portfolio-level Monte Carlo risk analysis.

    Downloads historical data, estimates mu/sigma per asset,
    simulates correlated paths via Cholesky decomposition,
    and returns VaR + expected range for the weighted portfolio.
    """
    weights = np.array(weights)
    weights = weights / weights.sum()

    data = yf.download(tickers, period=lookback_period, auto_adjust=True)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(tickers[0])
    data = data.dropna()

    log_returns = np.log(data / data.shift(1)).dropna()
    mu = log_returns.mean().values * 252
    sigma = log_returns.std().values * np.sqrt(252)
    corr_matrix = log_returns.corr().values

    # Cholesky decomposition for correlated random walks
    L = np.linalg.cholesky(corr_matrix)
    dt = 1 / 252
    n_assets = len(tickers)

    current_prices = data.iloc[-1].values
    portfolio_value = (current_prices * weights).sum()

    # Simulate
    port_paths = np.zeros((n_simulations, days + 1))
    port_paths[:, 0] = portfolio_value

    asset_prices = np.tile(current_prices, (n_simulations, 1))

    for t in range(1, days + 1):
        z = np.random.standard_normal((n_simulations, n_assets))
        correlated_z = z @ L.T
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * correlated_z
        asset_prices = asset_prices * np.exp(drift + diffusion)
        port_paths[:, t] = (asset_prices * weights).sum(axis=1)

    var_info = calc_var(port_paths)
    range_info = calc_expected_range(port_paths)

    return {
        "tickers": tickers,
        "weights": weights.tolist(),
        "days": days,
        "n_simulations": n_simulations,
        "current_portfolio_value": float(portfolio_value),
        "var": var_info,
        "expected_range": range_info,
        "simulations": port_paths,
    }
