---
name: wandas-signal-processing
description: Use when filtering, normalizing, resampling, trimming, fading, separating harmonic and percussive content, computing channel differences, calculating calibrated RMS or sound-level trends, or evaluating loudness, roughness, and sharpness with Wandas 0.7.2.
---

# Wandas: Signal Processing

`ChannelFrame` の時間域処理を、校正、metadata、lineage、Dask laziness を保ったまま組み立てる。

## Mandatory Rules

1. **Wandas-first**: signal transform は Wandas メソッドを使い、`scipy.signal` や NumPy で再実装しない。NumPy は materialize 後の小さな統計集約に限る。
2. **Method chaining**: 各操作は新しい Frame を返す。元 Frame を上書きした前提で扱わない。
3. **Visualization**: `.plot()` / `.describe()` を使い、`plt.plot(frame.data)` で直接描画しない。
4. **Preserve calibration**: level/psychoacoustic 解析は calibrated linear data から行う。`normalize()` 後の値を SPL として解釈しない。

## Filtering and Temporal Processing

| メソッド | シグネチャ | 返り値 |
|---|---|---|
| `.high_pass_filter` | `(cutoff: float, order: int = 4)` | `ChannelFrame` |
| `.low_pass_filter` | `(cutoff: float, order: int = 4)` | `ChannelFrame` |
| `.band_pass_filter` | `(low_cutoff: float, high_cutoff: float, order: int = 4)` | `ChannelFrame` |
| `.a_weighting` | `()` | `ChannelFrame` |
| `.normalize` | `(norm=inf, axis=-1, threshold=None, fill=None)` | `ChannelFrame` |
| `.remove_dc` | `()` | `ChannelFrame` |
| `.resampling` | `(target_sr: float, **kwargs)` | `ChannelFrame` |
| `.trim` | `(start: float = 0, end: float | None = None)` | `ChannelFrame` |
| `.fix_length` | `(length: int | None = None, duration: float | None = None)` | `ChannelFrame` |
| `.fade` | `(fade_ms: float = 50)` | `ChannelFrame` |
| `.channel_difference` | `(other_channel: int | str = 0)` | `ChannelFrame` |
| `.hpss_harmonic` / `.hpss_percussive` | `(kernel_size=31, power=2, margin=1, n_fft=2048, hop_length=None, win_length=None, window="hann", center=True, pad_mode="constant")` | `ChannelFrame` |

HPSS は `wandas[effects]` が必要。Frame 単体の resampling 名は `.resampling()`、`ChannelFrameDataset` では `.resample()`。

## Level and Trend Processing

| メソッド | シグネチャ | 返り値 | v0.7.2 契約 |
|---|---|---|---|
| `.rms` | property | `ndarray (n_channels,)` | calibrated linear RMS。即時計算し、Frame は返さない |
| `.rms_trend` | `(frame_length=2048, hop_length=512, dB=False, Aw=False)` | `ChannelFrame` | centered/zero-padded window RMS。`dB=True` の floor は -240 dB |
| `.sound_level` | `(freq_weighting="Z", time_weighting="Fast", dB=False)` | `ChannelFrame` | frequency weighting 後に Fast/Slow exponential RMS。`dB=True` の floor は -200 dB |
| `.channels[i].level_reference.to_level` | `(amplitude)` | `float | ndarray` | scalar/array の linear amplitude を channel reference 相対 level に変換 |

`freq_weighting`: `"A"`, `"C"`, `"Z"` または `None`（flat）。`time_weighting`: `"Fast"` (125 ms), `"Slow"` (1 s)。

`.sound_level()` は実装済み filter/time constant を提供するが、IEC/JIS sound-level meter の tolerance、detector、校正、指向性まで満たすことを主張しない。
`dB=True` は各 channel reference 相対。SoundFile-backed WAV は既定で dBFS、Pa 校正済みなら dB SPL、単位なし identity reference なら generic dB になる。

## Psychoacoustic Metrics

| メソッド | シグネチャ | 返り値 | 単位 |
|---|---|---|---|
| `.loudness_zwtv` | `(field_type="free")` | `ChannelFrame` | sone |
| `.loudness_zwst` | `(field_type="free")` | `ndarray (n_channels,)` | sone |
| `.roughness_dw` | `(overlap=0.5)` | `ChannelFrame` | asper |
| `.roughness_dw_spec` | `(overlap=0.5)` | `RoughnessFrame` | asper/Bark |
| `.sharpness_din` | `(weighting="din", field_type="free")` | `ChannelFrame` | acum |
| `.sharpness_din_st` | `(weighting="din", field_type="free")` | `ndarray (n_channels,)` | acum |

