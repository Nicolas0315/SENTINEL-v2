"""
Pair Trading Analysis — Engle-Granger cointegration-based pair trading.

Reference: quant-trading/Pair trading backtest.py
"""

import logging
from itertools import combinations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import yfinance as yf

logger = logging.getLogger(__name__)

# Default candidate pairs
DEFAULT_PAIRS = [
    ("NVDA", "AVGO"),   # Semiconductors
    ("GOOGL", "META"),  # Ad-tech
    ("AAPL", "MSFT"),   # Big-tech
]


def test_cointegration(
    series1: pd.Series,
    series2: pd.Series,
    significance: float = 0.05,
) -> dict:
    """
    Engle-Granger two-step cointegration test.

    Returns dict with keys:
        cointegrated (bool), p_value (float), model (OLS result),
        residuals (Series), adj_coefficient (float | None)
    """
    # Step 1: long-run equilibrium regression  Y = a + b*X + eps
    model = sm.OLS(series2, sm.add_constant(series1)).fit()
    residuals = model.resid

    adf_stat, p_value, *_ = adfuller(residuals)

    if p_value > significance:
        return {
            "cointegrated": False,
            "p_value": p_value,
            "model": model,
            "residuals": residuals,
            "adj_coefficient": None,
        }

    # Step 2: error-correction model
    x_diff = series1.diff().dropna()
    y_diff = series2.diff().dropna()
    lagged_resid = residuals.shift(1).dropna()

    common_idx = x_diff.index.intersection(lagged_resid.index)
    ecm_x = sm.add_constant(pd.concat([x_diff.loc[common_idx], lagged_resid.loc[common_idx]], axis=1))
    ecm_y = y_diff.loc[common_idx]

    ecm_model = sm.OLS(ecm_y, ecm_x).fit()
    adj_coeff = ecm_model.params.iloc[-1]

    cointegrated = adj_coeff < 0
    return {
        "cointegrated": cointegrated,
        "p_value": p_value,
        "model": model,
        "residuals": residuals,
        "adj_coefficient": adj_coeff,
    }


def find_pairs(
    tickers: list[str],
    period: str = "1y",
    significance: float = 0.05,
) -> list[dict]:
    """Test all ticker combinations for cointegration. Returns list of cointegrated pairs."""
    data = yf.download(tickers, period=period, group_by="ticker", auto_adjust=True)

    results = []
    for t1, t2 in combinations(tickers, 2):
        try:
            s1 = data[t1]["Close"].dropna()
            s2 = data[t2]["Close"].dropna()
            common = s1.index.intersection(s2.index)
            res = test_cointegration(s1.loc[common], s2.loc[common], significance)
            if res["cointegrated"]:
                results.append({"ticker1": t1, "ticker2": t2, **res})
                logger.info(f"Cointegrated pair found: {t1}/{t2} (p={res['p_value']:.4f})")
        except Exception as e:
            logger.warning(f"Error testing {t1}/{t2}: {e}")

    return results


def calc_spread(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """OLS-based spread: residual of regressing series2 on series1."""
    model = sm.OLS(series2, sm.add_constant(series1)).fit()
    return model.resid


def generate_pair_signals(
    series1: pd.Series,
    series2: pd.Series,
    z_threshold: float = 2.0,
    bandwidth: int = 250,
) -> pd.DataFrame:
    """
    Generate Z-score-based pair trading signals.

    Signals: +1 = long spread (long s2, short s1), -1 = short spread, 0 = flat.
    """
    df = pd.DataFrame({"asset1": series1, "asset2": series2})
    df["signal"] = 0
    df["z_score"] = np.nan

    for i in range(bandwidth, len(df)):
        window1 = df["asset1"].iloc[i - bandwidth : i]
        window2 = df["asset2"].iloc[i - bandwidth : i]

        res = test_cointegration(window1, window2)
        if not res["cointegrated"]:
            continue

        model = res["model"]
        fitted = model.predict(sm.add_constant(df["asset1"].iloc[i : i + 1]))
        residual = df["asset2"].iloc[i] - fitted.iloc[0]
        z = (residual - res["residuals"].mean()) / res["residuals"].std()
        df.iloc[i, df.columns.get_loc("z_score")] = z

        if z > z_threshold:
            df.iloc[i, df.columns.get_loc("signal")] = -1  # short spread
        elif z < -z_threshold:
            df.iloc[i, df.columns.get_loc("signal")] = 1   # long spread

    df["position"] = df["signal"].replace(0, np.nan).ffill().fillna(0).astype(int)
    return df


@dataclass
class PairTrader:
    """Manage a single pair trade."""

    ticker1: str
    ticker2: str
    z_threshold: float = 2.0
    bandwidth: int = 250
    capital: float = 100_000.0
    _position: int = 0  # -1, 0, 1
    _history: list = field(default_factory=list)

    def fetch_data(self, period: str = "1y") -> pd.DataFrame:
        d1 = yf.download(self.ticker1, period=period, auto_adjust=True)["Close"]
        d2 = yf.download(self.ticker2, period=period, auto_adjust=True)["Close"]
        common = d1.index.intersection(d2.index)
        return pd.DataFrame({"asset1": d1.loc[common], "asset2": d2.loc[common]})

    def check_cointegration(self, period: str = "1y") -> dict:
        data = self.fetch_data(period)
        return test_cointegration(data["asset1"], data["asset2"])

    def generate_signals(self, period: str = "2y") -> pd.DataFrame:
        data = self.fetch_data(period)
        return generate_pair_signals(
            data["asset1"], data["asset2"],
            z_threshold=self.z_threshold,
            bandwidth=self.bandwidth,
        )

    def current_z_score(self, period: str = "1y") -> Optional[float]:
        data = self.fetch_data(period)
        spread = calc_spread(data["asset1"], data["asset2"])
        z = (spread.iloc[-1] - spread.mean()) / spread.std()
        return float(z)

    def status(self) -> dict:
        return {
            "pair": f"{self.ticker1}/{self.ticker2}",
            "position": self._position,
            "capital": self.capital,
            "history_count": len(self._history),
        }
