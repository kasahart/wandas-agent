# Wandas 0.7.2 Signal Processing API Reference

ソース: `wandas/wandas/frames/mixins/channel_processing_mixin.py`, `wandas/wandas/processing/temporal.py`, `wandas/wandas/core/metadata.py`

## Contents

1. Filters and shaping
2. Channel and time operations
3. Level operations
4. Calibration rules

## Filters and shaping

```python
.high_pass_filter(cutoff: float, order: int = 4) -> ChannelFrame
.low_pass_filter(cutoff: float, order: int = 4) -> ChannelFrame
.band_pass_filter(
    low_cutoff: float,
    high_cutoff: float,
    order: int = 4,
) -> ChannelFrame
.a_weighting() -> ChannelFrame
```

カットオフは正で Nyquist 未満、band pass は `low_cutoff < high_cutoff`。

```python
.normalize(
    norm: float | None = float("inf"),
    axis: int | None = -1,
    threshold: float | None = None,
    fill: bool | None = None,
) -> ChannelFrame
```

- `norm=inf` は peak/vector infinity norm の正規化。
- `norm=2` は L2 vector norm の正規化で、RMS=1 の保証ではない。
- 校正値を保つ level 解析の前には使わない。

```python
.remove_dc() -> ChannelFrame
.trim(start: float = 0, end: float | None = None) -> ChannelFrame
.fix_length(length: int | None = None, duration: float | None = None) -> ChannelFrame
.fade(fade_ms: float = 50) -> ChannelFrame
.resampling(target_sr: float, **kwargs) -> ChannelFrame
```

`fade()` は両端に対称 Tukey window を適用する。

## Channel and time operations

```python
.channel_difference(other_channel: int | str = 0) -> ChannelFrame
```

選択した reference channel を各 channel の同じ array index から引く。`source_time_offset` を使った時間 alignment は行わない。

```python
.hpss_harmonic(
    kernel_size=31,
    power=2,
    margin=1,
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window="hann",
    center=True,
    pad_mode="constant",
) -> ChannelFrame

.hpss_percussive(...) -> ChannelFrame
```

`wandas[effects]` を必要とする。

## Level operations

```python
.rms_trend(
    frame_length: int = 2048,
    hop_length: int = 512,
    dB: bool = False,
    Aw: bool = False,
) -> ChannelFrame
```

- centered, zero-padded sliding RMS。
- `dB=False`: calibrated linear unit。
- `dB=True`: `20 * log10(max(window_rms / channel_ref, 1e-12))`。下限 -240 dB。
- 出力 sampling rate は入力を `hop_length` で割った値。

```python
.sound_level(
    freq_weighting: str | None = "Z",
    time_weighting: str = "Fast",
    dB: bool = False,
) -> ChannelFrame
```

- A/C/Z frequency weighting の後、Fast 125 ms または Slow 1 s の exponential power average を取る。
- `dB=False`: calibrated linear RMS。
- `dB=True`: `10 * log10(max(smoothed_power / ref**2, 1e-20))`。下限 -200 dB。
- full sound-level-meter conformity を保証しない。

```python
frame.rms -> ndarray  # shape: (n_channels,)
```

全 sample の calibrated linear RMS を即時計算する。lineage/history は増やさない。

## Calibration rules

```python
calibrated = frame.with_calibration(
    {"mic": wd.ChannelCalibration(factor=0.42, unit="Pa")}
)
reference = calibrated.channels[0].level_reference
level = reference.to_level(calibrated.rms[0])
```

- Pa の既定 ref は `2e-5` で、level unit は `dB SPL`。
- explicit `FS` / ref 1 は `dBFS`。
- unit 未設定/ref 1 は generic `dB re 1 input unit`。
- `to_level()` は calibrated linear amplitude を受け取り、factor を再適用しない。
