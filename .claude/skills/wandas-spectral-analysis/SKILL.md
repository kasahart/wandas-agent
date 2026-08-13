---
name: wandas-spectral-analysis
description: Use when performing FFT, Welch-averaged amplitude analysis, STFT, fractional-octave analysis, real cepstrum or cepstrogram analysis, coherence, cross-spectral analysis, or transfer-function estimation with the typed spectral Frames in Wandas 0.7.2.
---

# Wandas: Spectral Analysis

時間域 `ChannelFrame` を、意味と軸を持つ spectral/cepstral/pairwise Frame へ遅延変換する。

## Mandatory Rules

1. **Wandas-first**: `np.fft` や `scipy.signal` で同じ解析を再実装せず、Wandas の Frame transform を使う。
2. **Typed results**: coherence/CSD/transfer の戻り値を generic `SpectralFrame` とみなさず、quantity-specific property と pair metadata を使う。
3. **Method chaining**: 変換は新しい Frame を返し、metadata、source time、lineage を保持する。
4. **Visualization**: `.plot()` / `.plot_matrix()` を使い、`plt.plot(frame.data)` で直接描画しない。

## Transform API

| メソッド | 主要引数 | 返り値 | 数値の意味 |
|---|---|---|---|
| `.fft` | `(n_fft=None, window="hann")` | `SpectralFrame` | one-sided peak-amplitude spectrum |
| `.welch` | `(n_fft=2048, hop_length=None, win_length=None, window="hann", average="mean")` | `SpectralFrame` | segment power を平均後、peak amplitude に変換。PSD/per-Hz ではない |
| `.stft` | `(n_fft=2048, hop_length=None, win_length=None, window="hann")` | `SpectrogramFrame` | one-sided peak-amplitude time-frequency data |
| `.cepstrum` | `(n_fft=None, window="hann", floor=1e-12)` | `CepstralFrame` | normalized real cepstrum |
| `.stft(...).cepstrum` | `(floor=1e-12)` | `CepstrogramFrame` | 各 STFT time frame の real cepstrum |
| `.noct_spectrum` | `(fmin=25, fmax=20000, n=3, G=10, fr=1000)` | `NOctFrame` | fractional-octave band RMS amplitude |
| `.coherence` | spectral window args + `detrend="constant"` | `CoherenceFrame` | typed magnitude-squared coherence |
| `.csd` | spectral window args + `detrend`, `scaling`, `average` | `CrossSpectralFrame` | typed `P_out_in = conj(X_input) * X_output` |
| `.transfer_function` | spectral window args + `detrend`, `scaling`, `average` | `TransferFunctionFrame` | typed `H_out_in = P_out_in / P_in_in` |

`hop_length=None` は STFT/coherence 系では通常 `n_fft // 4`、`win_length=None` は `n_fft`。Welch doc contract では default hop は `win_length // 4`。

`noct_spectrum()` / `noct_synthesis()` は center-frequency helper のため `wandas[psychoacoustic]` が必要。

## Inverse and Derived Transforms

| API | 入力 | 返り値 | 注意 |
|---|---|---|---|
| `.ifft()` | `SpectralFrame` | `ChannelFrame` | windowed analysis input を復元。default Hann の 0 値は割り戻さない |
| `.istft()` | `SpectrogramFrame` | `ChannelFrame` | stored STFT state で逆変換 |
| `.noct_synthesis(...)` | `SpectralFrame` | `NOctFrame` | 48 kHz のみ。`n_fft` は Frame から取得 |
| `.lifter(cutoff, mode="low")` | cepstral Frame | 同じ cepstral Frame | complete unsliced quefrency axis が必要 |
| `.to_spectral_envelope()` | cepstral Frame | `SpectralFrame` / `SpectrogramFrame` | zero-phase smooth envelope |

## Spectral Properties

| Frame | Quantity-specific properties |
|---|---|
| `SpectralFrame` | `.freqs`, `.magnitude`, `.phase`, `.power`, `.dB`, `.dBA`, `.unwrapped_phase` |
| `SpectrogramFrame` | `.freqs`, `.times`, `.magnitude`, `.dB`, `.dBA`, `.get_frame_at(time_idx)` |
| `CepstralFrame` | `.quefrencies`, `.n_fft`, `.window` |
| `CepstrogramFrame` | `.quefrencies`, `.times`, `.n_frames`, `.n_quefrency_bins` |
| `NOctFrame` | `.freqs`, `.dB`, `.dBA`, `.fmin`, `.fmax`, `.n` |

FFT、Welch、STFT、N-octave の `.dB` は channel reference 相対の amplitude level。単チャンネル public property は singleton channel 軸を省く。

`wd.read()` で読んだ WAV の既定 reference は full scale 1 なので `.dB` は dBFS。dB SPL が必要なら、FFT/STFT より前に実測係数を `with_calibration(..., unit="Pa")` で適用する。generic reference の結果も SPL と呼ばない。

