---
# Wandas — Core API Reference

主要な入出力、前処理、解析、可視化メソッドの概要と簡単な使用例を示します。詳細なパラメータは `references/analysis.md` の該当セクションを参照してください。

## 1. Import

```python
import wandas as wd
```

## 2. Input / Output (I/O)

- `read_wav(path: str) -> ChannelFrame`
  - WAV ファイルを読み込みます。

- `read_csv(path: str, time_column: str = None, sr: int = None) -> ChannelFrame`
  - CSV を読み込みます。`time_column` 指定で時刻列を用いてサンプリングレートを推定できます。`sr` で明示的に指定可能。

- `generate_sin(freqs: list, duration: float, sampling_rate: int) -> ChannelFrame`
  - テスト用の正弦波を生成します。

## 3. Signal Processing (Filtering & Resampling)

これらは `ChannelFrame` に対して呼び出せます。すべてメソッドチェイン可能です。

- `low_pass_filter(cutoff: float, order: int = 4)`
- `high_pass_filter(cutoff: float, order: int = 4)`
- `band_pass_filter(low: float, high: float, order: int = 4)`
- `resample(target_rate: int)`
- `normalize()`

例:

```python
sig = wd.read_wav('input.wav')
sig_filtered = sig.high_pass_filter(20).normalize()
```

## 4. Analysis (FFT / STFT)

- `fft(n_fft: int = None, window: str = 'hann') -> SpectralFrame`
- `psd(n_fft: int = None, window: str = 'hann') -> SpectralFrame`
- `stft(n_fft: int = 2048, hop_length: int = 512, window: str = 'hann') -> SpectrogramFrame`

（パラメータの詳細は `references/analysis.md` を参照）

## 5. Visualization & Inspection

- `plot(title: str = None, **kwargs)` — フレームの可視化。Matplotlib の `Axes` を返します。
- `describe()` — 統計情報（平均、RMS、最大/最小など）とメタデータを表示します。

## 6. Notes & Best Practices

- メソッドは非破壊的に新しいフレームを返すため、比較が容易です（例: フィルタ前後を別変数で保持）。
- 大きなデータを扱う場合はリサンプリングや `n_fft`/`hop_length` の調整で計算量を制御してください。

- 演算子の順序について: `ChannelFrame` は `frame * scalar` や `frame + other_frame` のように左オペランドがフレームになるケースをサポートします。`scalar * frame` のようにスカラーを左に置くと Python 側でスカラーの乗算が優先され `TypeError` になることがあるため、スケーリングは `frame * 0.5` のようにフレーム側を左にしてください。

 例:

```python
sig_main = wd.generate_sin([1000.0], duration=2.0, sampling_rate=10000)
sig_noise = wd.generate_sin([50.0], duration=2.0, sampling_rate=10000)
# 正しい: ChannelFrame * scalar
sig = sig_main + (sig_noise * 0.5)
# 間違い（TypeError を起こす可能性あり）
# sig = sig_main + 0.5 * sig_noise
```
