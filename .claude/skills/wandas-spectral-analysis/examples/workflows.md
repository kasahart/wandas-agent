# wandas-spectral-analysis: Workflows

## Scenario 1: FFT で peak frequency を特定する

```python
import numpy as np
import wandas as wd

signal = wd.read("machine.wav")
spectrum = signal.fft()

peak_index = np.argmax(spectrum.magnitude)
print(f"Peak frequency: {spectrum.freqs[peak_index]:.1f} Hz")
spectrum.plot(xlim=(20, 8_000), title="Peak-amplitude spectrum")
```

`.magnitude` と `.data` は mono なら `(frequency,)`。multi-channel では `(channel, frequency)`。

## Scenario 2: Welch average で安定した amplitude spectrum を得る

```python
import wandas as wd

signal = wd.read("noise.wav")
mean_spectrum = signal.welch(n_fft=4_096, hop_length=1_024, average="mean")
median_spectrum = signal.welch(n_fft=4_096, hop_length=1_024, average="median")

ax = mean_spectrum.plot(overlay=True, label="Mean")
median_spectrum.plot(ax=ax, overlay=True, label="Median", title="Welch amplitude comparison")
ax.legend()
```

Wandas の Welch 結果は peak amplitude であり、PSD/per-Hz ではない。

## Scenario 3: STFT で異常時刻を調べる

```python
import numpy as np
import wandas as wd

signal = wd.read("sensor-log.csv", time_column="Time")
spectrogram = signal.remove_dc().stft(n_fft=2_048, hop_length=256)

spectrogram.plot(
    cmap="inferno",
    fmin=0,
    fmax=2_000,
    vmin=-80,
    vmax=-20,
    title="Time-frequency map",
)

time_index = int(np.argmin(np.abs(spectrogram.times - 10.0)))
spectrogram.get_frame_at(time_index).plot(title="Spectrum near 10 s")
```

## Scenario 4: Cepstrogram から時間変動する envelope を得る

```python
import wandas as wd

signal = wd.read("speech.wav")
cepstrogram = signal.stft(n_fft=2_048, hop_length=256).cepstrum()
envelope = cepstrogram.lifter(cutoff=0.002, mode="low").to_spectral_envelope()

cepstrogram.plot(qmax=0.02, title="Cepstrogram")
envelope.plot(fmin=20, fmax=8_000, title="Time-varying spectral envelope")
```

## Scenario 5: Fractional-octave band level を見る

`wandas[psychoacoustic]` を導入してから実行する。

```python
import wandas as wd

signal = wd.read("environment.wav")
bands = signal.noct_spectrum(fmin=25, fmax=8_000, n=3)
bands.plot(Aw=True, title="A-weighted 1/3-octave levels")
```

Output は各 band の RMS amplitude。`.dB` / `.dBA` は channel reference 相対 level。

## Scenario 6: input-output pair を明示して解析する

```python
import wandas as wd

excitation = wd.read("input.wav").rename_channels({0: "input"})
response = wd.read("output.wav").rename_channels({0: "output"})
combined = excitation.concat_frame(response)

coherence = combined.coherence(n_fft=2_048).select_pair(output=1, input=0)
csd = combined.csd(n_fft=2_048, scaling="density").select_pair(output=1, input=0)
transfer = combined.transfer_function(n_fft=2_048).select_pair(output=1, input=0)

coherence.plot(title="Coherence")
csd.plot(view="level", title="Cross-spectral density level")
transfer.plot(view="gain_db", title="Transfer gain")
```

`gain_db` は input/output の pair domain が dimensionless のときだけ使える。異なる単位間では `transfer_level_db` を選ぶ。
