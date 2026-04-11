# wandas Skills Renewal & wandas-analyst Agent Design

**Date:** 2026-04-11  
**Status:** Approved

---

## 目的

wandas ライブラリを使った信号解析・レポーティングのための Claude Code スキル群を刷新する。
既存の単一スキル `wandas-signal-analysis` を廃止し、専門スキル4本＋オーケストレーター兼エージェントスキル1本の 5スキル構成に移行する。

---

## 背景・課題

| 現状 | 問題 |
|------|------|
| `.claude/skills/wandas-signal-analysis/` | 肥大化・役割が混在 |
| `wandas/.claude/skills/` に4スキルあるが未統合 | プロジェクト側で使えない |
| Dask/NumPy の挙動記述が2箇所で食い違う | 誤ったコードが生成される |
| 固定テンプレート解析 | 目的に応じた柔軟な解析ができない |

---

## アーキテクチャ

### スキル構成（5本）

```
.claude/skills/
  wandas-getting-started/       ← wandas サブモジュールから移行・更新
  wandas-signal-processing/     ← 同上
  wandas-spectral-analysis/     ← 同上
  wandas-visualization/         ← 同上
  wandas-analyst/               ← 新規作成（オーケストレーター＋エージェント）

# 廃止
  wandas-signal-analysis/       ← 削除
```

### 責任分担

| スキル | 役割 |
|--------|------|
| `wandas-getting-started` | データ読み込み・フレーム型の理解・I/O |
| `wandas-signal-processing` | フィルタリング・前処理・正規化 |
| `wandas-spectral-analysis` | FFT/STFT/Welch/コヒーレンス/伝達関数 |
| `wandas-visualization` | `.plot()` / `.describe()` / オーバーレイ |
| `wandas-analyst` | 実験計画・適応型解析・Notebook生成・条件比較・考察 |

---

## 各スキルのファイル構成

### 専門スキル（4本共通）

```
<skill-name>/
  SKILL.md                      ← 必須（フロントマター + API + パターン）
  examples/
    workflows.md                ← コピペで動くコードスニペット集
  references/
    <topic>_api.md              ← メソッドシグネチャ詳細（辞書的参照）
```

### wandas-analyst

```
wandas-analyst/
  SKILL.md                      ← オーケストレーションプロトコル
  examples/
    workflows.md                ← 解析シナリオ例（ノイズ評価・異常検知など）
  templates/
    analysis_report.ipynb       ← Notebook テンプレート
  references/
    notebook_structure.md       ← セクション構成・Markdownセルの書き方
    subagent_protocol.md        ← サブエージェントの役割・呼び出し方
```

---

## wandas-analyst: 適応型解析プロトコル

### コア思想

従来の固定テンプレート実行ではなく、発見駆動の調査サイクルを採用する。

```
固定フロー（旧）: 目的 → テンプレート実行 → レポート
適応型（新）:     目的 → 仮説 → 最小解析 → 発見 → 再仮説 → … → 統合
```

### サブエージェント構成

```
Orchestrator（wandas-analyst メインスキル）
  - 解析目的・仮説を常に保持（北極星）
  - 調査ラウンドの計画・管理
  - 各サブエージェントへの「問い」を発行
  - 収束判断・最終統合

  ├─ Diagnostician（セッション冒頭に1回）
  │    入力: ファイルパス群
  │    出力: 信号品質・特徴量・推奨解析リスト
  │    確認: クリッピング / DC オフセット / ノイズフロア / sr / ch 数
  │
  ├─ Analysis Agent（調査ラウンドごとに呼び出し）
  │    ※ 1種類のエージェント。ラウンドごとに「解析種別」を引数として渡す。
  │    入力: 今回の問い + 解析種別 + 最小限のコンテキスト（前ラウンド発見サマリー）
  │    出力: 解析コード + 発見 + 次への示唆
  │    解析種別（Orchestrator がラウンドごとに選択）:
  │      - temporal    : 時間波形・RMS トレンド
  │      - spectral    : FFT / Welch / 1/3オクターブ
  │      - level       : 音圧評価・dB(A)・統計量
  │      - stft        : 時間-周波数・異常検知
  │      - coherence   : コヒーレンス・伝達関数（多ch 時）
  │      - psycho      : ラウドネス・ラフネス・シャープネス
  │      - comparison  : 条件間差分・比率・統計比較
  │
  └─ Synthesis Agent（全ラウンド完了後に1回）
       入力: 初期目的 + 全ラウンド発見サマリーのみ（生解析データは渡さない）
       出力: 仮説検証・結論・次のステップ・未解決の問い
```