## Typed Pairwise Results

| Frame | Public properties | Plot `view` |
|---|---|---|
| `CoherenceFrame` | `.coherence`, `.pairs`, `.pair_domains`, `.select_pair(output, input)` | `"coherence"` |
| `CrossSpectralFrame` | `.magnitude`, `.phase`, `.level_db`, `.scaling` | `"magnitude"`, `"phase"`, `"level"` |
| `TransferFunctionFrame` | `.gain`, `.phase`, `.gain_db`, `.transfer_level_db`, `.denominator_role` | `"gain"`, `"phase"`, `"gain_db"`, `"transfer_level_db"` |

Pairwise Frame は output-major/input-minor の flattened pair rows を持つ。A-weighting、arithmetic、inverse FFT は拒否される。`gain_db` は selected pair が dimensionless の場合だけ使える。

## Patterns

### Peak-amplitude FFT and Welch average

```python
import numpy as np
import wandas as wd

signal = wd.read("machine.wav")

spectrum = signal.fft(window="hann")
peak_index = np.argmax(spectrum.magnitude)
print(f"Peak: {spectrum.freqs[peak_index]:.1f} Hz")
spectrum.plot(xlim=(20, 8_000), title="Peak-amplitude FFT")

stable_amplitude = signal.welch(n_fft=4_096, hop_length=1_024)
stable_amplitude.plot(xlim=(20, 8_000), title="Welch-averaged amplitude")
```

### STFT and frame extraction

```python
spectrogram = signal.stft(n_fft=2_048, hop_length=256)
spectrogram.plot(fmin=20, fmax=4_000, cmap="inferno")

target_index = np.argmin(np.abs(spectrogram.times - 10.0))
frame_near_10s = spectrogram.get_frame_at(int(target_index))
frame_near_10s.plot(title="Spectrum near 10 s")
```

`get_frame_at()` の引数は秒ではなく time-frame index。
これは `SpectrogramFrame` の API で、`CepstrogramFrame` には公開 `get_frame_at()` がない。指定時刻の cepstrum が必要なら、元の time-domain Frame を意図した時間窓で `.trim()` してから `.cepstrum()` を計算する。

### Cepstral envelope

```python
cepstrum = signal.cepstrum(n_fft=2_048)
low_quefrency = cepstrum.lifter(cutoff=0.002, mode="low")
envelope = low_quefrency.to_spectral_envelope()

ax = cepstrum.plot(title="Real cepstrum")
ax.set_xlim(0, 0.02)
envelope.plot(xlim=(20, 8_000), title="Spectral envelope")
```

### Typed coherence and transfer path

```python
input_signal = wd.read("input.wav").rename_channels({0: "input"})
output_signal = wd.read("output.wav").rename_channels({0: "output"})
combined = input_signal.concat_frame(output_signal)

coherence = combined.coherence(n_fft=2_048).select_pair(output=1, input=0)
transfer = combined.transfer_function(n_fft=2_048).select_pair(output=1, input=0)

coherence.plot(title="Output/Input coherence")
transfer.plot(view="gain_db", title="Output/Input transfer gain")
```

`concat_frame()` の default alignment は strict。sampling rate と sample length を先に揃える。

## Common Mistakes

| 間違い | 正解 |
|---|---|
| Welch output を PSD / `dB/Hz` と呼ぶ | Wandas `.welch()` は peak-amplitude spectrum。density が必要な pairwise CSD では `scaling="density"` を使う |
| `.coherence()` の返り値を `SpectralFrame` と扱う | `CoherenceFrame.coherence` と pair API を使う |
| Frame を `.add_channel(other_frame)` で結合 | `.concat_frame(other_frame)` を使う |
| `get_frame_at(10)` を 10 秒と解釈 | index 10。秒は `.times` から最寄り index を探す |
| `CepstrogramFrame.get_frame_at(...)` | 公開 API はない。全体を plot するか、元波形の対象時間窓を `.trim()` 後に `.cepstrum()` |
| pairwise Frame に `Aw=True` | pairwise A-weighting は未定義で拒否される |
| N-octave で optional dependency error | `wandas[psychoacoustic]` を導入する |
| transfer の全 pair を1本の FRF と解釈 | `.select_pair(output=..., input=...)` で役割を明示する |
| single-channel property を `[0]` で固定参照 | v0.7.0+ は public singleton channel 軸を省く |
| Hann FFT を `.ifft()` すれば元波形が完全復元 | windowed input を復元する。exact prepared-input round trip には `window="boxcar"` |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — amplitude、STFT、cepstrum、typed pairwise のワークフロー
- [`references/spectral_api.md`](references/spectral_api.md) — v0.7.2 spectral/cepstral/pairwise API
