# wandas-signal-processing: Workflows

## Scenario 1: 校正済み環境音の level を確認する

```python
import numpy as np
import wandas as wd

raw = wd.read("noise.wav")
pressure = raw.with_calibration(
    {0: wd.ChannelCalibration(factor=0.42, unit="Pa")}
)

fast = pressure.sound_level(freq_weighting="A", time_weighting="Fast", dB=True)
weighted = pressure.a_weighting()
reference = weighted.channels[0].level_reference
equivalent_level = reference.to_level(weighted.rms[0])

print(f"Equivalent level: {equivalent_level:.1f} {reference.label}")
print(f"Fast max: {np.max(fast.data):.1f} {fast.channels[0].unit}")
fast.plot(title="A-weighted Fast level")
```

`sound_level()` の time trend と、全区間 linear RMS から求める equivalent level を混同しない。規制適合判定には測定器・規格側の追加要件も確認する。

## Scenario 2: 機械振動の帯域を抽出する

```python
import wandas as wd

sensor = wd.read("vibration.csv", time_column="Time")
filtered = (
    sensor
    .remove_dc()
    .band_pass_filter(low_cutoff=100, high_cutoff=3_000)
)

ax = sensor.plot(overlay=True, label="Original", alpha=0.5)
filtered.plot(ax=ax, overlay=True, label="Filtered", title="Band-pass comparison")
ax.legend()
```

絶対振幅や施工前後の低減量を比較する場合は `.normalize()` しない。

## Scenario 3: 心理音響指標を比較する

```python
import wandas as wd

signal = wd.read("product-sound.wav")

loudness = signal.loudness_zwtv(field_type="free")
roughness = signal.roughness_dw(overlap=0.5)
sharpness = signal.sharpness_din(weighting="din", field_type="free")

loudness.plot(title="Loudness [sone]")
roughness.plot(title="Roughness [asper]")
sharpness.plot(title="Sharpness [acum]")

print("steady loudness:", signal.loudness_zwst(field_type="free"))
print("steady sharpness:", signal.sharpness_din_st(weighting="din", field_type="free"))

roughness_spec = signal.roughness_dw_spec(overlap=0.5)
roughness_spec.plot(cmap="viridis", title="Specific roughness [asper/Bark]")
```

## Scenario 4: RMS amplitude level の時間変化を見る

```python
import wandas as wd

signal = wd.read("machine-run.wav")
calibrated = signal.with_calibration(
    {0: wd.ChannelCalibration(factor=9.81, unit="m/s^2")}
)

rms_z = calibrated.rms_trend(dB=True, Aw=False)
rms_a = calibrated.rms_trend(dB=True, Aw=True)

ax = rms_z.plot(overlay=True, label="Z-weighted")
rms_a.plot(ax=ax, overlay=True, label="A-weighted", title="RMS level comparison")
ax.legend()
```

## Scenario 5: HPSS で harmonic/percussive を分離する

```python
import wandas as wd

music = wd.read("music.wav")
harmonic = music.hpss_harmonic(kernel_size=31)
percussive = music.hpss_percussive(kernel_size=31)

harmonic.describe()
percussive.describe()
```

HPSS には `wandas[effects]` が必要。
