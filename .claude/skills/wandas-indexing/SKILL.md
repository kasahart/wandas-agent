---
name: wandas-indexing
description: Use when selecting or slicing wandas frames by channel index, channel label, channel metadata query, boolean mask, NumPy index array, or multidimensional indexing such as frame[channel, sample_slice] and spectrogram[channel, freq_slice, time_slice].
---

# wandas: Indexing and Selection

wandas frame の `[]` は **先頭の indexing 要素を channel 選択**として扱う。tuple indexing の2要素目以降だけが sample / frequency bin / time frame など channel 以外の軸に適用される。

## Mandatory Rules

1. **Wandas-first**: channel selection, sample slicing, spectral slicing は wandas frame の `[]` / `.get_channel()` を使う。NumPy 配列へ変換してから独自に切り出すのは、最終的な数値抽出が必要な場合だけにする。
2. **Method chaining**: selection 後も wandas frame が返るので、`.high_pass_filter(...).normalize().fft()` のようにチェーンを継続する。
3. **Visualization**: selection 結果は `.plot()` / `.describe()` で確認する。`matplotlib` / `plt.plot(frame.data)` による直接描画は禁止。

## API サマリーテーブル

| API | 引数 | 返り値 | 効果 |
|---|---:|---|---|
| `frame[i]` | `int` | same frame type | channel index で1チャンネルを選択。負 index も可 |
| `frame["label"]` | `str` | same frame type | channel label の完全一致で1チャンネルを選択 |
| `frame[start:stop]` | `slice` | same frame type | channel axis を slice |
| `frame[[0, 2]]` | `list[int]` | same frame type | 複数 channel index を選択 |
| `frame[["x", "z"]]` | `list[str]` | same frame type | 複数 channel label を選択 |
| `frame[np.array([0, 2])]` | integer ndarray | same frame type | NumPy integer array で channel 選択 |
| `frame[np.array([True, False, True])]` | boolean ndarray | same frame type | boolean mask で channel 選択。長さは `n_channels` と一致必須 |
| `frame[channel_key, ...]` | tuple | same frame type | 1要素目で channel 選択、2要素目以降で残りの軸を slice |
| `frame.get_channel(channel_idx)` | int/list/tuple/int ndarray/bool ndarray | same frame type | channel index 系の選択 |
| `frame.get_channel(query=...)` | str/regex/callable/dict | same frame type | channel metadata query で選択 |
| `frame.label2index(label)` | str | int | channel label から index を取得 |
| `len(frame)` | none | int | channel 数 |
| `for ch in frame` | none | iterator | 1 channel frame を順番に yield |

## Patterns

### チャンネル番号・ラベル・list で選択する

```python
import numpy as np
import wandas as wd

sr = 16000
data = np.arange(3 * sr, dtype=float).reshape(3, sr)
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["x", "y", "z"])

first = frame[0]
last = frame[-1]
y = frame["y"]
subset_by_index = frame[[0, 2]]
subset_by_label = frame[["x", "z"]]
first_two = frame[0:2]

assert first.n_channels == 1
assert last.labels == ["z"]
assert y.labels == ["y"]
assert subset_by_index.labels == ["x", "z"]
assert subset_by_label.n_channels == 2
assert first_two.labels == ["x", "y"]
```

### NumPy index array と boolean mask で選択する

```python
import numpy as np
import wandas as wd

sr = 8000
data = np.arange(4 * sr, dtype=float).reshape(4, sr)
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["ch0", "ch1", "ch2", "ch3"])

by_array = frame[np.array([1, 3])]
by_mask = frame[np.array([True, False, True, False])]

assert by_array.labels == ["ch1", "ch3"]
assert by_mask.labels == ["ch0", "ch2"]
```

### metadata query で選択する

