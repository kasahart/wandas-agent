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
```
