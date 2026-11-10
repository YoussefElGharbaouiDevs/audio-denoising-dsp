import numpy as np
import pytest

from audio_dsp.audio import AudioData
from audio_dsp.denoise import DenoiseSettings, denoise
from audio_dsp.evaluation import synthetic_demo, snr_db


@pytest.mark.parametrize('kind', ['white', 'colored'])
@pytest.mark.parametrize('seed', [7, 42, 123])
def test_reduction_on_controlled_signals(kind, seed):
    clean, noisy = synthetic_demo(kind, seed)
    original = noisy.samples.copy()
    result = denoise(noisy, 0, .6)
    active = np.abs(clean.samples[:, 0]) > .005
    before = snr_db(clean.samples[active], noisy.samples[active])
    after = snr_db(clean.samples[active], result.samples[active])
    assert after > before + 1
    assert np.mean(result.samples[:8000]**2) < np.mean(noisy.samples[:8000]**2)*.5
    assert result.samples.shape == noisy.samples.shape
    np.testing.assert_array_equal(noisy.samples, original)


def test_zero_strength_is_exact_bypass():
    _, noisy = synthetic_demo()
    result = denoise(noisy, 0, .6, DenoiseSettings(strength=0))
    np.testing.assert_array_equal(noisy.samples, result.samples)


def test_silence_stays_finite_and_silent():
    result = denoise(AudioData(np.zeros(16000), 16000), 0, .5)
    np.testing.assert_array_equal(result.samples, 0)


def test_clean_audio_with_silent_profile_is_preserved():
    clean, _ = synthetic_demo()
    out = denoise(clean, 0, .6)
    np.testing.assert_allclose(out.samples, clean.samples, atol=1e-12)


def test_stereo_channels_are_processed_independently():
    _, a = synthetic_demo('white', 1)
    _, b = synthetic_demo('colored', 2)
    stereo = AudioData(np.column_stack([a.samples[:, 0], b.samples[:, 0]]), 16000)
    out = denoise(stereo, 0, .6)
    assert out.channels == 2
    np.testing.assert_allclose(out.samples[:, 0], denoise(a, 0, .6).samples[:, 0])
    np.testing.assert_allclose(out.samples[:, 1], denoise(b, 0, .6).samples[:, 0])


@pytest.mark.parametrize('start,end', [(-1,.5),(0,9),(.4,.3),(0,.1),(float('nan'),.5)])
def test_invalid_noise_interval(start, end):
    _, noisy = synthetic_demo()
    with pytest.raises(ValueError): denoise(noisy, start, end)


def test_minimum_length_clip_and_nonstandard_rate():
    x = np.random.default_rng(0).normal(0,.05,1654)
    out = denoise(AudioData(x,11025),0,len(x)/11025)
    assert len(out.samples) == len(x)
    assert np.isfinite(out.samples).all()


@pytest.mark.parametrize('settings', [{'strength':-1}, {'strength':np.nan}, {'max_reduction_db':37}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError): DenoiseSettings(**settings)
