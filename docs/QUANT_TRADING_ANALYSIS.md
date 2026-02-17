# quant-trading リポジトリ分析レポート

> 分析日: 2026-02-17
> 対象: https://github.com/je-suis-tm/quant-trading
> 目的: SENTINEL v2の予測精度改善（現在16-25%）のための知見抽出

---

## 1. リポジトリ全体像

Robert Mercer の引用から始まる、個人開発者による**クオンツトレーディング戦略集**。テクニカル指標、統計的裁定取引、オプション戦略、クオンタメンタル分析プロジェクトを含む。全戦略がPythonバックテスト付き。フリクションレス（スリッページ・手数料なし）を前提とした歴史的データバックテスト。

## 2. 実装されている戦略一覧

### テクニカル指標系（8戦略）

| # | 戦略 | 種別 | 概要 |
|---|------|------|------|
| 1 | **MACD Oscillator** | モメンタム | 短期/長期SMAクロスオーバー |
| 3 | **Heikin-Ashi Candlestick** | モメンタム | ノイズ除去ローソク足でトレンド検出 |
| 4 | **London Breakout** | ブレイクアウト | 東京市場最終時間の高値/安値を閾値に |
| 5 | **Awesome Oscillator** | モメンタム | High/Lowの平均ベースのMACD改良版（Saucer手法） |
| 7 | **Dual Thrust** | ブレイクアウト | 前日OHLC基準の日中ブレイクアウト |
| 8 | **Parabolic SAR** | トレンド反転 | 再帰計算によるStop & Reverse指標 |
| 9 | **Bollinger Bands Pattern Recognition** | パターン認識 | ボリンジャーバンドでBottom W（ダブルボトム）検出 |
| 10 | **RSI Pattern Recognition** | パターン認識 | RSIにヘッドショルダーパターン検出 |
| 17 | **Shooting Star** | ローソク足パターン | 弱気反転シグナル |

### クオンタメンタル分析（6プロジェクト）

| # | プロジェクト | 手法 |
|---|-------------|------|
| 2 | **Pair Trading** | Engle-Granger共和分検定 → 統計的裁定取引 |
| 6 | **Oil Money** | 原油価格 vs 産油国通貨の因果性検証（Granger因果性） |
| 11 | **Monte Carlo** | Wiener Process仮定での株価シミュレーション |
| 12 | **Options Straddle** | ストラドル戦略のペイオフ分析 |
| 13 | **Portfolio Optimization** | グラフ理論による分散投資（別リポジトリ） |
| 14 | **Smart Farmers** | 凸最適化で農作物市場の需給モデリング |
| 15 | **VIX Calculator** | リーマン和+テイラー展開でカスタムVIX算出 |
| 16 | **Wisdom of Crowds** | Dawid-Skene/Platt-Burgesアンサンブルで予測集約 |

## 3. バックテスト手法の分析

### 現状のアプローチ
- **構造**: 各戦略が独立した`.py`ファイル。`main()`関数で呼び出し可能
- **データ取得**: `yfinance` / `fix_yahoo_finance`でYahoo Financeから取得
- **シグナル生成**: `signal_generation(df, method)` パターンで統一
- **評価**: 主にビジュアル（matplotlib）。P&Lプロットと売買ポジション表示
- **弱点**: Sharpe Ratio、最大ドローダウン、勝率等の**定量的評価メトリクスが未実装**

### SENTINEL v2との比較
SENTINELの`predictor.py`はスコアリングシステム（各指標が±1〜2のスコア寄与）で方向を予測。quant-tradingリポジトリは実際の売買シグナル生成に焦点。

## 4. テクニカル指標の使い方

### quant-tradingリポジトリ
- RSI: 標準14期間 + **パターン認識**（ヘッドショルダー）← これが差別化ポイント
- MACD: 標準設定 + **Awesome Oscillator**（Saucer手法でレスポンス改善）
- Bollinger Bands: 標準20期間 + **Bottom Wパターン検出**（算術的アプローチ）
- Parabolic SAR: 再帰計算による精密な実装
- Heikin-Ashi: ノイズフィルタリング

### SENTINEL v2の現状
- RSI: 30/70閾値のみ
- MACD: ラインクロスとヒストグラム方向のみ
- Bollinger: 上限/下限タッチのみ
- **パターン認識なし** ← 最大の改善余地

## 5. リスク管理手法

### quant-tradingリポジトリ
- London Breakout: **ストップロス/ストッププロフィット**を明示的に設定
- Dual Thrust: 日中ポジション反転 + 日末全クリア
- Options Straddle: ストライク価格最適化による損失帯域縮小
- VIX Calculator: ボラティリティ予測ツール
- Pair Trading: 共和分ステータスの**定期チェック**を推奨

### SENTINEL v2の現状
- リスク管理の仕組みが**ほぼ未実装**

## 6. コード品質・構造の評価

### quant-tradingリポジトリ
| 項目 | 評価 | 備考 |
|------|------|------|
| 可読性 | ⭐⭐⭐ | コメント豊富、教育的 |
| モジュール性 | ⭐⭐ | 各ファイル独立だが共通化なし（DRY違反） |
| テスト | ⭐ | テストコードなし |
| 型ヒント | ⭐ | なし |
| エラーハンドリング | ⭐ | 最小限 |
| 再利用性 | ⭐⭐ | `main()`関数で呼び出し可能 |
| 統計手法 | ⭐⭐⭐⭐ | Engle-Granger、Granger因果性、ADF検定等 |

