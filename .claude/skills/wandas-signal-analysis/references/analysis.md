---
# Wandas — Analysis Reference

周波数領域解析（FFT / PSD）および時間周波数解析（STFT）に関する API と使用上の注意をまとめています。まずは小さなパラメータで試してから本番用パラメータを決定してください。

## 1. Frequency Analysis (FFT / PSD)

- `fft(n_fft: int = None, window: str = 'hann') -> SpectralFrame`
  - 説明: 時間波形（ChannelFrame）を FFT し、周波数スペクトルを返します。
  - 引数:
    - `n_fft`: FFT 長（周波数分解能）。None の場合は信号長に合わせる。
    - `window`: 窓関数（'hann', 'hamming', 'boxcar' 等）。

- `psd(n_fft: int = None, window: str = 'hann') -> SpectralFrame`
  - 説明: パワースペクトル密度（PSD）を計算します。FFT と同様のパラメータを受け取ります。

### 実用メモ

- 周波数分解能は `sampling_rate / n_fft` で決まります。低周波を精細に解析するには大きな `n_fft` を選びますがメモリと計算時間が増えます。
- 長時間信号を窓分割せずに FFT すると時間情報が失われるため、非定常信号には STFT を検討してください。

## 2. Time–Frequency Analysis (STFT)

- `stft(n_fft: int = 2048, hop_length: int = 512, window: str = 'hann') -> SpectrogramFrame`
  - 説明: 短時間フーリエ変換を行いスペクトログラムを返します。異音検出や時間変化の可視化に有効です。
  - 引数:
    - `n_fft`: フレーム長（周波数分解能に影響）。デフォルト 2048。
    - `hop_length`: フレーム間のシフト量（時間分解能に影響）。デフォルト 512。
    - `window`: 窓関数（'hann' 推奨）。

### 実用メモ

- `n_fft` を増やすと周波数分解能は上がるが時間分解能が下がる（トレードオフ）。
- `hop_length` を小さくすると時間分解能が上がるが計算量が増える。

## 3. Visualization Options

`SpectrogramFrame` や `SpectralFrame` の `.plot()` は下記オプションをサポートします。

- `cmap`: カラーマップ（例: 'viridis', 'plasma', 'inferno', 'magma'）
- `yscale`: Y軸スケール（'linear' または 'log'）
- `xscale`: X軸スケール（'linear' または 'log'）
- `vmin`, `vmax`: カラースケールのクリッピング

例:

```python
# STFT の基本例
(
    signal
    .high_pass_filter(20)
    .stft(n_fft=1024, hop_length=256)
    .plot(cmap='jet', title='Spectrogram Analysis')
)
```

## 4. Troubleshooting / Tips

- スペクトログラムがぼやける: `n_fft` を増やすか `hop_length` を小さくしてみる。
- ノイズフロアが高い: 窓関数や平均化（重ね合わせ平均）を検討する。
- メモリエラー: サブサンプリングやチャンク処理、`n_fft` の縮小を検討。

参照: [../examples/workflows.md](../examples/workflows.md) のワークフロー例を参照してください。
