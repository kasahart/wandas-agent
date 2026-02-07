---
# Wandas: Workflows & Examples

このファイルには、`wandas` を使った典型的な解析ワークフローをいくつかまとめています。コード生成やクイックスタートの参考として利用してください。

## Example 1 — Basic Audio Analysis
WAV ファイルを読み込み、波形の確認 → 前処理 → FFT → スペクトル表示 を行う基本フロー。

```python
import wandas as wd
import matplotlib.pyplot as plt

# 1. データの読み込み
signal = wd.read_wav("input_audio.wav")

# 2. 統計情報の確認
signal.describe()

# 3. 前処理と FFT（メソッドチェイン）
(
    signal
    .normalize()                   # 正規化
    .low_pass_filter(cutoff=1000)  # 1 kHz 以上をカット
    .fft()                         # FFT 変換
    .plot(title="Processed Signal Spectrum")
)

plt.show()
```

## Example 2 — Spectrogram for Anomaly Detection (Time–Frequency)
センサーデータなどの時変信号から異常（非定常成分）を検出するためのスペクトログラム解析例。

```python
import wandas as wd

# CSV データの読み込み（Time 列を指定）
raw_data = wd.read_csv("sensor_log.csv", time_column="Time")

# 高速フーリエ変換のための前処理（低周波ノイズ除去）
spectrogram = (
    raw_data
    .high_pass_filter(cutoff=50)  # 電源ノイズ等の低周波を除去
    .stft(n_fft=2048, hop_length=512, window='hann')
)

# 可視化
spectrogram.plot(cmap='inferno', title="Anomaly Detection Spectrogram")
```

## Example 3 — Compare Filter Effects
フィルタ適用前後のスペクトルを比較する例。複数のプロセスを比較する際に有用です。

```python
import wandas as wd
import matplotlib.pyplot as plt

original = wd.read_wav("noisy_machine.wav")
filtered = original.band_pass_filter(low=100, high=2000)

ax = original.fft().plot(label="Original")
filtered.fft().plot(ax=ax, label="Filtered", title="Filter Effect Comparison")

plt.legend()
plt.show()
```

---

Tips:
- 出力や可視化のスタイルは `plot()` の引数で指定できます（`cmap`, `title`, `ax` など）。
- 大きなデータは `stft()` の `n_fft` や `hop_length` を調整してメモリと解像度のトレードオフを行ってください。
