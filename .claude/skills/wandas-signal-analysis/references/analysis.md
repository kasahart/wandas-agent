Wandas Analysis API Reference周波数領域および時間周波数領域の解析に関するAPI仕様です。1. Frequency Analysis (FFT)ChannelFrame から SpectralFrame への変換を行います。.fft(n_fft: int = None, window: str = 'hann') -> SpectralFrame高速フーリエ変換（FFT）を実行し、パワースペクトルを計算します。n_fft: FFT長。Noneの場合はデータ長に合わせます。window: 窓関数の種類（'hann', 'hamming', 'boxcar' 等）。.psd(n_fft: int = None, window: str = 'hann') -> SpectralFrameパワースペクトル密度（PSD）を計算します。2. Time-Frequency Analysis (STFT)ChannelFrame から SpectrogramFrame への変換を行います。.stft(n_fft: int = 2048, hop_length: int = 512, window: str = 'hann') -> SpectrogramFrame短時間フーリエ変換（STFT）を実行し、スペクトログラムデータを生成します。異音解析や非定常信号の解析に最適です。n_fft: フレーム長（周波数分解能に影響）。デフォルトは2048。hop_length: 時間シフト量（時間分解能に影響）。デフォルトは512。window: 窓関数。デフォルトは 'hann'（ハニング窓）。3. Visualization Options for Analysis解析結果の .plot() メソッドには以下のオプションが有効です。cmap: カラーマップ（SpectrogramFrame用）。例: 'viridis', 'plasma', 'jet'。yscale: Y軸のスケール（'linear', 'log'）。xscale: X軸のスケール（'linear', 'log'）。4. Example Usage# STFTの例
(
    signal
    .high_pass_filter(20)
    .stft(n_fft=1024, hop_length=256)
    .plot(cmap='jet', title="Spectrogram Analysis")
)
