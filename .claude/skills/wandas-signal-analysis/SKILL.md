---
name: wandas-signal-analysis

description: wandas を用いた時系列信号（音声・振動など）の解析スキル。フレーム中心APIとメソッドチェーンで安全かつ再現性のある解析コードを生成します。
---

# Wandas Signal Analysis Skill

このスキルは、独自の信号処理ライブラリ wandas を使用して、時系列データ（音声、振動など）の解析タスクを実行する際に使用します。
wandas は matplotlib と統合されており、メソッドチェーン記法によって直感的かつ可読性の高い信号処理パイプラインを構築できます。

## 利用判断基準 (When to use)

ユーザーが以下のタスクを要求した場合にこのスキルを有効化してください：

- 音声ファイル（WAV）やセンサーデータ（CSV）の読み込みと解析
- ノイズ除去（ローパス、ハイパス、バンドパスフィルタ）
- 周波数解析（FFT、STFT、N-オクターブ解析）
- 信号の統計量算出（RMS、クレストファクター、歪度、尖度）
- データの可視化（波形、スペクトログラム、スペクトル）


必須ルール（必読）

- **Wandas-first**: 直接の `numpy`/`scipy` 実装は禁止。必ず `wandas` のメソッドを使うこと。
- **可視化**: 直接の `matplotlib` 描画は禁止。チェーンの最後に `.plot()` を使うこと。
- **メソッドチェーン**: 処理はメソッドチェーンで記述し、`operation_history` を残すこと。
- **ドキュメント遵守**: 解析前に `docs/guidelines.md` を確認すること。

## 重要な原則 (Core Principles)

- **Wandasファースト**: 直接の `scipy`/`numpy` 実装は避け、wandas のメソッドを使ってください。
- **メソッドチェーン**: 処理はメソッドチェーンで記述し、可読性と一貫性を確保してください。
- **ガードレール遵守**: 解析前に `docs/guidelines.md` を確認し、規則を守ってください。


## 基本的なワークフロー

1. セットアップ: `import wandas as wd`
2. 読み込み: `wd.read_wav()` や `wd.read_csv(..., time_column=...)` で `ChannelFrame` を取得
3. 前処理: `.low_pass_filter()`, `.normalize()` などをチェーンで適用
4. 解析・可視化: `.fft()`, `.stft()`, `.describe()` を用い、最後に `.plot()` を呼ぶ


## Design
wandas は Frame-Centric で、すべてのデータは `Frame` オブジェクトにカプセル化されます。型注釈とメソッドチェーンを前提にコード生成してください。

## Quick Start
以下は最小の初期化と基本的な利用パターンの例です。エージェントがデータを理解する目的で `scripts/basic_loading.py` を併用することを推奨します。

```python
import wandas as wd

# WAV読み込みの例
sig = wd.read_wav("path/to/file.wav")

# メソッドチェインで前処理→解析→プロット
# describeメソッドによって、時系列信号、パワースペクトル、スペクトログラム、Audioコントロールが表示される。
(
    sig
    .normalize()
    .high_pass_filter(cutoff=50)
    .describe()
)

# CSV読み込み（Time列がある場合）
cf = wd.read_csv("path/to/data.csv", time_column="Time")

# numpy配列からChannelFrameを生成
# 音圧データとしてpa単位で初期化する例。単位を指定することで、デシベル計算時にデシベル基準値が加味される。
import numpy as np
fs = 51200  # サンプリング周波数
duration = 10  # 録音時間（秒）
ch_Pa =  wd.from_numpy(
    data=np.random.randn(fs*duration) * 0.1,  # ダミーデータ
    sampling_rate=fs,
    ch_labels=['Location A', 'Location B', 'Location C'],
    ch_units='Pa'
)

```

## Architecture
- Frame-based: データは `ChannelFrame` / `SpectralFrame` 等の `Frame` オブジェクトで管理します。
- 操作はオブジェクトのメソッドで行い、型注釈に従って引数を指定してください（例: `frame.fft()`）。
- 上で述べた **必須ルール** を厳守してください。

## Documentation Map (Resource Navigation)

タスクに応じて、以下の参照ファイルを読み込んでください：

- **基本操作 & クラス構造**: `references/core_api.md` を参照
- **高度な解析 (FFT, STFT)**: `references/analysis.md` を参照
- **実装パターン・コード例**: `examples/workflows.md` を参照

## Utility Scripts

未知のデータファイル（WAV/CSV）が与えられた場合、まずは以下のスクリプトを実行してデータの概要を確認することを推奨します。

```bash
python scripts/basic_loading.py <file_path>
```

## Examples

### WAV を読み込んでノイズ除去した後にスペクトログラムを作りたい

```python
import wandas as wd

sig = wd.read_wav("recording.wav")

processed = (
    sig
    .normalize()
    .band_pass_filter(low_cutoff=100, high_cutoff=5000)
    .stft(n_fft=2048, hop_length=256)
)

processed.plot(cmap='magma', title='Processed Spectrogram')
```

### CSV のセンサーデータを読み込んで異常検知向けに前処理したい

```python
import wandas as wd

df = wd.read_csv("sensor.csv", time_column="Time")

df = (
    df
    .resample(target_sr=8000)
    .interpolate(method='linear')
    .high_pass_filter(cutoff=50)
)

spec = df.stft(n_fft=1024, hop_length=256)
spec.plot(title='Sensor Spectrogram')
```
