#!/usr/bin/env python3
"""Backtest demo: run blind prediction backtest on S&P500 and NVDA."""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.predictor import backtest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"SENTINEL v2 - Backtest Demo")
    print(f"Period: {start_date} → {end_date}")
    print(f"{'='*60}\n")

    for ticker in ["^GSPC", "NVDA"]:
        print(f"\n--- {ticker} ---")
        df = backtest(ticker, start_date, end_date)
        if df.empty:
            print(f"No results for {ticker}")
            continue

        total = len(df)
        hits = df["hit"].sum()
        accuracy = hits / total * 100

        print(f"Total predictions: {total}")
        print(f"Hits: {hits}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"\nAvg confidence: {df['confidence'].mean():.1f}%")

        # Show direction breakdown
        for direction in ["UP", "DOWN", "FLAT"]:
            subset = df[df["predicted"] == direction]
            if len(subset) > 0:
                dir_acc = subset["hit"].mean() * 100
                print(f"  {direction}: {len(subset)} predictions, {dir_acc:.0f}% accurate")

        print(f"\nDetailed results:")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
