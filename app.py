"""Interface locale : python -m streamlit run app.py."""
import hashlib
import time

import numpy as np
import streamlit as st

from audio_dsp.audio import AudioData, read_audio, resample_audio, wav_bytes
from audio_dsp.denoise import DenoiseSettings, denoise, noise_segment
from audio_dsp.evaluation import synthetic_demo, snr_db
from audio_dsp.plots import comparison_figure

st.set_page_config(page_title="Audio Lab · DSP", page_icon="🎧", layout="wide")
st.title("Audio Lab")
st.markdown("**Réduire le bruit. Comprendre le signal.**")
st.caption("Projet de vision artificielle · Approche DSP classique · Traitement local, sans deep learning")

with st.sidebar:
    st.header("Votre enregistrement")
    source = st.radio("Source audio", ["Importer un fichier", "Démonstration synthétique"])
    st.caption("WAV ou MP3 · 25 Mo maximum · 120 secondes maximum · mono ou stéréo · 8 à 96 kHz")
    st.markdown("**Parcours**\n\n1. Écouter l’original\n2. Sélectionner du bruit seul\n3. Débruiter et comparer\n4. Télécharger le WAV")
    st.caption("Les fichiers audio restent en mémoire pendant la session. Aucun enregistrement n’est ajouté au dépôt.")

reference = None
audio = None
if source == "Démonstration synthétique":
    kind = st.selectbox("Bruit de démonstration", ["Bruit blanc", "Bruit coloré"])
    reference, audio = synthetic_demo("white" if kind == "Bruit blanc" else "colored")
    source_id = "demo-" + kind
    st.info("Signal harmonique modulé, pas une voix réelle. De 0 à 0,6 s, il contient uniquement du bruit. La référence propre permet de mesurer le SNR.")
else:
    uploaded = st.file_uploader("Choisir un enregistrement vocal", type=["wav", "mp3"], key="audio_upload")
    if uploaded is not None:
        payload = uploaded.getvalue()
        source_id = hashlib.sha256(payload).hexdigest()
        try:
            # Cache limité à la session, invalidé à chaque nouveau fichier.
            if st.session_state.get("decoded_id") != source_id:
                st.session_state["decoded_audio"] = read_audio(payload)
                st.session_state["decoded_id"] = source_id
            audio = st.session_state["decoded_audio"]
        except ValueError as exc:
            st.error(str(exc))

if audio is None:
    for key in ("source_id", "denoised", "denoise_key", "sampled", "sample_key", "decoded_id", "decoded_audio"):
        st.session_state.pop(key, None)
    st.info("Importez un fichier pour commencer, ou choisissez la démonstration synthétique dans la barre latérale.")
    with st.expander("Comment fonctionne le débruitage ?"):
        st.write("Une courte portion de bruit sert à estimer son spectre. Une soustraction spectrale atténue ensuite les composantes associées au bruit, puis le signal est reconstruit. Cette méthode fonctionne surtout sur le souffle et les bruits continus.")
    st.stop()

if st.session_state.get("source_id") != source_id:
    for key in ("denoised", "denoise_key", "sampled", "sample_key", "noise_start", "noise_end", "confirm_noise"):
        st.session_state.pop(key, None)
    st.session_state["source_id"] = source_id

def player(data, label):
    encoded, gain = wav_bytes(data)
    st.markdown(f"**{label}**")
    st.audio(encoded, format="audio/wav")
    if gain < .99999:
        st.caption(f"Gain de sécurité à l’export : {20*np.log10(gain):.2f} dB pour éviter l’écrêtage.")
    return encoded


c1, c2, c3 = st.columns(3)
c1.metric("Durée", f"{audio.duration:.2f} s")
c2.metric("Échantillonnage", f"{audio.sample_rate:,} Hz".replace(",", " "))
c3.metric("Canaux", "Mono" if audio.channels == 1 else "Stéréo conservée")
original_wav = player(audio, "Enregistrement original")
channel = st.selectbox("Canal affiché dans les graphiques", list(range(audio.channels)), format_func=lambda i: "Mono" if audio.channels == 1 else ["Gauche", "Droit"][i])
tab_denoise, tab_sampling, tab_method = st.tabs(["Débruitage", "Échantillonnage", "Méthode et limites"])

