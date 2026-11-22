"""Estimation automatique du bruit par les trames de faible énergie.

Heuristique DSP hors ligne, pas un détecteur parfait d'absence de parole.
"""
from dataclasses import dataclass

import numpy as np
from scipy.signal import stft, istft

from .audio import AudioData
from .denoise import DenoiseSettings, _stft_parameters, _apply_mask


@dataclass(frozen=True)
class AutoReport:
    applied: bool
    message: str
    selected_frames: int
    total_frames: int
    contrast_db: float
    # Intervalles de trames candidates, pas des silences certifiés.
    candidate_ranges: tuple[tuple[float, float], ...]


def _candidate_ranges(selected, times, frame_seconds, duration):
    ranges = []
    indices = np.flatnonzero(selected)
    if not len(indices): return ()
    first = previous = indices[0]
    for current in indices[1:]:
        if current != previous + 1:
            ranges.append((max(0., times[first]-frame_seconds/2), min(duration, times[previous]+frame_seconds/2)))
            first = current
        previous = current
    ranges.append((max(0., times[first]-frame_seconds/2), min(duration, times[previous]+frame_seconds/2)))
    return tuple(ranges)


def denoise_auto(audio: AudioData, settings: DenoiseSettings | None = None) -> tuple[AudioData, AutoReport]:
    """Estimer le bruit sur tout le fichier sans imposer un silence initial.

    Les trames peu énergétiques de tous les canaux servent à construire un
    masque de sélection commun. Les spectres de bruit restent propres à chaque
    canal. En l'absence de contraste suffisant, conserver l'original plutôt
    que traiter arbitrairement une voix continue comme du bruit.
    """
    settings = settings or DenoiseSettings()
    if audio.duration < .15:
        raise ValueError("L’estimation automatique nécessite au moins 0,15 seconde d’audio.")
    kwargs = _stft_parameters(audio)
    # Énergies sans remplissage aux bords : aucun faux silence créé par padding.
    energies = []
    for channel in range(audio.channels):
        _, times, z = stft(audio.samples[:, channel], **kwargs, boundary=None, padded=False)
        energies.append(np.sum(np.abs(z)**2, axis=0))
    energy = np.mean(energies, axis=0)
    low, high = np.quantile(energy, [.20, .80])
    contrast = float(10*np.log10(max(high, 1e-30)/max(low, 1e-30)))
    threshold = min(float(np.quantile(energy, .35)), float(low + .03*(high-low)))
    selected = energy <= threshold
    ranges = _candidate_ranges(selected, times, kwargs['nperseg']/audio.sample_rate, audio.duration)
    count = int(np.sum(selected))
    total = len(energy)
    reason = None
    if np.max(np.abs(audio.samples)) < 1e-10:
        reason = "Enregistrement silencieux : aucun débruitage nécessaire."
    elif settings.strength == 0 or settings.max_reduction_db == 0:
        reason = "Traitement désactivé par les réglages."
    elif contrast < 3.0 or count < 3:
        reason = "Aucune pause assez distincte n’a été repérée. L’original est conservé pour éviter d’altérer la voix ; essayez le mode manuel."
    if reason:
        return AudioData(audio.samples.copy(), audio.sample_rate), AutoReport(False, reason, count, total, contrast, ranges)

    output = np.empty_like(audio.samples)
    for channel in range(audio.channels):
        _, _, analysis = stft(audio.samples[:, channel], **kwargs, boundary=None, padded=False)
        profile = np.mean(np.abs(analysis[:, selected])**2, axis=1, keepdims=True)
        _, _, full = stft(audio.samples[:, channel], **kwargs, boundary='zeros', padded=True)
        _, restored = istft(_apply_mask(full, profile, settings), **kwargs, input_onesided=True, boundary=True)
        output[:, channel] = restored[:len(audio.samples)]
    message = "Profil estimé automatiquement sur les trames les moins énergétiques de l’ensemble du fichier. Ces passages ne sont pas des silences certifiés."
    if contrast < 6:
        message += " Le contraste est faible : comparez attentivement la voix avant et après."
    return AudioData(output, audio.sample_rate), AutoReport(True, message, count, total, contrast, ranges)