### 各ラウンド後の収束判断（Orchestrator が自問）

```
1. この発見は仮説を支持するか、否定するか、新たな疑問を生むか？
2. 次に見るべき指標・時間帯・周波数帯はあるか？
3. これ以上掘り下げても解析目的に対して価値があるか？
```

### サブエージェントが確証バイアスを防ぐ理由

| 問題 | 解決策 |
|------|--------|
| 目的を見失う | Orchestrator が毎ラウンド目的を参照 |
| 確証バイアス | Synthesis Agent は生データを見ずに結論を書く |
| 浅い専門分析 | Analysis Agent は1つの問いだけに集中 |
| 考察の一貫性 | Synthesis が全発見を横断して矛盾を発見 |

---

## Notebook テンプレート構成

固定フレーム（調査設計・統合考察）＋適応ループ（発見次第で増減）。

```
[固定] Section 0: 調査設計
  [Markdown] 問い（What are we trying to understand?）
  [Markdown] 初期仮説（Before looking at data）
  [Code]     データ読み込み・条件定義
  [Code]     Diagnostician の結果（信号診断）

[適応ループ] Investigation Round N:
  [Markdown] ## Round N: ＜今回調べること＞
             - 動機: 前ラウンドの発見 or 初期仮説から
             - 問い: このラウンドで答えたいこと
  [Code]     解析コード（目的に直結した最小限）
  [Code]     数値サマリー
  [Markdown] ### Findings
             - 観察: グラフ・数値から読めること
             - 解釈: なぜそうなっているか
             - 示唆: 次のラウンドへの方向性

[固定] Section Final: 統合・考察
  [Markdown] 仮説検証（初期仮説との照合）
  [Code]     全指標サマリーテーブル・条件間比較
  [Markdown] 結論・示唆・次のステップ・未解決の問い
```

---

## 専門スキルの更新方針

### API 整合性の修正

- **最優先:** `wandas/wandas/` ソースを Grep/Read して引数名・デフォルト値を再確認
- **Dask/NumPy 問題:** ソースの実装を確認して一方に統一（記述の食い違いを解消）
- **引数名の誤記:** `band_pass_filter` は `low_cutoff`/`high_cutoff`（`low`/`high` ではない）等を Common Mistakes に明記

### SKILL.md フォーマット規約（CLAUDE.md 準拠）

1. フロントマター（`name:` / `description:`）
2. 必須ルール（Wandas-first / メソッドチェーン / `.plot()` 使用）
3. API サマリーテーブル
4. Patterns（コピペ動作するスニペット）
5. Common Mistakes
6. Documentation Map（examples/ と references/ へのリンク）

---

## 実装スコープ

### Phase 1: 専門スキル移行・更新（4本）

1. `wandas-getting-started` — サブモジュールから移行、examples/ + references/ 追加
2. `wandas-signal-processing` — 同上
3. `wandas-spectral-analysis` — 同上
4. `wandas-visualization` — 同上
5. `wandas-signal-analysis` を削除

### Phase 2: wandas-analyst 新規作成

1. `SKILL.md` — オーケストレーションプロトコル・サブエージェント呼び出し手順
2. `examples/workflows.md` — 典型シナリオ（ノイズ評価・異常検知・条件比較）
3. `templates/analysis_report.ipynb` — 適応型 Notebook テンプレート
4. `references/notebook_structure.md` — セクション構成ガイド
5. `references/subagent_protocol.md` — サブエージェントへの問い・コンテキストの渡し方

---

## 成功基準

- [ ] WAV ファイルを渡すだけで調査設計から考察まで Notebook が生成される
- [ ] 解析目的が変わっても固定テンプレートに縛られない
- [ ] Synthesis Agent が生データを見ずに結論を書き、確証バイアスが防がれる
- [ ] 各専門スキルの API 記述がソースと一致している
- [ ] `wandas-analyst` が他専門スキルを参照指示として明記している
