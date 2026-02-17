#!/usr/bin/env python3
"""Daily SENTINEL run: fetch data, analyze, predict, report."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.fetcher import ALL_TICKERS, US_STOCKS, fetch_prices
from src.analysis.technical import generate_signals
from src.analysis.predictor import blind_predict
from src.delivery.discord_report import daily_market_summary, prediction_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"=== SENTINEL Daily Run: {today} ===")

    # 1. Fetch market data
    logger.info("Fetching market data...")
    prices = fetch_prices(ALL_TICKERS, period="3mo", interval="1d")

    # 2. Technical analysis for US stocks
    logger.info("Running technical analysis...")
    analyses = {}
    for ticker in US_STOCKS:
        try:
            if ticker in prices.columns.get_level_values(0):
                df = prices[ticker].dropna()
                if not df.empty:
                    signals = generate_signals(df)
                    analyses[ticker] = signals
                    logger.info(f"{ticker}: {signals.get('overall', {}).get('signal', 'N/A')}")
        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}")

    # 3. Generate predictions
    logger.info("Generating predictions...")
    prediction_tickers = US_STOCKS + ["BTC-USD", "^GSPC"]
    predictions = []
    for ticker in prediction_tickers:
        pred = blind_predict(ticker, as_of_date=today)
        predictions.append(pred)
        logger.info(f"Prediction {ticker}: {pred.get('direction')} ({pred.get('confidence')}%)")

    # 4. Generate reports
    logger.info("Generating reports...")
    market_summary = daily_market_summary()
    pred_report = prediction_report(predictions)
    print("\n" + market_summary)
    print("\n" + pred_report)

    # 5. Save predictions
    output_dir = Path(__file__).parent.parent / "data" / "predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{today}.json"
    result = {
        "date": today,
        "predictions": predictions,
        "analyses": {k: _serialize(v) for k, v in analyses.items()},
    }
    output_file.write_text(json.dumps(result, indent=2, default=str))
    logger.info(f"Results saved to {output_file}")


def _serialize(obj):
    """Make objects JSON-serializable."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj


if __name__ == "__main__":
    main()
