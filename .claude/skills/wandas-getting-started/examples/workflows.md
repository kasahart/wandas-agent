# wandas-getting-started: Workflows

## Recipe 1: WAV/CSV を同じ入口で読む

```python
import wandas as wd

audio = wd.read("recording.wav", channel=0, start=0.0, end=10.0)
sensor = wd.read("vibration.csv", time_column="Time")

audio.describe(fmin=20, fmax=min(8_000, audio.sampling_rate / 2))
sensor.plot(title="Vibration waveform")
```

URL、bytes、binary file-like も `wd.read()` へ渡せる。匿名の CSV bytes には `file_type="csv"` を指定する。

```python
csv_bytes = b"time,x\n0.0,1.0\n0.1,2.0\n"
frame = wd.read(csv_bytes, file_type="csv")
```

## Recipe 2: 校正済み ChannelFrame を作る

```python
import numpy as np
import wandas as wd

sr = 48_000
t = np.arange(sr) / sr
raw_voltage = 0.1 * np.sin(2 * np.pi * 1_000 * t)

raw = wd.from_numpy(raw_voltage, sampling_rate=sr, ch_labels=["mic"])
calibrated = raw.with_calibration(
    {"mic": wd.ChannelCalibration(factor=0.42, unit="Pa")}
)

reference = calibrated.channels[0].level_reference
print(reference.label)
print(reference.to_level(calibrated.rms[0]))
```

`LevelReference.to_level()` へ渡す値は、すでにチャンネルの linear domain にある値。校正係数を再度掛けない。

## Recipe 3: Frame の immutability と計算境界を確認する

```python
import wandas as wd

source = wd.read("machine.wav")
processed = source.remove_dc().low_pass_filter(cutoff=4_000)

assert processed is not source
print([entry["operation"] for entry in processed.operation_history])

# ここで初めて処理済み値を materialize
values = processed.data
```

## Recipe 4: 大きさを抑えて計算結果を再利用する

```python
import wandas as wd

signal = wd.read("bounded-recording.wav")
cached_spectrum = signal.stft(n_fft=2_048).astype("complex64").cache()

cached_spectrum.plot(fmin=20, fmax=8_000)
cached_spectrum.abs().plot(fmin=20, fmax=8_000)
```

`cache()` は Frame 全体をローカルメモリへ同期計算する。入力が収まることを先に確認する。

## Recipe 5: フォルダを metadata-first で扱う

```python
from pathlib import Path

import wandas as wd


def resolve_filename(path: Path) -> dict[str, object]:
    # 例: fan_loaded_1500rpm_01.wav
    machine, state, rpm_text, take = path.stem.split("_")
    return {
        "machine": machine,
        "state": state,
        "rpm": int(rpm_text.removesuffix("rpm")),
        "take": int(take),
    }


dataset = wd.from_folder(
    "recordings",
    file_extensions=[".wav"],
    metadata_resolver=resolve_filename,
)

selected = dataset.select(machine="fan", state="loaded", rpm=1_500)
calibration = wd.ChannelCalibration(factor=0.42, unit="Pa")
prepared = selected.apply(
    lambda frame: frame.with_calibration([calibration])
).trim(0, 5)

# Dataset に cache() はない。再利用する個々の Frame だけを materialize する。
first = prepared[0]
cached = None if first is None else first.astype("float32").cache()

if cached is not None:
    rms_pa = float(cached.rms[0])
    reference = cached.channels[0].level_reference
    print(reference.to_level(rms_pa), reference.label)
```

`metadata_resolver` はルートからの相対 `Path` を受け取る。命名規則が混在する場合は resolver 内で明示的に処理する。上の校正係数は例であり、実測したマイク・アンプ・ADC 系の値に置き換える。校正済み SPL 経路では `.normalize()` を使わない。

## Recipe 6: WDF を保存・復元する

```python
import wandas as wd

signal = wd.read("audio.wav").remove_dc()
signal.save("analysis.wdf", overwrite=True)

restored = wd.load("analysis.wdf")
print(type(restored).__name__)
```

WDF は `wandas[io]` extra が必要。`wd.load()` は保存された具象 Frame 型を復元する。