`wandas[psychoacoustic]` が必要。`field_type` は `"free"` / `"diffuse"`、sharpness weighting は `"din"`, `"aures"`, `"bismarck"`, `"fastl"`。

## Patterns

### Immutable preprocessing pipeline

```python
import wandas as wd

source = wd.read("noisy.wav")
cleaned = (
    source
    .remove_dc()
    .high_pass_filter(cutoff=50)
    .low_pass_filter(cutoff=8_000)
    .fade(fade_ms=10)
)

cleaned.describe(fmin=20, fmax=8_000)
```

Amplitude を比較・校正する解析では `.normalize()` を入れない。形状確認や再生用に正規化する場合だけ明示する。

### Calibrated A-weighted level

```python
import wandas as wd

raw = wd.read("noise.wav")
pressure = raw.with_calibration(
    {0: wd.ChannelCalibration(factor=0.42, unit="Pa")}
)

# 時間トレンド
level_fast = pressure.sound_level("A", "Fast", dB=True)
level_fast.plot(title="A-weighted Fast level")

# 全区間の A-weighted RMS amplitude level
weighted = pressure.a_weighting()
reference = weighted.channels[0].level_reference
equivalent_level = reference.to_level(weighted.rms[0])
print(f"Equivalent A-weighted level: {equivalent_level:.1f} {reference.unit}")
```

### RMS trend with channel-aware reference

```python
rms_level = pressure.rms_trend(
    frame_length=2_048,
    hop_length=512,
    dB=True,
    Aw=True,
)

print(rms_level.channels[0].unit)
rms_level.plot(title="A-weighted RMS amplitude level")
```

### Psychoacoustic summary

```python
import wandas as wd

signal = wd.read("product-sound.wav")
loudness = signal.loudness_zwtv(field_type="free")
roughness = signal.roughness_dw(overlap=0.5)
sharpness = signal.sharpness_din(weighting="din", field_type="free")

loudness.plot(title="Time-varying loudness [sone]")
roughness.plot(title="Time-varying roughness [asper]")
sharpness.plot(title="Time-varying sharpness [acum]")

print(signal.loudness_zwst(field_type="free"))
print(signal.sharpness_din_st(weighting="din", field_type="free"))
```

### Combine Frames before channel comparison

```python
reference = wd.read("reference.wav").rename_channels({0: "reference"})
measurement = wd.read("measurement.wav").rename_channels({0: "measurement"})
combined = reference.concat_frame(measurement)

difference = combined.channel_difference(other_channel="reference")
difference.plot(overlay=True, title="Difference from reference")
```

## Common Mistakes

| 間違い | 正解 |
|---|---|
| `.band_pass_filter(low=100, high=5_000)` | `low_cutoff` / `high_cutoff` を使う |
| `normalize(norm=2)` を RMS=1 と呼ぶ | L2 vector norm の正規化。RMS 値は `.rms` で確認する |
| `read_wav(..., normalize=True)` | `wd.read()` に normalize 引数はない。必要なら後段 `.normalize()` |
| `np.mean(sound_level(..., dB=True).data)` を Leq と呼ぶ | dB を算術平均しない。weighted linear RMS を `LevelReference.to_level()` で変換する |
| 未校正 WAV の値を dB SPL と呼ぶ | `level_reference.unit/label` を確認し、Pa 校正する。SoundFile-backed audio の既定は dBFS |
| `.loudness_zwst().plot()` | steady-state API は ndarray。時変 Frame の `.loudness_zwtv()` を plot する |
| `a_weighting()` を pairwise spectral Frame に適用 | A weighting は ChannelFrame/SpectralFrame 系の対応 API に限る。typed pairwise Frame では拒否される |
| 心理音響 extra なしで呼ぶ | `wandas[psychoacoustic]` を導入する |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — 校正、filter、level、psychoacoustic のワークフロー
- [`references/filters_api.md`](references/filters_api.md) — filter・時間処理・level API
- [`references/psychoacoustic_api.md`](references/psychoacoustic_api.md) — psychoacoustic API と戻り値
