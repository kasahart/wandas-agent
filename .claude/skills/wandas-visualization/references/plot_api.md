# Wandas 0.7.2 Visualization API Reference

ソース: `wandas/wandas/frames/channel.py`, `spectral.py`, `spectrogram.py`, `noct.py`, `roughness.py`, `cepstral.py`, `cepstrogram.py`, `pairwise.py`

## Contents

1. Channel and spectral plots
2. Cepstral plots
3. Pairwise plots
4. Return and compute behavior

## Channel and spectral plots

```python
ChannelFrame.plot(
    plot_type="waveform", ax=None, title=None, overlay=False,
    xlabel=None, ylabel=None, alpha=1.0, xlim=None, ylim=None, **kwargs,
) -> Axes | Iterator[Axes]

ChannelFrame.rms_plot(
    ax=None, title=None, overlay=True, Aw=False, **kwargs,
) -> Axes | Iterator[Axes]
```

```python
ChannelFrame.describe(
    normalize=True,
    is_close=True,
    *,
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
    **kwargs,
) -> list[Figure] | None
```

`normalize` は playback display 用。summary の Welch は peak-amplitude spectrum で PSD ではない。

```python
SpectralFrame.plot(
    plot_type="frequency", ax=None, title=None, overlay=False,
    xlabel=None, ylabel=None, alpha=1.0, xlim=None, ylim=None,
    Aw=False, **kwargs,
) -> Axes | Iterator[Axes]

SpectrogramFrame.plot(
    plot_type="spectrogram", ax=None, title=None, cmap="jet",
    vmin=None, vmax=None, fmin=0, fmax=None, xlim=None, ylim=None,
    Aw=False, overlay=False, **kwargs,
) -> Axes | Iterator[Axes]

SpectrogramFrame.plot_Aw(
    plot_type="spectrogram", ax=None, **kwargs,
) -> Axes | Iterator[Axes]
```

```python
NOctFrame.plot(
    plot_type="noct", ax=None, title=None, overlay=False,
    xlabel=None, ylabel=None, alpha=1.0, xlim=None, ylim=None,
    Aw=False, **kwargs,
) -> Axes | Iterator[Axes]

RoughnessFrame.plot(
    plot_type="heatmap", ax=None, title=None, cmap="viridis",
    vmin=None, vmax=None, xlabel="Time [s]",
    ylabel="Frequency [Bark]",
    colorbar_label="Specific Roughness [Asper/Bark]", **kwargs,
) -> Axes
```

## Cepstral plots

```python
CepstralFrame.plot(
    plot_type="quefrency",
    ax=None,
    *,
    title=None,
    xlabel="Quefrency [s]",
    ylabel="Real cepstrum",
    **line_kwargs,
) -> Axes | Iterator[Axes]
```

`qmin` / `qmax` 引数はない。返された Axes へ `set_xlim()` を使う。

```python
CepstrogramFrame.plot(
    plot_type="cepstrogram",
    ax=None,
    *,
    title=None,
    xlabel="Time [s]",
    ylabel="Quefrency [s]",
    cmap="RdBu_r",
    qmin=0.0,
    qmax=None,
    vmin=None,
    vmax=None,
    **kwargs,
) -> Axes | Iterator[Axes]
```

Multi-channel `CepstrogramFrame` へ explicit `ax` は渡せない。channel を選ぶか、`ax=None` で個別 panel を作る。

## Pairwise plots

```python
PairwiseSpectralFrame.plot(
    plot_type="frequency", ax=None, title=None, overlay=False,
    xlabel=None, ylabel=None, alpha=1.0, xlim=None, ylim=None,
    Aw=False, view=None, **kwargs,
) -> Axes | Iterator[Axes]

PairwiseSpectralFrame.plot_matrix(
    plot_type="matrix", *, view=None, **kwargs,
) -> Axes | Iterator[Axes]
```

| Concrete Frame | Valid view values |
|---|---|
| `CoherenceFrame` | `None`, `"coherence"`, `"raw"` |
| `CrossSpectralFrame` | `None`, `"magnitude"`, `"phase"`, `"level"` |
| `TransferFunctionFrame` | `None`, `"gain"`, `"phase"`, `"gain_db"`, `"transfer_level_db"` |

全 pairwise Frame で `Aw=True` を拒否する。

## Return and compute behavior

- plot/describe は requested values を materialize する compute boundary。
- single-channel/selected-pair は通常 `Axes`。multi-channel/pair は `Iterator[Axes]` の場合がある。
- script で display event loop が必要なら `matplotlib.pyplot.show()` は使えるが、data drawing 自体は Frame plot method に任せる。
- overlay は同一 Axes へ描く操作。別 Frame の比較では `ax=` を明示する。
