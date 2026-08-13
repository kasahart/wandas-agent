# wandas-indexing workflows

## 複数センサー CSV のチャンネル選択から周波数解析まで

```python
import numpy as np
import wandas as wd

sr = 12000
time = np.arange(sr * 2, dtype=float) / sr
data = np.vstack([
    np.sin(2 * np.pi * 120 * time),
    np.sin(2 * np.pi * 240 * time),
    np.sin(2 * np.pi * 480 * time),
])
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["acc_x", "acc_y", "acc_z"])

selected = frame[["acc_x", "acc_z"]]
spectrum = selected.normalize().fft()

assert spectrum.n_channels == 2
assert hasattr(spectrum, "freqs")
```

## sample index による時間範囲切り出し

```python
import numpy as np
import wandas as wd

sr = 16000
data = np.random.default_rng(2).normal(size=(2, sr * 4))
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["mic_front", "mic_rear"])

start = int(0.5 * frame.sampling_rate)
end = int(1.5 * frame.sampling_rate)
window = frame[:, start:end]

assert window.n_channels == 2
assert window.shape[-1] == end - start
assert np.allclose(window.source_time_offset, 0.5)
```

local `window.time` は0秒から始まり、元波形内の開始位置は `source_time_offset` に保持される。

## Spectrogram の時刻範囲を切り出す

```python
import numpy as np
import wandas as wd

signal = wd.generate_sin(freqs=[440, 880], sampling_rate=16_000, duration=1.0)
spectrogram = signal.stft(n_fft=512, hop_length=128)
time_window = spectrogram[:, :, 2:8]

assert time_window.n_channels == 2
assert time_window.freqs.shape == spectrogram.freqs.shape
assert time_window.n_frames == 6
assert np.allclose(time_window.source_time_offset, 2 * 128 / 16_000)
```

Wandas 0.7.2 の `SpectralFrame` / `SpectrogramFrame` は complete canonical frequency grid を必要とする。周波数表示の絞り込みは `.plot(fmin=..., fmax=...)` を使い、frequency-bin 部分 slice で新しい Frame を作らない。
