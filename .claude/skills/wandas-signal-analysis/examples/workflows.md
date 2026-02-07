Wandas Workflow Exampleswandas を使用した典型的な解析コードのパターンです。コード生成の参考にしてください。Example 1: Basic Audio AnalysisWAVファイルを読み込み、波形を確認し、FFTを実行してスペクトルを表示する基本フロー。import wandas as wd
import matplotlib.pyplot as plt

# 1. データの読み込み
signal = wd.read_wav("input_audio.wav")

# 2. 統計情報の確認
signal.describe()

# 3. 前処理とFFT解析（メソッドチェイン）
(
    signal
    .normalize()                  # 正規化
    .low_pass_filter(cutoff=1000) # 1kHz以上をカット
    .fft()                        # FFT変換
    .plot(title="Processed Signal Spectrum") # プロット
)
plt.show()
Example 2: Spectrogram for Anomaly Detection (Time-Frequency)時系列で変化する異音（非定常信号）を特定するためのスペクトログラム解析。import wandas as wd

# 1. CSVデータの読み込み（Time列を指定）
raw_data = wd.read_csv("sensor_log.csv", time_column="Time")

# 2. STFT解析（ハイパスフィルタでDC成分除去後に実行）
spectrogram = (
    raw_data
    .high_pass_filter(cutoff=50)  # 電源ノイズ等の低周波を除去
    .stft(n_fft=2048, hop_length=512, window='hann')
)

# 3. カラーマップを指定して可視化
spectrogram.plot(cmap='inferno', title="Anomaly Detection Spectrogram")
Example 3: Comparison of Filter Effectsフィルタ適用前後の信号を比較するフロー（変数を分けて保持する場合）。import wandas as wd
import matplotlib.pyplot as plt

# 原信号
original = wd.read_wav("noisy_machine.wav")

# フィルタ適用
filtered = original.band_pass_filter(low=100, high=2000)

# 重ねてプロット（wandasはmatplotlib axesを返すため重ね書きが可能）
ax = original.fft().plot(label="Original")
filtered.fft().plot(ax=ax, label="Filtered", title="Filter Effect Comparison")
plt.legend()
plt.show()
