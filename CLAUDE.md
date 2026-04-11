# wandas-agent — Skills Development Guide

## このリポジトリの目的
wandas（音声・振動信号処理ライブラリ）の Claude Code スキルを開発・管理する。
スキルは `.claude/skills/<name>/` に置かれ、ユーザーが wandas を使う際に Claude が自動的に参照する。

## リポジトリ構造
```
wandas/              ← wandas 本体（git submodule）★APIの根拠はここ
.claude/skills/
  wandas-getting-started/   ← I/O・フレーム型・物理単位
  wandas-signal-processing/ ← フィルタ・音圧・心理音響
  wandas-spectral-analysis/ ← FFT/STFT/Welch/コヒーレンス
  wandas-visualization/     ← .plot() / .describe()
  wandas-analyst/           ← 適応型解析・Notebookレポート生成（オーケストレーター）
```

> **注意**: `.claude/skills/` のスキルは `wandas/.claude/skills/` より優先される。
> 同名スキルがある場合、プロジェクトルートのものを使用する。

## スキルのファイル構成
```
<skill-name>/
  SKILL.md              ← メイン（必須）
  examples/
    workflows.md        ← 実装パターン集
  references/
    <topic>_api.md      ← API 詳細リファレンス
  scripts/
    <name>.py           ← エージェント実行用スクリプト（任意）
```

## SKILL.md の必須セクション（順序を守る）
1. **フロントマター** — `name:` と `description:`
   - `description` はスキル起動トリガーになる。ユーザーの具体的な操作を列挙する。
2. **必須ルール** — 下記3つを必ず記載する
   - Wandas-first: `scipy`/`numpy` 直接実装禁止
   - メソッドチェーン: 処理はチェーンで記述
   - 可視化: `matplotlib` 直接描画禁止、`.plot()` / `.describe()` を使う
3. **API サマリーテーブル** — メソッド名・引数・返り値・効果
4. **Patterns** — コピペで動くコードスニペット
5. **Common Mistakes** — 引数名の間違いなど実際に起きやすいもの
6. **Documentation Map** — `examples/` と `references/` へのリンク

## 開発の鉄則

### API は必ずソースから確認する
```
wandas/wandas/        ← Python ソース（Grep/Read で調べる）
```
引数名・デフォルト値・返り値を想定で書かない。
例: `band_pass_filter` の引数は `low_cutoff` / `high_cutoff`（`low`/`high` ではない）。

### フォーマットの一貫性
既存スキル（`wandas-getting-started` など）のスタイルに合わせる。
テーブル形式・コードブロックの書き方を参照すること。

### examples/ と references/ の役割分担
- `examples/workflows.md`: ユーザーの典型的なタスクをそのまま解決できるコード
- `references/<topic>_api.md`: メソッドのシグネチャと詳細説明（辞書的に使う）
```

