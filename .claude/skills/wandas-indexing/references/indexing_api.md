# wandas indexing API reference

ソース: `wandas/wandas/core/base_frame.py` at Wandas v0.7.2 / submodule commit `1aed2d9513b7b08f1de3b65576fe4db4005fbeee`.

## `BaseFrame.get_channel(channel_idx=None, query=None, validate_query_keys=True)`

- `channel_idx`: `int | list[int] | tuple[int, ...] | ndarray[int] | ndarray[bool]`
- `query`: `str | re.Pattern | Callable[[ChannelMetadata], bool] | dict[str, Any]`
- `query` が指定された場合、`channel_idx` は使わず query から indices を作る。
- `str` query は label 完全一致。
- `re.Pattern` query は label に対する `search()`。
- callable query は `ChannelMetadata` を受け取り truthy な channel を選ぶ。
- dict query は `ChannelMetadata` の field または channel `extra` key に対する equality / regex 条件。
- match なしは `KeyError`。
- selection は immutable な新しい Frame を返し、`wandas.frame.index` として lineage と `operation_history` に記録する。

## `BaseFrame.__getitem__(key)`

Supported keys:

- `int`: `get_channel(int(key))`
- `str`: `label2index(key)` 後に `get_channel(index)`
- `ndarray[bool]`: mask 長を `n_channels` と照合し、`np.where(mask)[0]` で選択
- `ndarray[int]`: integer array で選択
- `list[str]`: 各 label を `label2index` して選択
- `list[int]`: 複数 index で選択
- `tuple`: `_handle_multidim_indexing(key)`
- `slice`: channel axis を slice

Errors:

- 空 list は `ValueError`。
- mixed-type list は `TypeError`。
- boolean mask 長と `n_channels` が異なる場合は `ValueError`。
- unknown label は `KeyError`。
- unsupported key type は `TypeError`。

## `_handle_multidim_indexing(key)`

- `len(key) > self._data.ndim` は `ValueError`。
- `key[0]` は channel key として再帰的に `self[channel_key]` で処理される。
- `key[1:]` は選択済み Frame の non-channel semantic axes に適用され、すべて `slice` でなければならない。
- time axis は連続forward sliceだけを受け付け、step/reverse sliceは拒否する。
- `frame[channel_key, sample_slice]` や `spec[channel_key, :, time_slice]` のように書く。秒単位ではなく sample / time-frame index を渡す。
- time slice の開始位置は `source_time_offset` に加算される一方、slice後の local `.time` / `.times` は0から始まる。
- `SpectralFrame` / `SpectrogramFrame` は complete canonical one-sided gridを要求するため、frequency-bin部分sliceはconstructor validationで拒否される。

## `.data` と shape の注意

- `.data` は `.compute()` を呼び、Dask graph を materialize する。
- `n_channels == 1` の通常 frame では `.data` が `axis=0` で squeeze される。
- frame を維持して chain を続ける場合は `.data` ではなく frame のまま扱う。

## Spectral frequency range

- 表示範囲だけを絞る: `spectrogram.plot(fmin=20, fmax=8_000)`。
- 数値だけを抽出する: `mask = (spectrum.freqs >= 20) & (spectrum.freqs <= 8_000)` の後、`spectrum.magnitude[..., mask]`。
- 部分frequency gridを持つ `SpectralFrame` / `SpectrogramFrame` は作らない。
