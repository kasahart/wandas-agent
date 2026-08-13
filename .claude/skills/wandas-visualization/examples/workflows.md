# wandas-visualization: Workflows

## Scenario 1: Recording overview を保存する

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

## Scenario 2: Filter 前後を同じ Axes で比べる

```python
import wandas as wd

original = wd.read("noisy.wav")
filtered = original.band_pass_filter(low_cutoff=100, high_cutoff=4_000)

ax = original.fft().plot(overlay=True, label="Original", alpha=0.7)
filtered.fft().plot(ax=ax, overlay=True, label="Filtered", title="Filter comparison")
ax.legend()
```

## Scenario 3: A-weighted spectrogram を表示する

```python
import wandas as wd

signal = wd.read("machine.wav")
spectrogram = signal.stft(n_fft=2_048, hop_length=256)

spectrogram.plot(
    Aw=True,
    cmap="inferno",
    fmin=100,
    fmax=5_000,
    vmin=-70,
    vmax=-20,
    title="A-weighted spectrogram",
)
```

`.plot_Aw()` は `.plot(Aw=True)` の shortcut。

## Scenario 4: Cepstrum と cepstrogram を見分ける

```python
cepstrum = signal.cepstrum(n_fft=2_048)
ax = cepstrum.plot(title="Real cepstrum")
ax.set_xlim(0, 0.02)

cepstrogram = spectrogram.cepstrum()
cepstrogram.plot(
    qmin=0,
    qmax=0.02,
    cmap="RdBu_r",
    title="Time-varying cepstrum",
)
```

## Scenario 5: Fractional-octave conditions を overlay する

```python
import wandas as wd

before = wd.read("before.wav")
after = wd.read("after.wav")

before_bands = before.noct_spectrum(fmin=25, fmax=8_000, n=3)
after_bands = after.noct_spectrum(fmin=25, fmax=8_000, n=3)

ax = before_bands.plot(overlay=True, label="Before")
after_bands.plot(ax=ax, overlay=True, label="After", title="1/3-octave comparison")
ax.legend()
```

## Scenario 6: Pairwise matrix と selected pair を使い分ける

```python
import wandas as wd

input_signal = wd.read("input.wav").rename_channels({0: "input"})
output_signal = wd.read("output.wav").rename_channels({0: "output"})
combined = input_signal.concat_frame(output_signal)

transfer = combined.transfer_function(n_fft=2_048)
transfer.plot_matrix(view="gain_db")

path = transfer.select_pair(output=1, input=0)
path.plot(view="phase", title="Output/Input phase")
```

## Scenario 7: Specific roughness を heatmap にする

```python
import wandas as wd

signal = wd.read("product-sound.wav")
roughness = signal.roughness_dw_spec(overlap=0.5)
roughness.plot(cmap="viridis", title="Specific roughness [asper/Bark]")
```