with tab_denoise:
    st.subheader("1 · Définir le profil de bruit")
    st.write("Choisissez un passage sans parole, contenant le bruit à atténuer. Au moins 0,15 s ; idéalement 0,5 à 1 s.")
    if audio.duration < .15:
        st.warning("Ce fichier est trop court pour estimer un profil de bruit. Importez un extrait plus long.")
    else:
        def reset_confirmation():
            st.session_state["confirm_noise"] = False

        c1, c2 = st.columns(2)
        start = c1.number_input("Début (secondes)", min_value=0., max_value=audio.duration, value=0., step=.05, format="%.3f", key="noise_start", on_change=reset_confirmation)
        end = c2.number_input("Fin (secondes)", min_value=0., max_value=audio.duration, value=min(.6, audio.duration), step=.05, format="%.3f", key="noise_end", on_change=reset_confirmation)
        selection = None
        try:
            selection = noise_segment(audio, start, end)
            player(AudioData(selection, audio.sample_rate), "Écouter le passage sélectionné")
            if np.max(abs(selection)) < 1e-7:
                st.warning("Ce passage est presque silencieux : il ne fournit pas de profil de bruit représentatif.")
        except ValueError as exc:
            st.warning(str(exc))
        confirmed = st.checkbox("J’ai écouté le passage et il contient uniquement du bruit, sans parole.", key="confirm_noise")
        st.subheader("2 · Régler et traiter")
        c1, c2 = st.columns(2)
        strength = c1.slider("Intensité de soustraction", 0., 4., 1.5, .1, help="0 désactive le traitement. Une valeur élevée risque d’altérer la voix.")
        reduction = c2.slider("Atténuation maximale du masque (dB)", 0, 36, 18, 1)
        current_key = (source_id, start, end, strength, reduction)
        if st.session_state.get("denoise_key") != current_key:
            st.session_state.pop("denoised", None)
        if st.button("Débruiter l’enregistrement", type="primary", disabled=selection is None or not confirmed):
            try:
                with st.spinner("Analyse spectrale et reconstruction…"):
                    begin = time.perf_counter()
                    result = denoise(audio, start, end, DenoiseSettings(strength, reduction))
                    st.session_state["denoised"] = result
                    st.session_state["elapsed"] = time.perf_counter()-begin
                    st.session_state["denoise_key"] = current_key
            except ValueError as exc:
                st.error(str(exc))
        if "denoised" in st.session_state:
            result = st.session_state["denoised"]
            st.subheader("3 · Comparer le résultat")
            encoded = player(result, "Enregistrement débruité")
            st.caption(f"Traitement : {st.session_state['elapsed']:.3f} s · fréquence et canaux conservés · export WAV PCM 16 bits")
            if reference is not None:
                active = np.abs(reference.samples[:,0]) > .005
                before_snr = snr_db(reference.samples[active], audio.samples[active])
                after_snr = snr_db(reference.samples[active], result.samples[active])
                left, right = st.columns(2)
                left.metric("SNR avant · référence synthétique", f"{before_snr:.2f} dB")
                right.metric("SNR après · référence synthétique", f"{after_snr:.2f} dB", f"{after_snr-before_snr:+.2f} dB")
                st.caption("Mesure sur les échantillons actifs de la référence. Elle ne remplace pas une évaluation sur de vraies voix.")
            st.pyplot(comparison_figure(audio, result, channel))
            st.caption("Même échelle d’amplitude et même échelle de couleur pour les deux versions. Comparez aussi l’intelligibilité et les artefacts à l’écoute.")
            st.download_button("Télécharger le WAV débruité", encoded, "audio_debruite.wav", "audio/wav")

with tab_sampling:
    st.subheader("Explorer la fréquence d’échantillonnage")
    st.write("Cette expérience utilise l’original, indépendamment du débruitage. La durée et la hauteur sont conservées grâce à un véritable rééchantillonnage avec filtrage anti-repliement.")
    target = st.selectbox("Fréquence cible (Hz)", [8000, 16000, 22050, 44100, 48000], index=1)
    sample_key = (source_id, target)
    if st.session_state.get("sample_key") != sample_key:
        st.session_state.pop("sampled", None)
    if st.button("Rééchantillonner l’original"):
        try:
            st.session_state["sampled"] = resample_audio(audio, target)
            st.session_state["sample_key"] = sample_key
        except ValueError as exc:
            st.error(str(exc))
    if "sampled" in st.session_state:
        result = st.session_state["sampled"]
        encoded = player(result, f"Version à {target} Hz")
        a, b, c = st.columns(3)
        a.metric("Fréquence de Nyquist", f"{target/2000:g} kHz")
        b.metric("WAV original · 16 bits", f"{len(original_wav)/1e6:.2f} Mo")
        c.metric("WAV rééchantillonné · 16 bits", f"{len(encoded)/1e6:.2f} Mo")
        st.caption("La bande utile reste légèrement sous la fréquence de Nyquist. Les tailles comparées utilisent le même encodage PCM 16 bits et le même nombre de canaux.")
        if target > audio.sample_rate:
            st.info("Augmenter la fréquence ne recrée pas les détails absents de l’enregistrement initial.")
        st.pyplot(comparison_figure(audio, result, channel))
        st.download_button("Télécharger le WAV rééchantillonné", encoded, f"audio_{target}Hz.wav", "audio/wav")

with tab_method:
    st.subheader("Une méthode DSP explicable")
    st.markdown("""
1. **STFT** : fenêtre de Hann de 32 ms et recouvrement de 75 %.
2. **Profil de bruit** : moyenne de la puissance spectrale du passage sélectionné.
3. **Soustraction spectrale** : masque de gain avec plancher d’atténuation.
4. **Lissage** : 3 cases fréquentielles et 5 trames temporelles.
5. **Reconstruction** : phase conservée, STFT inverse, durée et canaux conservés.

Le traitement est adapté surtout aux bruits continus. Une sélection contenant de la parole peut dégrader la voix. Une forte réduction peut produire un son métallique. Le système ne sépare ni plusieurs locuteurs ni les instruments.

Sans référence propre, nous ne présentons pas de gain de SNR calculé sur une voix réelle. Une réduction visible du spectrogramme ne prouve pas à elle seule une amélioration.

**Confidentialité** : traitement local, fichiers en mémoire, aucune API audio externe. La première version limite les fichiers à 12 millions de valeurs audio en plus des limites de durée et de taille.
""")