```python
import re
import numpy as np
import wandas as wd

sr = 8000
data = np.random.default_rng(0).normal(size=(3, sr))
frame = wd.from_numpy(
    data,
    sampling_rate=sr,
    ch_labels=["mic_front", "mic_rear", "acc_x"],
    ch_units=["Pa", "Pa", "m/s^2"],
)

front = frame.get_channel(query="mic_front")
mics = frame.get_channel(query=re.compile(r"^mic_"))
pressure = frame.get_channel(query={"unit": "Pa"})
accel = frame.get_channel(query=lambda ch: ch.label.startswith("acc_"))

assert front.labels == ["mic_front"]
assert mics.labels == ["mic_front", "mic_rear"]
assert pressure.n_channels == 2
assert accel.labels == ["acc_x"]
```

### 秒指定を sample index に変換して時間範囲を切り出す

```python
import numpy as np
import wandas as wd

sr = 16000
data = np.random.default_rng(1).normal(size=(2, sr * 3))
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["left", "right"])

start_sec = 1.0
end_sec = 2.5
start = int(start_sec * frame.sampling_rate)
end = int(end_sec * frame.sampling_rate)

segment = frame[:, start:end]
left_segment = frame["left", start:end]

assert segment.n_channels == 2
assert segment.shape[-1] == end - start
assert left_segment.n_channels == 1
assert left_segment.shape[-1] == end - start
```

### 選択後も wandas chain を継続する

```python
import numpy as np
import wandas as wd

sr = 16000
time = np.arange(sr, dtype=float) / sr
data = np.vstack([
    np.sin(2 * np.pi * 440 * time),
    np.sin(2 * np.pi * 880 * time),
])
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["low", "high"])

spectrum = frame["low"].high_pass_filter(cutoff=100.0).normalize().fft()

assert spectrum.n_channels == 1
assert hasattr(spectrum, "freqs")
```

### STFT / spectrogram の channel, frequency, time slicing

```python
import numpy as np
import wandas as wd

sr = 16000
time = np.arange(sr, dtype=float) / sr
data = np.vstack([
    np.sin(2 * np.pi * 440 * time),
    np.sin(2 * np.pi * 880 * time),
])
frame = wd.from_numpy(data, sampling_rate=sr, ch_labels=["low", "high"])
spec = frame.stft(n_fft=512, hop_length=128)

# tuple の1要素目は channel、2要素目は frequency bin、3要素目は time frame
low_freq_ch0 = spec[0, :20, :]
time_window = spec[:, :, 2:8]

assert low_freq_ch0.n_channels == 1
assert time_window.n_channels == 2
assert hasattr(low_freq_ch0, "freqs")
assert hasattr(time_window, "times")
```

## Common Mistakes

| 間違い | 正しい対応 |
|---|---|
| `frame.loc[...]` / `frame.iloc[...]` を使う | wandas frame は pandas ではない。`frame[...]` または `.get_channel()` を使う |
| `frame[:, 1.0:2.0]` のように秒で slice する | slice は sample index。秒は `int(sec * frame.sampling_rate)` に変換する |
| `frame[[0, "ch1"]]` のように list 内で int と str を混在させる | `list[int]` または `list[str]` に統一する |
| `frame[[]]` で空選択する | 空 list は `ValueError`。必要なら先に候補有無を確認する |
| boolean mask の長さが channel 数と違う | `len(mask) == frame.n_channels` にする |
| `frame["mic"]` が部分一致すると期待する | label selection は完全一致。部分一致・正規表現は `get_channel(query=re.compile(...))` を使う |
| metadata query を `frame[...]` に渡す | dict/callable query は `frame.get_channel(query=...)` を使う |
| `frame[0, 100:200]` 後の `time` が元信号の絶対時刻を保つと期待する | slicing 後の `time` は切り出し frame の先頭を 0 として扱う。元時刻が必要なら offset を別途管理する |
| 単一 channel 選択後の `.data` が常に2Dだと仮定する | 通常 frame の `.data` は単一 channel で channel axis が squeeze される。shape は必要に応じて確認する |
| selection が `operation_history` に残ると期待する | selection は履歴に追加されない。解析レポートには選択条件を明示的に記録する |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — indexing を使ったコピペ可能な選択・切り出しワークフロー
- [`references/indexing_api.md`](references/indexing_api.md) — source に基づく indexing API の詳細仕様
