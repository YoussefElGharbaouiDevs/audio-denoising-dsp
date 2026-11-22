from pathlib import Path

from streamlit.testing.v1 import AppTest
from audio_dsp.audio import wav_bytes
from audio_dsp.evaluation import synthetic_demo

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_full_demo_flow_and_result_invalidation():
    app = AppTest.from_file(APP, default_timeout=30).run()
    next(w for w in app.radio if w.label == 'Source audio').set_value('Démonstration synthétique').run()
    assert not app.exception
    assert 'denoised' in app.session_state  # Aucun clic de traitement nécessaire.
    assert not app.checkbox
    old_key = app.session_state['denoise_key']
    app.slider[0].set_value(2.0).run()
    assert not app.exception
    assert 'denoised' in app.session_state
    assert app.session_state['denoise_key'] != old_key
    next(b for b in app.button if b.label == 'Rééchantillonner l’original').click().run()
    assert not app.exception
    assert app.session_state['sampled'].sample_rate == 16000
    next(w for w in app.radio if w.label == 'Source audio').set_value('Importer un fichier').run()
    assert 'sampled' not in app.session_state
    assert 'denoised' not in app.session_state


def test_bad_noise_selection_blocks_processing():
    app = AppTest.from_file(APP, default_timeout=30).run()
    next(w for w in app.radio if w.label == 'Source audio').set_value('Démonstration synthétique').run()
    next(w for w in app.radio if w.label == 'Mode de débruitage').set_value('Manuel — plusieurs passages').run()
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
    assert 'denoised' in app.session_state
    assert app.session_state['auto_report'].applied
    next(w for w in app.radio if w.label == 'Mode de débruitage').set_value('Manuel — plusieurs passages').run()
    assert 'denoised' not in app.session_state
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label == 'Débruiter l’enregistrement').click().run()
    assert 'denoised' in app.session_state
    app.number_input[1].set_value(.5).run()
    assert not app.checkbox[0].value
    assert next(b for b in app.button if b.label == 'Débruiter l’enregistrement').disabled
    app.file_uploader[0].set_value(('invalide.wav', b'not audio', 'audio/wav')).run()
    assert app.error
    assert 'denoised' not in app.session_state
    assert not app.exception


def test_manual_multiple_ranges():
    app = AppTest.from_file(APP, default_timeout=30).run()
    next(w for w in app.radio if w.label == 'Source audio').set_value('Démonstration synthétique').run()
    next(w for w in app.radio if w.label == 'Mode de débruitage').set_value('Manuel — plusieurs passages').run()
    next(w for w in app.selectbox if w.label == 'Nombre de passages de bruit').set_value(2).run()
    assert len(app.number_input) == 4
    app.number_input[2].set_value(3.7).run()
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label == 'Débruiter l’enregistrement').click().run()
    assert not app.exception
    assert 'denoised' in app.session_state


def test_new_upload_does_not_reuse_previous_automatic_result():
    app = AppTest.from_file(APP, default_timeout=30).run()
    for kind in ('white', 'colored'):
        _, noisy = synthetic_demo(kind)
        payload, _ = wav_bytes(noisy)
        app.file_uploader[0].set_value((kind+'.wav',payload,'audio/wav')).run()
        assert not app.exception
        assert app.session_state['denoise_key'][0] == app.session_state['source_id']
        if kind == 'white': first = app.session_state['denoised'].samples.copy()
    import numpy as np
    assert not np.array_equal(first, app.session_state['denoised'].samples)
