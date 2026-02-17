# Roadmap

## Phase 1: Foundation (Weeks 1–4)

**Goal:** Core data pipeline and basic monitoring

- [ ] Project scaffolding (Python package structure, CI/CD)
- [ ] FRED API integration (Fed Funds Rate, CPI, PCE, M2, GDP, Employment)
- [ ] CoinGecko API integration (BTC, WLD price tracking)
- [ ] Yahoo Finance integration (S&P 500, FANG+, Semiconductor watchlist)
- [ ] SQLite data store with schema design
- [ ] Basic Discord bot with daily summary delivery
- [ ] WLD price monitoring cron job
- [ ] Configuration via `.env` and YAML watchlist files

**Key Milestone:** Daily automated market summary delivered to Discord

## Phase 2: Analysis Engine (Weeks 5–10)

**Goal:** Scoring, anomaly detection, and cross-signal analysis

- [ ] 0–100 normalized scoring system for all indicators
- [ ] Volume anomaly detection (statistical z-score based)
- [ ] Sentiment analysis pipeline (X API integration for key persons)
- [ ] RSS news aggregation (Google News, SEC EDGAR)
- [ ] Correlation engine (political speech → market reaction lag analysis)
- [ ] Bitflyer API integration for BTC/JPY real-time data
- [ ] Interactive Discord commands (`/score`, `/watchlist`, `/anomaly`)
- [ ] Alerting system with configurable thresholds

**Key Milestone:** Real-time anomaly alerts with cross-signal context

## Phase 3: Portfolio & Trading (Weeks 11–16)

**Goal:** Portfolio tracking and paper trading

- [ ] Portfolio tracker (mutual funds NAV + crypto positions)
- [ ] Alpaca Paper Trading API integration
- [ ] Backtesting framework for trading strategies
- [ ] Rebalance alert system (target allocation drift monitoring)
- [ ] On-chain data integration (BTC whale tracking, WLD metrics)
- [ ] Weekly/monthly report generation (PDF + Discord embed)
- [ ] Performance dashboard (web UI via FastAPI + Plotly)
- [ ] Japanese equity data integration (TSE stocks)

**Key Milestone:** Paper trading with strategy backtesting and portfolio dashboard

## Phase 4: Trust Layer & Scale (Weeks 17–24)

**Goal:** Katala bridge, World ID integration, and production readiness

- [ ] World ID API integration for Proof of Personhood
- [ ] Katala bridge — connect social signal verification with market anomalies
- [ ] Market manipulation detection (SNS hype × volume anomaly matching)
- [ ] "Influencer PER" scoring model
- [ ] Platform metrics audit system (cross-reference reported vs. real engagement)
- [ ] PostgreSQL migration for production scale
- [ ] Celery task queue for distributed processing
- [ ] API documentation and developer onboarding guide
- [ ] Comprehensive test suite (>80% coverage)
- [ ] Public launch and community building

**Key Milestone:** Full SENTINEL + Katala integration with World ID trust verification

## Beyond Phase 4

- Multi-language support (Japanese, English, Spanish, French)
- Mobile app / PWA
- Plugin architecture for community-contributed data sources
- Decentralized hosting options
- Academic partnerships for financial research
- Integration with additional Proof of Personhood protocols
