# Wandas 0.7.2 Spectral API Reference

ソース: `wandas/wandas/frames/mixins/channel_transform_mixin.py`, `wandas/wandas/frames/spectral.py`, `wandas/wandas/frames/spectrogram.py`, `wandas/wandas/frames/cepstral.py`, `wandas/wandas/frames/cepstrogram.py`, `wandas/wandas/frames/pairwise.py`

## Contents

1. FFT, Welch, STFT
2. Cepstral transforms
3. Fractional-octave transforms
4. Typed pairwise transforms
5. Shape and level contracts

## FFT, Welch, STFT

```python
.fft(n_fft: int | None = None, window: str = "hann") -> SpectralFrame
```

One-sided peak-amplitude spectrum。positive-frequency bin（Nyquist 以外）を倍化し、window coherent gain で正規化する。

```python
.welch(
    n_fft: int = 2048,
    hop_length: int | None = None,
    win_length: int | None = None,
    window: str = "hann",
    average: str = "mean",
) -> SpectralFrame
```

Segment power を mean/median average して peak amplitude に変換する。物理単位は input channel と同じで、PSD や per-Hz ではない。

```python
.stft(
    n_fft: int = 2048,
    hop_length: int | None = None,
    win_length: int | None = None,
    window: str = "hann",
) -> SpectrogramFrame
```

One-sided peak-amplitude STFT。`SpectrogramFrame.get_frame_at(time_idx)` は秒ではなく integer frame index。

```python
SpectralFrame.ifft() -> ChannelFrame
SpectrogramFrame.istft() -> ChannelFrame
```

FFT inverse は stored `n_fft` / `window` の prepared input を再構成する。default Hann の zero sample を割り戻さない。

## Cepstral transforms

```python
ChannelFrame.cepstrum(
    n_fft: int | None = None,
    window: str = "hann",
    floor: float = 1e-12,
) -> CepstralFrame

SpectrogramFrame.cepstrum(
    floor: float = 1e-12,
) -> CepstrogramFrame
```

両方とも normalized magnitude に floor を適用して real cepstrum を作る。

```python
cepstral.lifter(
    cutoff: float,
    mode: Literal["low", "high"] = "low",
) -> SameCepstralFrame

cepstral.to_spectral_envelope() -> SpectralFrame | SpectrogramFrame
```

`lifter()` / envelope reconstruction は complete, unsliced quefrency axis が必要。

Plot API:

```python
CepstralFrame.plot(
    plot_type="quefrency",
    ax=None,
    *,
    title=None,
    xlabel="Quefrency [s]",
    ylabel="Real cepstrum",
    **kwargs,
)

CepstrogramFrame.plot(
    plot_type="cepstrogram",
    ax=None,
    *,
    title=None,
    cmap="RdBu_r",
    qmin=0.0,
    qmax=None,
    vmin=None,
    vmax=None,
    **kwargs,
)
```

## Fractional-octave transforms

この節の API は `wandas[psychoacoustic]` を必要とする。

```python
ChannelFrame.noct_spectrum(
    fmin: float = 25,
    fmax: float = 20000,
    n: int = 3,
    G: int = 10,
    fr: int = 1000,
) -> NOctFrame
```

各 band の RMS amplitude。`G=10` は base `10**(3/10)`、`G=2` は base 2 convention。

```python
SpectralFrame.noct_synthesis(
    fmin: float,
    fmax: float,
    n: int = 3,
    G: int = 10,
    fr: int = 1000,
) -> NOctFrame
```

48 kHz のみ。authoritative `n_fft` は `SpectralFrame` 自身から取得する。

## Typed pairwise transforms

```python
ChannelFrame.coherence(
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window="hann",
    detrend="constant",
) -> CoherenceFrame
```

`CoherenceFrame.coherence` は raw magnitude-squared coherence。undefined zero-energy bin は NaN。pairwise Frame は `.pairs`, `.pair_domains`, `.select_pair(output, input)`, `.plot_matrix()` を持つ。

```python
ChannelFrame.csd(
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window="hann",
    detrend="constant",
    scaling="spectrum",
    average="mean",
) -> CrossSpectralFrame
```

- raw: `P_out_in = conj(X_input) * X_output`
- properties: `.magnitude`, `.phase`, `.level_db`, `.scaling`
- `level_db`: `10 * log10(abs(P_out_in) / pair_reference)`
- plot view: `magnitude`, `phase`, `level`

```python
ChannelFrame.transfer_function(
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window="hann",
    detrend="constant",
    scaling="spectrum",
    average="mean",
) -> TransferFunctionFrame
```

- canonical raw: `H_out_in = P_out_in / P_in_in`
- properties: `.gain`, `.phase`, `.gain_db`, `.transfer_level_db`, `.denominator_role`
- `gain_db` は dimensionless pair のみ。
- plot view: `gain`, `phase`, `gain_db`, `transfer_level_db`

Pair selector の integer は original source-channel index。string selector は opaque source-channel ID であり display label ではない。

## Shape and level contracts

| Result | Mono/single-pair public shape | Multi public shape |
|---|---|---|
| Spectral property | `(frequency,)` | `(channel, frequency)` |
| Spectrogram property | `(frequency, time)` | `(channel, frequency, time)` |
| Cepstral data | `(quefrency,)` | `(channel, quefrency)` |
| Cepstrogram data | `(quefrency, time)` | `(channel, quefrency, time)` |
| Pairwise property | `(frequency,)` | `(pair, frequency)` |

FFT/Welch/STFT/N-octave `.dB` は channel reference を用いた amplitude level。CrossSpectral の `.level_db` は power-like なので 10 log10。pairwise A-weighting は拒否される。
