---
name: wandas-getting-started
description: Use when starting with Wandas 0.7.2, reading audio or sensor data from files, URLs, bytes, or streams, creating ChannelFrames from NumPy arrays, loading WDF artifacts, working with folder datasets, understanding lazy immutable Frame behavior, configuring channel calibration, or converting linear measurements with LevelReference.
---

# Wandas: Getting Started

Wandas は音声・振動・センサ波形を、サンプリングレート、チャンネル名、単位、校正、履歴と一緒に扱う Frame API。公開例では統合入口の `wd.read()` と `wd.from_numpy()` を優先する。

## Mandatory Rules

1. **Wandas-first**: 読み込み・信号変換・解析は Wandas の公開 API を使う。互換 API の `read_wav()` / `read_csv()` / `from_ndarray()` は既存コードの保守に限る。
2. **Lazy and immutable**: Frame 操作は Dask グラフを持つ新しい Frame を返す。`.data`、統計プロパティ、plot、`cache()` などが計算境界になる。
3. **Visualization**: `.plot()` / `.describe()` を使い、`plt.plot(frame.data)` のようにデータを直接描画しない。
4. **Calibration before levels**: SPL や物理量レベルを計算する前に、チャンネルの `unit`、`ref`、校正係数を確認する。`normalize()` したデータを校正値として扱わない。

## Top-level API

| API | 主要引数 | 返り値 | 用途 |
|---|---|---|---|
| `wd.read` | `(path, channel=None, start=None, end=None, ch_labels=None, time_column=0, delimiter=",", header=0, file_type=None, source_name=None, timeout=10.0)` | `ChannelFrame` | WAV/CSV/対応音声、URL、bytes、file-like を統一的に読む |
| `wd.from_numpy` | `(data, sampling_rate, label=None, metadata=None, ch_labels=None, ch_units=None)` | `ChannelFrame` | 1-D または channel-first 2-D 配列から作る |
| `wd.from_folder` | `(folder_path, sampling_rate=None, file_extensions=None, recursive=False, lazy_loading=True, metadata_resolver=None, path_metadata=False)` | `ChannelFrameDataset` | 複数ファイルを遅延データセットとして扱う |
| `wd.load` | `(path)` | 保存された具象 Frame | WDF 0.4 を読む。`wd.read()` は使わない |
| `wd.supported_formats` | `()` | `list[str]` | 登録済み reader の拡張子を確認する |
| `wd.generate_sin` | `(freqs=1000.0, sampling_rate=16000, duration=1.0, label=None)` | `ChannelFrame` | 正の実数スカラーまたはリストからテスト信号を作る |

`wd.read()` に `normalize` 引数はない。データ自体を正規化する場合は、読み込み後に `.normalize()` を明示する。`describe(normalize=True)` は再生表示だけを正規化し、解析対象は変更しない。

## Frame Types

| Frame | ドメイン | 主な生成元 |
|---|---|---|
| `ChannelFrame` | 時間 | `wd.read()`, `wd.from_numpy()` |
| `SpectralFrame` | 周波数 | `.fft()`, `.welch()` |
| `SpectrogramFrame` | 時間×周波数 | `.stft()` |
| `NOctFrame` | 1/N オクターブ | `.noct_spectrum()` |
| `CepstralFrame` | ケフレンシ | `.cepstrum()` |
| `CepstrogramFrame` | 時間×ケフレンシ | `.stft().cepstrum()` |
| `CoherenceFrame` | チャンネルペア×周波数 | `.coherence()` |
| `CrossSpectralFrame` | チャンネルペア×周波数 | `.csd()` |
| `TransferFunctionFrame` | チャンネルペア×周波数 | `.transfer_function()` |
| `RoughnessFrame` | Bark×時間 | `.roughness_dw_spec()` |

## Core Frame Contract

| API | 型・返り値 | 意味 |
|---|---|---|
| `.data` | `ndarray` | 校正適用済み値を計算する。単チャンネルでは先頭の singleton 軸を省く |
| `.channels` | `list[ChannelMetadata]` | ラベル、校正、単位、参照値をチャンネルごとに保持する |
| `.operation_history` | `list[dict]` | lineage から導出される互換表示 |
| `.previous` | `Frame | None` | 直前の receiver への process-local 参照 |
| `.astype(dtype)` | 同じ具象 Frame | raw tensor の dtype を遅延変換する |
| `.cache()` | 同じ具象 Frame | bounded な raw tensor 全体を同期計算し、メモリ上で再利用する |
| `.to_tensor(framework, device=None)` | framework tensor | `wandas[ml]` を使って PyTorch/TensorFlow に変換する |