### SENTINEL v2
| 項目 | 評価 | 備考 |
|------|------|------|
| 可読性 | ⭐⭐⭐⭐ | docstring、型ヒント完備 |
| モジュール性 | ⭐⭐⭐⭐ | パッケージ構造、関心の分離 |
| テスト | ⭐⭐ | 基本的なバックテストあり |
| 統計手法 | ⭐⭐ | 線形スコアリングのみ |

## 7. SENTINEL v2への具体的改善提案

### 🔴 Priority 1: パターン認識の導入（最大インパクト）

現在のSENTINELは単純な閾値ベース。quant-tradingのBollinger Bands Bottom W検出とRSI Head-Shoulder検出のロジックを移植すべき。

**具体的アクション:**
```python
# src/analysis/patterns.py を新規作成
def detect_double_bottom(close: pd.Series, bb_lower: pd.Series) -> bool:
    """Bollinger Bands Pattern Recognition backtest.pyの
    signal_generation()ロジックを移植"""

def detect_head_shoulder(rsi: pd.Series) -> bool:
    """RSI Pattern Recognition backtest.pyの
    パターン検出ロジックを移植"""
```

### 🔴 Priority 2: 共和分ベースのクロスアセット分析

Pair Tradingの`EG_method()`（Engle-Granger共和分検定）をSENTINELに導入。関連銘柄間の乖離を予測シグナルに活用。

**具体的アクション:**
- `statsmodels`のADF検定・VECM活用
- ウォッチリスト内のペア相関/共和分を定期監視
- 乖離度をスコアリングに追加（スプレッドが2σ超えたらリバーサル予測）

### 🟡 Priority 3: Awesome Oscillator（Saucer手法）の追加

現在のMACDシグナルを補完。High/Lowの平均ベースで計算し、Saucer手法でより早いレスポンスを得る。

**具体的アクション:**
```python
# src/analysis/technical.py に追加
def calc_awesome_oscillator(high: pd.Series, low: pd.Series,
                             fast: int = 5, slow: int = 34) -> pd.Series:
    midpoint = (high + low) / 2
    ao = midpoint.rolling(fast).mean() - midpoint.rolling(slow).mean()
    return ao

def detect_saucer(ao: pd.Series) -> int:
    """AO Saucer detection: +1=bullish, -1=bearish, 0=neutral"""
```

### 🟡 Priority 4: Heikin-Ashi変換によるノイズ除去

生のOHLCをHeikin-Ashi変換してからシグナル生成することで、横ばい市場でのダマシを減らせる。

### 🟢 Priority 5: VIXスタイルのボラティリティ指標

VIX Calculatorの手法を簡略化し、暗号通貨オプション市場のインプライドボラティリティを予測シグナルに組み込む。

### 🟢 Priority 6: Monte Carloシミュレーションによる信頼区間

予測に確率分布を導入。「UP/DOWN/FLAT」の単純分類ではなく、Monte Carloで価格レンジの確率分布を提示。

## 8. スコアリング改善の具体案

現在のSENTINEL predictor.pyは**線形スコア加算**（各指標±1〜2）で最大±10程度。

### 改善後のスコアリング構造:

```python
score = 0.0

# 既存（維持）
score += rsi_score       # -2 to +2
score += macd_score      # -2 to +2
score += bollinger_score # -2 to +2
score += ma_score        # -2 to +2

# 新規追加（quant-tradingから移植）
score += pattern_score   # -3 to +3 (Bottom W, Head-Shoulder等)
score += ao_saucer_score # -1 to +1 (Awesome Oscillator Saucer)
score += sar_score       # -1 to +1 (Parabolic SAR方向)
score += pair_zscore     # -2 to +2 (共和分ペアの乖離度)
```

**期待効果**: パターン認識の追加により、横ばい市場での誤シグナルが減少。共和分分析により、個別銘柄だけでなく市場構造の歪みも捕捉可能。予測精度16-25% → **30-40%**への改善を目標とする。

## 9. 実装ロードマップ

| Phase | 内容 | 期間 | 期待精度 |
|-------|------|------|----------|
| 1 | パターン認識（BB Bottom W + RSI H&S）移植 | 1週間 | 25-30% |
| 2 | Awesome Oscillator + Parabolic SAR追加 | 3日 | 28-33% |
| 3 | Pair Trading共和分分析導入 | 1週間 | 30-38% |
| 4 | Heikin-Ashi前処理 + Monte Carlo信頼区間 | 1週間 | 33-40% |

## 10. まとめ

quant-tradingリポジトリは**教育的な戦略集**として優秀。特にSENTINEL v2にとって価値が高いのは:

1. **パターン認識のアルゴリズム的アプローチ**（ML不要で高速）
2. **共和分検定による統計的裁定**の考え方
3. **Awesome Oscillator Saucer**によるMACDの補完
4. **Parabolic SAR**によるトレンド反転検出

コード品質はSENTINELの方が上（型ヒント、モジュール構造）だが、**戦略の深さと多様性**ではquant-tradingが圧倒的。ロジックを移植する際はSENTINELの既存コードスタイルに合わせてリファクタリングすること。
