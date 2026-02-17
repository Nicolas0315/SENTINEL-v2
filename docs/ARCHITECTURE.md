# Architecture

## System Overview

SENTINEL is structured as a modular pipeline architecture with five core layers: data ingestion, analysis, portfolio management, trust verification, and delivery.

```
SENTINEL Core
├── data-pipeline/          # Data Ingestion Layer
│   ├── market/             # Stocks, Forex, Commodities
│   ├── macro/              # Macroeconomic Indicators
│   ├── social/             # Social Sentiment
│   ├── onchain/            # Blockchain Data
│   └── news/               # News & Filings
├── analysis/               # Analysis Engine
│   ├── scoring/            # Indicator Scoring
│   ├── anomaly/            # Anomaly Detection
│   ├── correlation/        # Cross-Signal Correlation
│   └── prediction/         # Predictive Models
├── portfolio/              # Portfolio Management
│   ├── tracker/            # NAV & Valuation Tracking
│   ├── rebalance/          # Rebalance Alerts
│   └── paper-trade/        # Paper Trading
├── trust/                  # Trust Layer (Katala Bridge)
│   ├── world-id/           # World ID API Integration
│   ├── personhood/         # Proof of Personhood Verification
│   └── platform-audit/     # Platform Metrics Verification
└── delivery/               # Delivery Layer
    ├── discord/            # Discord Channel Delivery
    ├── alerts/             # Anomaly Alerts
    └── reports/            # Weekly/Monthly Reports
```

## Data Pipeline

### market/
Real-time and historical market data ingestion.

| Source | Data | Update Frequency |
|--------|------|-----------------|
| Yahoo Finance (`yfinance`) | Stock prices, ETFs, indices | 1min–daily |
| CoinGecko API | Crypto prices (BTC, WLD) | 5min |
| Bitflyer API | BTC/JPY orderbook, trades | Real-time |

### macro/
Macroeconomic indicator tracking.

| Source | Data | Update Frequency |
|--------|------|-----------------|
| FRED API | Fed Funds Rate, CPI, PCE, M2, GDP, Employment | As released |
| BIS | Cross-border financial statistics | Quarterly |
| IMF | World Economic Outlook data | Semi-annual |

### social/
Social media sentiment analysis and key person monitoring.

| Source | Data | Method |
|--------|------|--------|
| X (Twitter) API | Key person tweets, trending topics | Polling / Streaming |
| RSS Feeds | Blog posts, analyst commentary | Polling |

**Key Persons Monitored:**
- `@elonmusk` — DOGE, Tesla, xAI impact
- `@realDonaldTrump` — Tariffs, trade policy, financial regulation
- `@takaichi_sanae` — Japan economic security policy
- `@kantei` — Japan PM Office official

### onchain/
Blockchain data for crypto analysis.

| Source | Data |
|--------|------|
| Bitcoin RPC / Blockchain.info | BTC whale movements, hash rate, mempool |
| Worldcoin/WLD explorers | WLD token metrics, World ID adoption |

### news/
News and regulatory filing aggregation.

| Source | Data |
|--------|------|
| Google News RSS | Filtered news by keyword/topic |
| SEC EDGAR | 10-K, 10-Q, 8-K filings for watched companies |

## Analysis Engine

### scoring/
All indicators are normalized to a **0–100 scale** for unified comparison:
- 0–20: Extreme bearish / risk-off
- 20–40: Bearish
- 40–60: Neutral
- 60–80: Bullish
- 80–100: Extreme bullish / risk-on

### anomaly/
Detects unusual patterns across signals:
- **Volume anomaly**: Sudden volume spikes (>2σ from 20-day mean)
- **Sentiment shift**: Rapid change in social sentiment polarity
- **Cross-signal divergence**: Price moving opposite to sentiment or macro signals
- **Market manipulation signals**: SNS hype × volume anomaly correlation (Katala integration)

### correlation/
Cross-domain correlation analysis:
- Political speech → market reaction (lag analysis)
- Social sentiment → price movement
- Macro indicator release → sector rotation
- On-chain whale movement → price prediction

### prediction/
Statistical and ML-based forecasting:
- Time-series models (ARIMA, Prophet)
- Regime detection (HMM)
- Ensemble scoring for directional bias

## Portfolio Management

### tracker/
- Track NAV for mutual funds (eMAXIS Slim S&P500, iFreeNEXT FANG+, Semiconductor Index, Gold Fund)
- Crypto portfolio valuation (BTC, WLD)
- Unified dashboard with P&L

### rebalance/
- Target allocation monitoring
- Drift alerts when allocation exceeds threshold
- Suggested rebalance trades

### paper-trade/
- **Alpaca Paper Trading API** for US stocks
- Strategy backtesting and forward testing
- Performance tracking and trade journaling

## Trust Layer

The bridge between SENTINEL (financial) and Katala (social).

### world-id/
- World ID API integration for identity verification
- Proof of Personhood checks on social signal sources
- Bot vs. human classification for market-moving accounts

### personhood/
- Verify that influencers driving market sentiment are real humans
- "Influencer PER" — applying financial valuation logic to social influence
- Trust score computation

### platform-audit/
- Cross-reference platform-reported metrics (followers, engagement) with independent data
- Detect inflated numbers and fake engagement
- Open-source verification as antidote to platform opacity

## Delivery

### discord/
- Channel-based delivery (one channel per signal category)
- Rich embeds with charts and summaries
- Interactive commands for on-demand queries

### alerts/
- Real-time anomaly notifications
- Configurable thresholds per signal type
- Priority levels (info, warning, critical)

### reports/
- **Weekly digest**: Market summary, portfolio performance, top anomalies
- **Monthly report**: Macro outlook, correlation shifts, prediction accuracy review

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Data Store | SQLite (dev) → PostgreSQL (prod) |
| Task Queue | APScheduler → Celery (prod) |
| API Framework | FastAPI |
| Charting | Plotly / Matplotlib |
| ML | scikit-learn, statsmodels, Prophet |
| Delivery | discord.py |
| Paper Trading | Alpaca Trade API |
| Identity | World ID API (Worldcoin) |
