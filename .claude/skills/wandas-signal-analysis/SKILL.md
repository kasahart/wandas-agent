---
name: wandas-signal-analysis-helper
description: wandas を使用して時系列信号解析（読み込み・前処理・スペクトル解析）を行う際に使用します。ユーザーが wandas の機能について質問したり、コード生成を求めた場合に適しています。
---

# Wandas Signal Analysis Skill

## Overview
このスキルはカスタムライブラリ `wandas` を使った時系列信号解析の支援を目的としています。
主に以下のタスクで利用します：読み込み（WAV/CSV）、前処理（フィルタ・ノイズ除去）、周波数解析（FFT/STFT）、および可視化。

## Quick Start
以下は最小の初期化と基本的な利用パターンの例です。エージェントがデータを理解する目的で `scripts/basic_loading.py` を併用することを推奨します。

```python
import wandas as wd

# WAV読み込みの例
sig = wd.read_wav("path/to/file.wav")

# CSV読み込み（Time列がある場合）
df = wd.read_csv("path/to/data.csv", time_column="Time")

# メソッドチェインで前処理→解析→プロット
(
    sig
    .normalize()
    .high_pass_filter(cutoff=50)
    .stft(n_fft=2048, hop_length=512)
    .plot(title="Spectrogram")
)
```

## Documentation Map (Resource Navigation)
必要な詳細は下記の各ファイルを参照してください。まずはタスクに関連するファイルだけを開く「段階的開示」を推奨します。

- **基本機能・主要API**:
  - [references/core_api.md](references/core_api.md): 主要クラス、基本的なメソッドの説明
- **高度な機能・設定**:
  - [references/analysis.md](references/analysis.md): FFT/STFT、パラメータ設定、可視化オプション
- **ユースケース・チュートリアル**:
  - [examples/workflows.md](examples/workflows.md): Notebook／スクリプトから抽出した典型的な処理フロー
- **トラブルシューティング**:
  - [references/analysis.md](references/analysis.md): よくあるエラーと対処（該当箇所を参照）

## Usage Guidelines
コードを生成・実行する際の注意点:

1. **実行環境**: エージェント実行時に `wandas` がインストールされていることを前提とします。スクリプト `scripts/basic_loading.py` は環境チェックの例です。
2. **例外処理**: ファイル読み込みや解析時に失敗する可能性があるため `try/except` を用いて `Exception` を適切に捕捉してください。
3. **データ形式**: CSV を扱う際は時刻列（`Time`）の存在とフォーマットを確認してください。時刻列がない場合はサンプリングレートを明示する必要があります。

## Examples
以下はユーザー要求とそれに対する模範的な応答（コード）例です。

**User**: "WAV を読み込んでノイズ除去した後にスペクトログラムを作りたい"

**Model**:
```python
import wandas as wd

sig = wd.read_wav("recording.wav")

processed = (
    sig
    .normalize()
    .band_pass_filter(low=100, high=5000)
    .stft(n_fft=2048, hop_length=256)
)

processed.plot(cmap='magma', title='Processed Spectrogram')
```

**User**: "CSV のセンサーデータを読み込んで異常検知向けに前処理したい"

**Model**:
```python
import wandas as wd

df = wd.read_csv("sensor.csv", time_column="Time")

df = (
    df
    .resample("100ms")
    .interpolate(method='linear')
    .high_pass_filter(cutoff=50)
)

spec = df.stft(n_fft=1024, hop_length=256)
spec.plot(title='Sensor Spectrogram')
```

---

## References
- スニペットやユーティリティ: `scripts/basic_loading.py` を先に実行してデータ概要を取得してください。


