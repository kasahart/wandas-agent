# Wandas 0.7.2 I/O and Core API Reference

ソース: `wandas/wandas/io/read.py`, `wandas/wandas/frames/channel.py`, `wandas/wandas/core/base_frame.py`, `wandas/wandas/core/metadata.py`, `wandas/wandas/utils/frame_dataset.py`

## Contents

1. Unified reading
2. Construction and datasets
3. Frame materialization and reuse
4. Calibration and measurement levels
5. Persistence and compatibility APIs

## Unified reading

```python
wd.read(
    path: str | Path | bytes | bytearray | memoryview | BinaryIO,
    channel: int | list[int] | None = None,
    start: float | None = None,
    end: float | None = None,
    ch_labels: list[str] | None = None,
    time_column: int | str = 0,
    delimiter: str = ",",
    header: int | None = 0,
    file_type: str | None = None,
    source_name: str | None = None,
    timeout: float = 10.0,
) -> ChannelFrame
```

- WAV、CSV、SoundFile 対応音声、HTTP(S)、bytes、binary file-like を受け付ける。
- `channel` は読み込むチャンネル番号、`start` / `end` は秒。
- `file_type` は拡張子推論を上書きする。匿名 bytes は互換既定で WAV として扱う。
- URL/音声は sample decode を遅延する。CSV は shape と sampling rate のため同期 metadata pass を行い、計算時に再度 parse する。
- WDF は明示的に拒否されるため `wd.load()` を使う。
- `normalize` 引数はない。

```python
wd.supported_formats() -> list[str]
```

## Construction and datasets

```python
wd.from_numpy(
    data: NDArrayReal,
    sampling_rate: float,
    label: str | None = None,
    metadata: dict | None = None,
    ch_labels: list[str] | None = None,
    ch_units: list[str] | str | None = None,
) -> ChannelFrame
```

- 1-D は `(1, samples)` へ変換する。2-D は `(channels, samples)`。
- 3-D 以上は `ValueError`。
- `ch_units="Pa"` の既定参照値は 20 µPa。未指定は unit `""`、ref `1.0`。

```python
wd.generate_sin(
    freqs: int | float | list[int | float] = 1000.0,
    sampling_rate: int = 16000,
    duration: float = 1.0,
    label: str | None = None,
) -> ChannelFrame
```

- Python/NumPy の整数・浮動小数を受け付ける。
- 空リスト、非有限、0 以下は `ValueError`。非数値や bool は `TypeError`。

```python
wd.from_folder(
    folder_path: str,
    sampling_rate: int | None = None,
    file_extensions: list[str] | None = None,
    recursive: bool = False,
    lazy_loading: bool = True,
    metadata_resolver: Callable[[Path], Mapping[str, object]] | None = None,
    path_metadata: bool = False,
) -> ChannelFrameDataset
```

Dataset の主要操作:

| API | 効果 |
|---|---|
| `.select(**criteria)` | resolver/path metadata の exact match。Frame は読まない |
| `.apply(func)` | 各 Frame へ任意の変換を適用し、新しい Dataset を返す |
| `.resample(target_sr)` | 全 Frame の遅延 resampling |
| `.trim(start, end)` | 全 Frame の遅延 trim |
| `.normalize(**kwargs)` | 全 Frame の遅延 normalize |
| `.stft(...)` | `SpectrogramFrameDataset` を返す |

`metadata_resolver` と `path_metadata=True` は併用しない。
`with_calibration()`、`astype()`、`cache()` は Frame API。校正は `.apply(...)` で Dataset 全体へ写像できるが、cache は選択・変換後に取り出した個々の Frame へ適用する。

## Frame materialization and reuse

```python
frame.data -> ndarray
frame.cache() -> SameConcreteFrame
frame.astype(dtype) -> SameConcreteFrame
frame.to_tensor(framework="torch", device=None) -> Any
```

- `.data` は校正済み値を materialize する。単チャンネルは singleton channel 軸を省く。
- `.cache()` は raw Dask tensor 全体を同期計算し、同じ具象型の新しい Frame を返す。lineage/Recipe node は増やさない。
- `.astype()` は raw tensor を遅延変換し、lineage/Recipe node を追加する。
- real/integer Frame は `float32` / `float64`、complex Frame は `complex64` / `complex128` だけを出力 dtype として受け付ける。
- `to_tensor()` は `wandas[ml]` が必要で、遅延値を materialize する。

## Calibration and measurement levels

```python
wd.ChannelCalibration(
    factor: float = 1.0,
    unit: str = "",
    ref: float = inferred,
)
```

`factor` は raw sample から物理量への倍率。`unit="Pa"` では `ref=2e-5` を推論する。

```python
frame.with_calibration(
    values: Sequence[float | ChannelCalibration]
          | Mapping[str | int, float | ChannelCalibration]
          | NDArrayReal
) -> ChannelFrame
```

- 数値は factor だけを置換する。
- `ChannelCalibration` は factor、unit、ref をまとめて置換する。
- raw sample は変えず、校正乗算は遅延する。

```python
reference = frame.channels[index].level_reference

reference.reference_value: float
reference.reference_unit: str
reference.unit: str       # "dBFS", "dB SPL", or "dB"
reference.label: str      # canonical display label
reference.to_level(amplitude) -> float | ndarray
```

`to_level()` は `20 * log10(abs(amplitude) / reference)` を使い、ratio floor は `1e-12`。0 は `-240 dB`。入力はすでに linear physical domain にある値であり、calibration factor を再適用しない。

## Persistence and compatibility APIs

```python
frame.save(path, *, compress="gzip", overwrite=False) -> None
wd.load(path) -> BaseFrame
frame.to_wav(path, format=None) -> None
```

- WDF 0.4 は built-in Frame の具象型、軸、校正、metadata、表示履歴を保存する。`wandas[io]` が必要。
- `wd.read_wav(filename, labels=None)` と `wd.read_csv(...)` は互換用。`read_wav()` に `normalize` はない。
- `wd.from_ndarray(...)` は deprecated。新規コードでは `wd.from_numpy()` を使う。
