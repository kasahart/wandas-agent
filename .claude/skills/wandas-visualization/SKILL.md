---
name: wandas-visualization
description: Use when plotting Wandas 0.7.2 waveform, spectral, spectrogram, fractional-octave, cepstral, cepstrogram, roughness, coherence, cross-spectral, or transfer-function results; overlaying Frames; building typed pair matrices; or exporting ChannelFrame.describe() figures.
---

# Wandas: Visualization

Frame が持つ semantic axes と quantity-specific view を使って可視化する。plot は明示的な compute boundary。

## Mandatory Rules

1. **Wandas-first**: `.plot()`, `.plot_matrix()`, `.describe()` を使い、`plt.plot(frame.data)` や `imshow(frame.data)` で Frame の意味を捨てない。
2. **Typed view**: pairwise result は具象型に対応する `view=` を選ぶ。label/history から quantity を推測しない。
3. **Axes passing**: 別 Frame を重ねる場合は、最初の `.plot()` が返した `ax` を次の `.plot(ax=ax, ...)` へ渡す。
4. **Handle multi-channel returns**: multi-channel plot は `Iterator[Axes]` を返す場合がある。単一 Axes が必要なら先に channel/pair を選択する。

## Plot API by Frame Type

| Frame | API | 主な controls |
|---|---|---|
| `ChannelFrame` | `.plot(plot_type="waveform", ax=None, title=None, overlay=False, alpha=1.0, xlim=None, ylim=None)` | waveform |
| `ChannelFrame` | `.rms_plot(ax=None, title=None, overlay=True, Aw=False)` | RMS trend |
| `ChannelFrame` | `.describe(...)` | waveform + Welch amplitude + STFT summary |
| `SpectralFrame` | `.plot(plot_type="frequency", ..., overlay=False, Aw=False, xlim=None, ylim=None)` | amplitude level/frequency |
| `SpectrogramFrame` | `.plot(plot_type="spectrogram", ..., cmap="jet", fmin=0, fmax=None, vmin=None, vmax=None, Aw=False)` | time-frequency |
| `NOctFrame` | `.plot(plot_type="noct", ..., overlay=False, Aw=False)` | fractional-octave bands |
| `CepstralFrame` | `.plot(plot_type="quefrency", ax=None, title=None, xlabel=..., ylabel=..., **line_kwargs)` | real cepstrum |
| `CepstrogramFrame` | `.plot(plot_type="cepstrogram", ..., cmap="RdBu_r", qmin=0, qmax=None, vmin=None, vmax=None)` | time-quefrency |
| `RoughnessFrame` | `.plot(plot_type="heatmap", ..., cmap="viridis", vmin=None, vmax=None)` | Bark-time heatmap |
| typed pairwise Frame | `.plot(..., view=None)` / `.plot_matrix(view=None)` | quantity-specific pair view |

戻り値は通常 `Axes`、multi-channel/pair では `Iterator[Axes]` の場合がある。

## ChannelFrame.describe

```python
figures = signal.describe(
    normalize=True,
    is_close=True,
    fmin=0,
    fmax=None,
    cmap="jet",
    vmin=None,
    vmax=None,
    xlim=None,
    ylim=None,
    Aw=False,
    waveform=None,
    spectral=None,
    image_save=None,
)
```

- 波形、Welch-averaged amplitude、STFT をまとめる。
- `normalize=True` は notebook audio playback 用の正規化で、Frame data を変えない。
- `image_save` で保存し、`is_close=False` で返却 Figure を後処理できる。
- Multi-channel では channel ごとに Figure を作る。

## Pairwise Views

| Frame | `view` values | default |
|---|---|---|
| `CoherenceFrame` | `"coherence"` | coherence |
| `CrossSpectralFrame` | `"magnitude"`, `"phase"`, `"level"` | magnitude |
| `TransferFunctionFrame` | `"gain"`, `"phase"`, `"gain_db"`, `"transfer_level_db"` | gain |

Pairwise Frame で `Aw=True` は未定義。`.plot_matrix()` は typed output-row/input-column に各 pair を配置する。

## Patterns

### Overall signal summary and export

```python
import wandas as wd

signal = wd.read("audio.wav")
signal.describe(
    fmin=20,
    fmax=min(8_000, signal.sampling_rate / 2),
    cmap="inferno",
    vmin=-80,
    vmax=-20,
    image_save="audio-overview.png",
)
```

### Overlay original and filtered spectra

```python
original = wd.read("noisy.wav")
filtered = original.band_pass_filter(low_cutoff=100, high_cutoff=4_000)

ax = original.fft().plot(overlay=True, label="Original", alpha=0.7)
filtered.fft().plot(ax=ax, overlay=True, label="Filtered", title="Filter comparison")
ax.legend()
```

### Cepstral and cepstrogram views

```python
cepstrum = signal.cepstrum(n_fft=2_048)
ax = cepstrum.plot(title="Real cepstrum")
ax.set_xlim(0, 0.02)

cepstrogram = signal.stft(n_fft=2_048, hop_length=256).cepstrum()
cepstrogram.plot(qmin=0, qmax=0.02, cmap="RdBu_r", title="Cepstrogram")
```

### Typed pair matrix

```python
reference = wd.read("reference.wav").rename_channels({0: "reference"})
measurement = wd.read("measurement.wav").rename_channels({0: "measurement"})
combined = reference.concat_frame(measurement)

coherence = combined.coherence(n_fft=2_048)
transfer = combined.transfer_function(n_fft=2_048)

coherence.plot_matrix()
transfer.plot_matrix(view="gain_db")
```

`gain_db` は dimensionless pairs にだけ有効。異なる単位なら `transfer_level_db` を使う。

### Roughness heatmap

```python
roughness = signal.roughness_dw_spec(overlap=0.5)
roughness.plot(
    cmap="viridis",
    title="Specific roughness",
    colorbar_label="Specific Roughness [Asper/Bark]",
)
```

## Common Mistakes

| 間違い | 正解 |
|---|---|
| `plt.plot(frame.data)` | `frame.plot()` を使う |
| 別 Frame に `overlay=True` だけを指定 | 最初の戻り `ax` を次へ渡す |
| `.plot()` は常に単一 Axes | multi-channel/pair では Iterator の場合がある。先に選択する |
| `CepstralFrame.plot(qmax=...)` | line plot 後に `ax.set_xlim(...)`。`qmin/qmax` は `CepstrogramFrame.plot()` の引数 |
| `SpectrogramFrame.get_frame_at(10)` を 10 秒の可視化に使う | time index。`.times` で秒から index を求める。`CepstrogramFrame` にはこの API はない |
| CSD/transfer に generic `.dB` / `Aw=True` | `view="level"`, `"gain_db"`, `"transfer_level_db"` を使う。Aw は拒否される |
| `describe(normalize=True)` が解析値を変える | playback display だけ。Frame data は不変 |
| Welch plot を PSD と表示 | Wandas Welch は averaged peak amplitude |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — summary、overlay、cepstral、typed pairwise の可視化例
- [`references/plot_api.md`](references/plot_api.md) — v0.7.2 plot signatures と view 契約
