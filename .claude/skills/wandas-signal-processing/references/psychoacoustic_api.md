# Wandas 0.7.2 Psychoacoustic API Reference

ソース: `wandas/wandas/frames/mixins/channel_processing_mixin.py`, `wandas/wandas/processing/psychoacoustic.py`

## Requirements

- `wandas[psychoacoustic]` をインストールする。
- 校正値を必要とする解析では、正しい physical-domain calibration を設定する。
- algorithm が対応する sampling rate を使う。安易な resampling で元データの帯域を作り出せるとは考えない。

## Loudness

```python
.loudness_zwtv(field_type: str = "free") -> ChannelFrame
.loudness_zwst(field_type: str = "free") -> NDArrayReal
```

- `loudness_zwtv`: ISO 532-1:2017 Zwicker time-varying loudness。単位 sone。出力は約 2 ms step の `ChannelFrame`。
- `loudness_zwst`: stationary loudness。shape `(n_channels,)` の ndarray。
- `field_type`: `"free"` または `"diffuse"`。

## Roughness

```python
.roughness_dw(overlap: float = 0.5) -> ChannelFrame
.roughness_dw_spec(overlap: float = 0.5) -> RoughnessFrame
```

- Daniel & Weber 法。
- `roughness_dw`: total roughness time series、単位 asper。
- `roughness_dw_spec`: 47 Bark bands × time の specific roughness、単位 asper/Bark。
- mono `RoughnessFrame.data` は `(47, n_time)`、multi-channel は `(n_channels, 47, n_time)`。
- `R = 0.25 * sum(R'_i)` を Bark axis に沿って集約する。

## Sharpness

```python
.sharpness_din(
    weighting: str = "din",
    field_type: str = "free",
) -> ChannelFrame

.sharpness_din_st(
    weighting: str = "din",
    field_type: str = "free",
) -> NDArrayReal
```

- time-varying は `ChannelFrame`、stationary は shape `(n_channels,)` の ndarray。
- 単位 acum。
- `weighting`: `"din"`, `"aures"`, `"bismarck"`, `"fastl"`。

## Return-type summary

| API | Lazy Frame | `.plot()` | Public data shape |
|---|---|---|---|
| `loudness_zwtv` | yes | yes | mono `(time,)`; multi `(channel, time)` |
| `loudness_zwst` | no | no | `(n_channels,)` |
| `roughness_dw` | yes | yes | mono `(time,)`; multi `(channel, time)` |
| `roughness_dw_spec` | yes | yes | mono `(bark, time)`; multi `(channel, bark, time)` |
| `sharpness_din` | yes | yes | mono `(time,)`; multi `(channel, time)` |
| `sharpness_din_st` | no | no | `(n_channels,)` |

## Common constraints

- steady-state ndarray API は Frame chain や `.plot()` を持たない。
- time axes は Wandas の window/step start convention を使い、外部実装の center convention とずれる場合がある。
- optional dependency error が出た場合は private implementation を直接 import せず、対応 extra を導入する。
