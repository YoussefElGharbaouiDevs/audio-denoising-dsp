from pathlib import Path

from streamlit.testing.v1 import AppTest
from audio_dsp.audio import wav_bytes
from audio_dsp.evaluation import synthetic_demo

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_full_demo_flow_and_result_invalidation():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    app.radio[0].set_value('Démonstration synthétique').run()
    assert not app.exception
    assert app.button[0].disabled
    app.checkbox[0].check().run()
    app.button[0].click().run()
    assert not app.exception
    assert 'denoised' in app.session_state
    assert app.session_state['denoised'].sample_rate == 16000
    app.slider[0].set_value(2.0).run()
    assert 'denoised' not in app.session_state
    # Rééchantillonnage indépendant du résultat de débruitage.
    sampling = next(b for b in app.button if b.label == 'Rééchantillonner l’original')
    sampling.click().run()
    assert not app.exception
    assert app.session_state['sampled'].sample_rate == 16000
    app.radio[0].set_value('Importer un fichier').run()
    assert 'sampled' not in app.session_state
    assert not app.exception


def test_bad_noise_selection_blocks_processing():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Démonstration synthétique').run()
    app.number_input[0].set_value(1.).run()
    app.checkbox[0].check().run()
    assert app.button[0].disabled
    assert app.warning
    assert not app.exception


def test_uploaded_wav_processing_and_invalid_file():
    app = AppTest.from_file(APP, default_timeout=30).run()
    _, noisy = synthetic_demo()
    payload, _ = wav_bytes(noisy)
    app.file_uploader[0].set_value(('essai.wav', payload, 'audio/wav')).run()
    assert not app.exception
    app.checkbox[0].check().run()
    app.button[0].click().run()
    assert not app.exception
    assert 'denoised' in app.session_state
    # Un profil modifié doit être écouté et confirmé à nouveau.
    app.number_input[1].set_value(.5).run()
    assert not app.checkbox[0].value
    assert app.button[0].disabled
    app.file_uploader[0].set_value(('invalide.wav', b'not audio', 'audio/wav')).run()
    assert app.error
    assert 'denoised' not in app.session_state
    assert not app.exception