`cache()` はローカルメモリへ全量を載せる。収まるデータだけに使い、精度を下げてよい場合は `.astype("float32").cache()` の順にする。

## Patterns

### ファイルを統一 API で読む

```python
import wandas as wd

recording = wd.read("recording.wav", channel=0, start=0.25, end=1.25)
sensor = wd.read("sensor.csv", time_column="Time")

print(recording.sampling_rate, recording.duration, recording.labels)
recording.describe(fmin=20, fmax=8_000)
```

### NumPy データへ物理単位を付ける

```python
import numpy as np
import wandas as wd

sr = 48_000
t = np.arange(sr) / sr
pressure_pa = 0.02 * np.sin(2 * np.pi * 1_000 * t)

frame = wd.from_numpy(
    pressure_pa,
    sampling_rate=sr,
    ch_labels=["mic"],
    ch_units="Pa",
)
```

`ch_units="Pa"` は単位と既定参照値 20 µPa を設定する。センサ係数が必要なら `with_calibration()` へ `wd.ChannelCalibration(factor=..., unit=..., ref=...)` を渡す。

### v0.7.2 の測定レベル参照を使う

```python
reference = frame.channels[0].level_reference
rms_pa = frame.rms[0]
rms_db = reference.to_level(rms_pa)

print(reference.reference_value)  # 2e-5
print(reference.reference_unit)   # Pa
print(reference.unit)             # dB SPL
print(reference.label)            # dB SPL re 20 µPa
print(rms_db)
```

SoundFile-backed audio は canonical full-scale の `FS` / reference 1 として読み込まれ、level unit は `dBFS` になる。`from_numpy()`、CSV、identity calibration は単位指定がなければ generic `dB re 1 input unit` のまま。

### フォルダメタデータで選択してから処理する

```python
import wandas as wd

dataset = wd.from_folder("recordings", recursive=True, path_metadata=True)
selected = dataset.select(partition_0="group_a")
features = selected.resample(16_000).trim(0, 5).normalize().stft(n_fft=512)
```

`select()` はファイルメタデータだけで絞り込み、波形を読まない。Hive-style の `group=group_a` ディレクトリでは key は `group` になる。

ファイル名を解析する場合は `metadata_resolver(relative_path: Path) -> Mapping` を渡す。`with_calibration()`、`astype()`、`cache()` は Frame API であり Dataset へ直接は呼べない。全要素への校正などは `dataset.apply(lambda frame: frame.with_calibration(...))`、cache は絞り込み・切り出し後の個々の Frame に対して行う。

### 計算済み結果を再利用する

```python
spectrogram = frame.stft(n_fft=2_048, hop_length=512)
cached = spectrogram.astype("complex64").cache()

levels = cached.dB
magnitude = cached.abs()
```

## Common Mistakes

| 間違い | 正解 |
|---|---|
| `wd.read("audio.wav", normalize=True)` | `wd.read("audio.wav").normalize()`。ただし校正解析では正規化しない |
| 新規コードで `wd.read_wav()` / `wd.read_csv()` | `wd.read()` を優先する |
| `wd.read("analysis.wdf")` | `wd.load("analysis.wdf")` |
| `frame.data.compute()` | `.data` はすでに NumPy 配列を返す |
| `.data` は常に `(channels, samples)` | 単チャンネル public data は `(samples,)`。`shape` も singleton channel 軸を省く |
| `wd.generate_sin(freqs=440)` は無効 | Python/NumPy の整数・浮動小数を受け付ける。正かつ有限であること |
| `add_channel(other_frame)` | Frame 同士は `.concat_frame(other_frame)`。`add_channel()` は1本の NumPy/Dask 配列用 |
| `cache()` は分散 cache | ローカル process の全量同期計算。eviction や capacity 制御はない |
| WAV を正規化してから SPL と呼ぶ | Pa 校正済みの元データから計算する |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — I/O、校正、dataset、cache の実行パターン
- [`references/io_api.md`](references/io_api.md) — v0.7.2 I/O・Frame・measurement-level API
