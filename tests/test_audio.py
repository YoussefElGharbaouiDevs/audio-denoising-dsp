from io import BytesIO

import numpy as np
import pytest
import soundfile as sf

from audio_dsp.audio import AudioData, read_audio, resample_audio, wav_bytes


def test_stereo_wav_round_trip():
    t = np.arange(1600) / 16000
    x = np.column_stack((.4 * np.sin(2*np.pi*440*t), .2*np.cos(2*np.pi*900*t)))
    encoded, gain = wav_bytes(AudioData(x, 16000))
    decoded = read_audio(encoded)
    assert decoded.channels == 2 and decoded.sample_rate == 16000
    assert gain == 1
    np.testing.assert_allclose(decoded.samples, x, atol=1/32768)


def test_downsampling_suppresses_frequencies_above_new_nyquist():
    rate = 48000
    t = np.arange(rate) / rate
    low = AudioData(np.sin(2*np.pi*1000*t), rate)
    high = AudioData(np.sin(2*np.pi*10000*t), rate)
    low_y = resample_audio(low, 8000).samples[100:-100]
    high_y = resample_audio(high, 8000).samples[100:-100]
    assert np.sqrt(np.mean(low_y**2)) > .69
    assert np.sqrt(np.mean(high_y**2)) < .005


def test_resampling_preserves_duration_channels_and_tone():
    t = np.arange(44100) / 44100
    x = np.column_stack([np.sin(2*np.pi*440*t), np.sin(2*np.pi*880*t)]) * .2
    out = resample_audio(AudioData(x, 44100), 16000)
    assert out.samples.shape == (16000, 2)
    assert out.duration == 1
    peak = np.argmax(abs(np.fft.rfft(out.samples[:, 0])))
    assert peak == 440


@pytest.mark.parametrize('data', [b'', b'not audio'])
def test_invalid_files_are_rejected(data):
    with pytest.raises(ValueError): read_audio(data)


def test_export_reduces_gain_instead_of_clipping():
    encoded, gain = wav_bytes(AudioData(np.array([0., 2., -2.]), 16000))
    y = read_audio(encoded).samples[:, 0]
    assert .49 < gain < .5
    assert np.max(abs(y)) < 1
    np.testing.assert_allclose(y, np.array([0., 2., -2.])*gain, atol=1/32768)


def test_float_wav_with_nonfinite_values_is_rejected():
    buf = BytesIO()
    sf.write(buf, [0., np.nan], 16000, format='WAV', subtype='FLOAT')
    with pytest.raises(ValueError, match='non finies'): read_audio(buf.getvalue())


def test_metadata_limits_before_decoding():
    buf = BytesIO()
    sf.write(buf, np.zeros((100, 3)), 16000, format='WAV')
    with pytest.raises(ValueError, match='mono ou stéréo'): read_audio(buf.getvalue())


@pytest.mark.parametrize('rate', [0, 7999, 96001, 16000.5])
def test_invalid_target_rate(rate):
    with pytest.raises(ValueError): resample_audio(AudioData(np.zeros(1000), 16000), rate)
