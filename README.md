# SENTINEL v2

**The Trust Visualization Infrastructure for Global Financial Markets**

> Making the invisible visible — monitoring markets, detecting anomalies, and building trust through open-source intelligence.

## What is SENTINEL?

SENTINEL is an open-source market intelligence platform that serves as the **nervous system of financial markets**. It collects, analyzes, and visualizes data across stocks, crypto, commodities, macroeconomic indicators, and social sentiment — providing a unified dashboard for understanding what's really happening in the global economy.

### Core Philosophy

The global derivatives market exceeds **$600 trillion** while world GDP sits at roughly **$100 trillion**. Much of modern finance consists of abstract transactions disconnected from real economic value. SENTINEL exists to **detect, visualize, and make sense of this gap**.

## Key Features

- **Multi-Source Data Pipeline** — Market data, macro indicators, on-chain analytics, news, and social sentiment
- **Anomaly Detection** — Volume spikes, sentiment shifts, and cross-signal correlation
- **Portfolio Tracking** — NAV tracking, rebalance alerts, and paper trading via Alpaca
- **Trust Layer (Katala Integration)** — Connecting financial market intelligence with social media verification
- **World ID Integration** — Proof of Personhood for verifying real human participation vs. bot manipulation
- **Discord Delivery** — Real-time alerts and periodic reports

## Architecture

SENTINEL connects two nervous systems:

| Layer | Role | Project |
|-------|------|---------|
| Financial Markets | Price, volume, macro, on-chain | **SENTINEL** |
| Social Markets | Influence, sentiment, authenticity | **Katala** |

Bridging these through **World ID's Proof of Personhood** creates a unified trust infrastructure — verifying that market-moving social signals come from real humans, not bots or coordinated manipulation.

## Why Open Source?

We believe market intelligence infrastructure should be:

1. **Transparent** — No black boxes. Every algorithm is auditable.
2. **Accessible** — Not locked behind Bloomberg terminals and hedge fund walls.
3. **Global** — Built for everyone, not just Wall Street.
4. **Trust-verified** — Integrating Proof of Personhood to ensure data integrity.

**SENTINEL aims to become foundational infrastructure for the world** — the open-source alternative to proprietary financial intelligence platforms.

## Quick Start

```bash
# Clone
git clone https://github.com/Nicolas0315/SENTINEL-v2.git
cd SENTINEL-v2

# Setup (coming soon)
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python -m sentinel.main
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Vision](docs/VISION.md)
- [Watchlist](docs/WATCHLIST.md)
- [Roadmap](docs/ROADMAP.md)
- [Legal Guidelines](docs/LEGAL.md)

## Contributing

Contributions welcome! Please read our contributing guidelines (coming soon) and open a PR.

## License

[MIT License](LICENSE)

---

## 🇯🇵 日本語セクション

### SENTINELとは

SENTINELは、金融市場のオープンソース・インテリジェンス基盤です。株式、暗号資産、コモディティ、マクロ経済指標、SNSセンチメントを横断的に収集・分析・可視化し、市場で本当に起きていることを理解するための統合ダッシュボードを提供します。

### コンセプト

- **金融市場の神経系（SENTINEL）** × **SNS市場の神経系（Katala）** の接続
- **World ID API** による Proof of Personhood 統合 — ボットや組織的操作ではなく、実在する人間のシグナルを検証
- デリバティブ600兆ドル vs GDP100兆ドルの乖離 — 「意味のないお金のやり取り」を検知・可視化
- 全人類AI投資時代におけるパイプライン構築のゴールデンタイム

### 運用体制

| 役割 | 担当 |
|------|------|
| メイン分析 + 開発 | しろくま (Sirokuma AI) |
| 深堀り調査 | Gemini Deep Research |
| コード実装 | Codex |
| オーケストレーション | Nicolas |
