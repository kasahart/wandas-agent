"""
wandas API 実行テスト

各スキルに記載されているコードスニペットが実際に動くことを確認する。
API シグネチャの変更やメソッドの削除を早期検出するためのテスト。
"""
import numpy as np
import pytest
import wandas as wd


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sig_16k():
    return wd.generate_sin(freqs=440.0, sampling_rate=16000, duration=0.5)


@pytest.fixture
def sig_44k():
    return wd.generate_sin(freqs=440.0, sampling_rate=44100, duration=1.0)


@pytest.fixture
def sig_48k():
    """心理音響メソッドは 48kHz が必要"""
    return wd.generate_sin(freqs=1000.0, sampling_rate=48000, duration=1.0)


# ---------------------------------------------------------------------------
# wandas-getting-started: I/O・フレーム型
# ---------------------------------------------------------------------------

class TestGettingStarted:
    def test_generate_sin_returns_ndarray(self, sig_16k):
        """.data は NumPy ndarray を直接返す（.compute() 不要）"""
        assert isinstance(sig_16k.data, np.ndarray)

    def test_generate_sin_requires_float_freqs(self):
        """freqs に int を渡すと ValueError になる"""
        with pytest.raises(ValueError):
            wd.generate_sin(freqs=440, sampling_rate=44100, duration=0.5)

    def test_from_numpy(self):
        data = np.random.randn(1, 8000)
        sig = wd.ChannelFrame.from_numpy(data, sampling_rate=16000)
        assert isinstance(sig.data, np.ndarray)
        assert sig.sampling_rate == 16000

    def test_channel_frame_properties(self, sig_16k):
        assert hasattr(sig_16k, "sampling_rate")
        assert hasattr(sig_16k, "n_channels")
        assert hasattr(sig_16k, "duration")
        assert hasattr(sig_16k, "labels")

    def test_ch_units_pa(self):
        """ch_units=['Pa'] で物理単位を設定できる（ch_refs パラメータは存在しない）"""
        sig = wd.ChannelFrame.from_numpy(
            np.random.randn(1, 16000),
            sampling_rate=16000,
            ch_units=["Pa"],
        )
        assert sig is not None


# ---------------------------------------------------------------------------
# wandas-signal-processing: フィルタ・音圧・心理音響
# ---------------------------------------------------------------------------

class TestSignalProcessing:
    def test_high_pass_filter(self, sig_16k):
        result = sig_16k.high_pass_filter(cutoff=100.0)
        assert isinstance(result.data, np.ndarray)

    def test_low_pass_filter(self, sig_16k):
        result = sig_16k.low_pass_filter(cutoff=2000.0)
        assert isinstance(result.data, np.ndarray)

    def test_band_pass_filter_uses_low_high_cutoff(self, sig_16k):
        """引数名は low_cutoff / high_cutoff（low / high ではない）"""
        result = sig_16k.band_pass_filter(low_cutoff=200.0, high_cutoff=2000.0)
        assert isinstance(result.data, np.ndarray)

    def test_sound_level_default_is_not_db(self, sig_16k):
        """sound_level() のデフォルトは dB=False（線形スケール）"""
        sl = sig_16k.sound_level()
        assert sl is not None

    def test_sound_level_with_db(self, sig_16k):
        sl = sig_16k.sound_level(freq_weighting="A", time_weighting="Fast", dB=True)
        assert sl is not None

    def test_normalize(self, sig_16k):
        result = sig_16k.normalize()
        assert np.max(np.abs(result.data)) <= 1.0 + 1e-6

    def test_resampling(self, sig_16k):
        result = sig_16k.resampling(8000)
        assert result.sampling_rate == 8000

    # 心理音響（48kHz 必須）

    def test_loudness_zwtv_returns_frame(self, sig_48k):
        loudness = sig_48k.loudness_zwtv(field_type="free")
        assert isinstance(loudness.data, np.ndarray)

    def test_loudness_zwst_returns_ndarray_not_frame(self, sig_48k):
        """.loudness_zwst() は ChannelFrame ではなく NDArrayReal を返す"""
        result = sig_48k.loudness_zwst(field_type="free")
        assert isinstance(result, np.ndarray)

    def test_sharpness_din_st_returns_ndarray_not_frame(self, sig_48k):
        """.sharpness_din_st() は ChannelFrame ではなく NDArrayReal を返す"""
        result = sig_48k.sharpness_din_st(field_type="free")
        assert isinstance(result, np.ndarray)

    def test_roughness_dw_returns_frame(self, sig_48k):
        result = sig_48k.roughness_dw()
        assert result is not None


# ---------------------------------------------------------------------------
# wandas-spectral-analysis: スペクトル変換
# ---------------------------------------------------------------------------

class TestSpectralAnalysis:
    def test_fft_has_freqs(self, sig_16k):
        spec = sig_16k.fft()
        assert hasattr(spec, "freqs")

    def test_welch_has_freqs(self, sig_16k):
        spec = sig_16k.welch()
        assert hasattr(spec, "freqs")

    def test_stft_has_freqs_and_times(self, sig_16k):
        spec = sig_16k.stft()
        assert hasattr(spec, "freqs")
        assert hasattr(spec, "times")

    def test_noct_spectrum(self, sig_44k):
        noct = sig_44k.noct_spectrum(fmin=25.0, fmax=8000.0, n=3)
        assert hasattr(noct, "freqs")

    def test_spectral_frame_properties(self, sig_16k):
        spec = sig_16k.fft()
        assert hasattr(spec, "freqs")
        assert hasattr(spec, "magnitude")
        assert hasattr(spec, "power")
