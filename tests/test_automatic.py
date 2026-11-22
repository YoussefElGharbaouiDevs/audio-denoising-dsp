import numpy as np
import pytest

from audio_dsp.audio import AudioData
from audio_dsp.automatic import denoise_auto
from audio_dsp.denoise import DenoiseSettings
from audio_dsp.evaluation import synthetic_demo, snr_db


@pytest.mark.parametrize('kind', ['white', 'colored'])
@pytest.mark.parametrize('seed', [7, 42, 123])
def test_automatic_noise_reduction(kind, seed):
    clean, noisy = synthetic_demo(kind, seed)
    result, report = denoise_auto(noisy)
    active = np.abs(clean.samples[:,0]) > .005
    assert report.applied
    assert snr_db(clean.samples[active], result.samples[active]) > snr_db(clean.samples[active], noisy.samples[active])+1
    assert result.samples.shape == noisy.samples.shape
    assert result.sample_rate == noisy.sample_rate


def test_noise_can_be_only_after_speech():
    rate = 16000
    t = np.arange(rate*3)/rate
    clean = .35*np.sin(2*np.pi*400*t)
    clean[t > 2.] = 0
    noisy = clean + np.random.default_rng(5).normal(0,.04,len(t))
    result, report = denoise_auto(AudioData(noisy, rate))
    assert report.applied
    assert all(start > 1.9 for start, end in report.candidate_ranges)
    assert np.mean(result.samples[round(2.1*rate):]**2) < np.mean(noisy[round(2.1*rate):]**2)*.5
    assert snr_db(clean[:rate], result.samples[:rate,0]) > snr_db(clean[:rate], noisy[:rate])


def test_candidates_cover_before_and_after_speech():
    rate = 16000
    t = np.arange(rate*3)/rate
    clean = .35*np.sin(2*np.pi*400*t)*((t>.75)&(t<2.25))
    noisy = clean + np.random.default_rng(9).normal(0,.03,len(t))
    _, report = denoise_auto(AudioData(noisy, rate))
    assert report.applied
    assert any(end < .75 for start,end in report.candidate_ranges)
    assert any(start > 2.25 for start,end in report.candidate_ranges)


def test_stationary_tone_is_not_mistaken_for_noise():
    t = np.arange(16000)/16000
    audio = AudioData(.3*np.sin(2*np.pi*500*t),16000)
    result, report = denoise_auto(audio)
    assert not report.applied
    np.testing.assert_array_equal(result.samples,audio.samples)


def test_stereo_silence_and_disable():
    audio = AudioData(np.zeros((16000,2)),16000)
    result, report = denoise_auto(audio)
    assert not report.applied
    assert result.channels == 2
    np.testing.assert_array_equal(result.samples,audio.samples)
    _, noisy = synthetic_demo()
    result, report = denoise_auto(noisy,DenoiseSettings(strength=0))
    np.testing.assert_array_equal(result.samples,noisy.samples)


def test_clean_reference_with_silent_pauses_is_unchanged():
    clean, _ = synthetic_demo()
    result, _ = denoise_auto(clean)
    np.testing.assert_allclose(result.samples,clean.samples,atol=1e-12)


def test_short_audio_rejected():
    with pytest.raises(ValueError,match='0,15'):
        denoise_auto(AudioData(np.zeros(100),16000))


def test_speech_on_one_stereo_channel_is_not_cancelled_in_detection():
    clean, noisy = synthetic_demo()
    stereo = AudioData(np.column_stack([noisy.samples[:,0], -noisy.samples[:,0]]), 16000)
    out, report = denoise_auto(stereo)
    assert report.applied
    assert out.samples.shape == stereo.samples.shape
    np.testing.assert_allclose(out.samples[:,0], -out.samples[:,1], atol=1e-12)
