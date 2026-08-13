# wandas-analyst: Workflows

## Scenario 1: Calibrated environmental level comparison

### Purpose

Day/night recordings の A-weighted overall level と Fast trend を比較し、追加調査すべき時間帯を特定する。法令適合は測定器・手順・地域基準を別途確認する。

```python
import numpy as np
import wandas as wd

MIC_FACTOR_PA_PER_FS = 0.42

day_raw = wd.read("day.wav").rename_channels({0: "day"})
night_raw = wd.read("night.wav").rename_channels({0: "night"})

day = day_raw.with_calibration(
    {"day": wd.ChannelCalibration(factor=MIC_FACTOR_PA_PER_FS, unit="Pa")}
)
night = night_raw.with_calibration(
    {"night": wd.ChannelCalibration(factor=MIC_FACTOR_PA_PER_FS, unit="Pa")}
)

def equivalent_a_level(frame):
    weighted = frame.a_weighting()
    reference = weighted.channels[0].level_reference
    return reference.to_level(weighted.rms[0]), reference.label

day_level, level_label = equivalent_a_level(day)
night_level, _ = equivalent_a_level(night)

day_fast = day.sound_level("A", "Fast", dB=True)
night_fast = night.sound_level("A", "Fast", dB=True)

print(f"Day:   {day_level:.1f} {level_label}")
print(f"Night: {night_level:.1f} {level_label}")
print(f"Night Fast max: {np.max(night_fast.data):.1f} {night_fast.channels[0].unit}")

ax = day_fast.plot(overlay=True, label="Day")
night_fast.plot(ax=ax, overlay=True, label="Night", title="A-weighted Fast level")
ax.legend()
```

## Scenario 2: Motor anomaly investigation

### Hypothesis

Abnormal condition では narrowband peak と harmonic/cepstral spacing が増え、発生時刻が局在する可能性がある。RPM またはタコ信号が既知のときだけ 1×、2× などの回転次数と照合する。未知なら「回転由来候補」に留める。

```python
import numpy as np
import wandas as wd

normal = wd.read("normal.wav")
abnormal = wd.read("abnormal.wav")

normal_spectrum = normal.fft()
abnormal_spectrum = abnormal.fft()

ax = normal_spectrum.plot(overlay=True, label="Normal", alpha=0.7)
abnormal_spectrum.plot(ax=ax, overlay=True, label="Abnormal", title="FFT comparison")
ax.legend()

peak_indices = np.argsort(abnormal_spectrum.magnitude)[-5:][::-1]
for index in peak_indices:
    print(
        f"{abnormal_spectrum.freqs[index]:.1f} Hz: "
        f"{abnormal_spectrum.magnitude[index]:.4g}"
    )

time_frequency = abnormal.stft(n_fft=1_024, hop_length=128)
time_frequency.plot(fmax=1_000, cmap="inferno", title="Abnormal time-frequency map")
```

## Scenario 3: Typed input-output relationship

```python
import wandas as wd

input_signal = wd.read("input.wav").rename_channels({0: "input"})
output_signal = wd.read("output.wav").rename_channels({0: "output"})
combined = input_signal.concat_frame(output_signal)

coherence = combined.coherence(n_fft=2_048).select_pair(output=1, input=0)
transfer = combined.transfer_function(n_fft=2_048).select_pair(output=1, input=0)

coherence.plot(title="Output/Input coherence")
transfer.plot(view="gain_db", title="Output/Input transfer gain")

print("Pair:", coherence.pairs[0])
print("Transfer definition:", transfer.definition)
```

Input/output の sampling rate と長さが異なる場合は、結合前に意図した alignment を決める。

## Scenario 4: Treatment before/after comparison

```python
import numpy as np
import wandas as wd

MIC_FACTOR_PA_PER_FS = 0.42
before = wd.read("before.wav").with_calibration(
    {0: wd.ChannelCalibration(factor=MIC_FACTOR_PA_PER_FS, unit="Pa")}
)
after = wd.read("after.wav").with_calibration(
    {0: wd.ChannelCalibration(factor=MIC_FACTOR_PA_PER_FS, unit="Pa")}
)

before_bands = before.noct_spectrum(fmin=25, fmax=8_000, n=3)
after_bands = after.noct_spectrum(fmin=25, fmax=8_000, n=3)
reduction_db = before_bands.dBA - after_bands.dBA

for frequency, reduction in zip(before_bands.freqs, reduction_db, strict=True):
    print(f"{frequency:7.1f} Hz: {reduction:+.1f} dB")

ax = before_bands.plot(Aw=True, overlay=True, label="Before")
after_bands.plot(ax=ax, Aw=True, overlay=True, label="After", title="1/3-octave comparison")
ax.legend()
```

Mono public property は `(band,)` なので、旧コードのような `reduction_db[0]` は不要。

## Scenario 5: Reused STFT and cepstrogram

```python
import wandas as wd

signal = wd.read("bounded-recording.wav")
stft = signal.stft(n_fft=2_048, hop_length=256).astype("complex64").cache()

stft.plot(fmin=20, fmax=8_000, cmap="inferno")
stft.cepstrum().plot(qmin=0, qmax=0.02, title="Cepstrogram")
```

`cache()` は bounded recording が memory に収まることを確認してから使う。
