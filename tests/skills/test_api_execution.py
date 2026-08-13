"""Wandas 0.7.2 public-API smoke tests for the repository skills."""

from __future__ import annotations

import numpy as np
import pytest
import wandas as wd


@pytest.fixture
def sig_16k():
    return wd.generate_sin(freqs=440, sampling_rate=16_000, duration=0.5)


@pytest.fixture
def sig_44k():
    return wd.generate_sin(freqs=440.0, sampling_rate=44_100, duration=1.0)


@pytest.fixture
def sig_48k():
    return wd.generate_sin(freqs=1_000, sampling_rate=48_000, duration=1.0)


class TestGettingStarted:
    def test_generate_sin_accepts_integer_frequencies(self, sig_16k):
        assert sig_16k.n_channels == 1
        assert isinstance(sig_16k.data, np.ndarray)

    def test_generate_sin_accepts_frequency_list(self):
        signal = wd.generate_sin(freqs=[440, 880.0], sampling_rate=16_000, duration=0.1)
        assert signal.n_channels == 2

    def test_from_numpy_suppresses_public_singleton_axis(self):
        signal = wd.from_numpy(np.ones((1, 800)), sampling_rate=8_000)
        assert signal.data.shape == (800,)
        assert signal.shape == (800,)

    def test_level_reference_for_pa(self):
        signal = wd.from_numpy(
            np.ones(800) * 2e-5,
            sampling_rate=8_000,
            ch_units="Pa",
        )
        reference = signal.channels[0].level_reference
        assert reference.unit == "dB SPL"
        assert reference.label == "dB SPL re 20 µPa"
        assert reference.to_level(2e-5) == pytest.approx(0.0)
        assert reference.to_level(0.0) == pytest.approx(-240.0)

    def test_astype_and_cache_preserve_concrete_type(self, sig_16k):
        converted = sig_16k.astype("float32")
        cached = converted.cache()
        assert type(cached) is type(sig_16k)
        assert str(cached._data.dtype) == "float32"
        assert any(entry["operation"] == "wandas.frame.astype" for entry in cached.operation_history)

    def test_concat_frame_replaces_frame_add_channel(self):
        left = wd.generate_sin(440, sampling_rate=16_000, duration=0.1).rename_channels({0: "left"})
        right = wd.generate_sin(880, sampling_rate=16_000, duration=0.1).rename_channels({0: "right"})
        combined = left.concat_frame(right)
        assert combined.n_channels == 2
        assert combined.labels == ["left", "right"]

    def test_folder_metadata_select_calibrate_and_cache(self, tmp_path, sig_16k):
        sig_16k.to_wav(tmp_path / "fan_loaded_1500rpm_01.wav")

        def resolve_filename(path):
            machine, state, rpm_text, take = path.stem.split("_")
            return {
                "machine": machine,
                "state": state,
                "rpm": int(rpm_text.removesuffix("rpm")),
                "take": int(take),
            }

        dataset = wd.from_folder(
            str(tmp_path),
            file_extensions=[".wav"],
            metadata_resolver=resolve_filename,
        )
        calibration = wd.ChannelCalibration(factor=0.42, unit="Pa")
        prepared = dataset.select(
            machine="fan", state="loaded", rpm=1_500
        ).apply(lambda frame: frame.with_calibration([calibration]))

        assert len(prepared) == 1
        frame = prepared[0]
        assert frame is not None
        cached = frame.astype("float32").cache()
        assert cached.metadata["take"] == 1
        assert cached.channels[0].level_reference.unit == "dB SPL"


class TestSignalProcessing:
    def test_filter_signatures(self, sig_16k):
        result = (
            sig_16k
            .high_pass_filter(cutoff=100.0)
            .low_pass_filter(cutoff=2_000.0)
            .band_pass_filter(low_cutoff=200.0, high_cutoff=2_000.0)
        )
        assert result.data.shape == sig_16k.data.shape

    def test_sound_level_default_is_linear(self, sig_16k):
        linear = sig_16k.sound_level()
        level = sig_16k.sound_level("A", "Fast", dB=True)
        assert linear.channels[0].unit == sig_16k.channels[0].unit
        assert level.channels[0].unit.startswith("dB")

    def test_rms_trend_level_preserves_reference_label(self):
        pressure = wd.from_numpy(
            np.ones(4_096) * 2e-5,
            sampling_rate=16_000,
            ch_units="Pa",
        )
        trend = pressure.rms_trend(frame_length=512, hop_length=128, dB=True)
        assert trend.channels[0].unit.startswith("dB SPL")

    def test_resampling(self, sig_16k):
        assert sig_16k.resampling(8_000).sampling_rate == 8_000

    def test_loudness_return_types(self, sig_48k):
        pytest.importorskip("mosqito")
        varying = sig_48k.loudness_zwtv(field_type="free")
        steady = sig_48k.loudness_zwst(field_type="free")
        assert isinstance(varying.data, np.ndarray)
        assert isinstance(steady, np.ndarray)
        assert steady.shape == (1,)

    def test_sharpness_stationary_returns_array(self, sig_48k):
        pytest.importorskip("mosqito")
        result = sig_48k.sharpness_din_st(field_type="free")
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,)


class TestSpectralAnalysis:
    def test_fft_welch_stft_shapes(self, sig_16k):
        fft = sig_16k.fft()
        welch = sig_16k.welch(n_fft=512)
        stft = sig_16k.stft(n_fft=512, hop_length=128)
        assert fft.magnitude.ndim == 1
        assert welch.magnitude.ndim == 1
        assert stft.magnitude.ndim == 2

    def test_cepstral_frames(self, sig_16k):
        cepstrum = sig_16k.cepstrum(n_fft=512)
        envelope = cepstrum.lifter(0.002).to_spectral_envelope()
        cepstrogram = sig_16k.stft(n_fft=512).cepstrum()
        assert isinstance(cepstrum, wd.CepstralFrame)
        assert isinstance(envelope, wd.SpectralFrame)
        assert isinstance(cepstrogram, wd.CepstrogramFrame)

    def test_get_frame_at_uses_time_index(self, sig_16k):
        spectrogram = sig_16k.stft(n_fft=512, hop_length=128)
        frame = spectrogram.get_frame_at(0)
        assert isinstance(frame, wd.SpectralFrame)

    def test_noct_spectrum(self, sig_44k):
        pytest.importorskip("mosqito")
        bands = sig_44k.noct_spectrum(fmin=25.0, fmax=8_000.0, n=3)
        assert isinstance(bands, wd.NOctFrame)

    def test_typed_pairwise_results(self):
        left = wd.generate_sin(440, sampling_rate=16_000, duration=1.0).rename_channels({0: "input"})
        right = wd.generate_sin(440, sampling_rate=16_000, duration=1.0).rename_channels({0: "output"})
        combined = left.concat_frame(right)

        coherence = combined.coherence(n_fft=512).select_pair(output=1, input=0)
        csd = combined.csd(n_fft=512).select_pair(output=1, input=0)
        transfer = combined.transfer_function(n_fft=512).select_pair(output=1, input=0)

        assert isinstance(coherence, wd.CoherenceFrame)
        assert isinstance(csd, wd.CrossSpectralFrame)
        assert isinstance(transfer, wd.TransferFunctionFrame)
        assert coherence.coherence.ndim == 1
        assert csd.level_db.ndim == 1
        assert transfer.gain_db.ndim == 1
