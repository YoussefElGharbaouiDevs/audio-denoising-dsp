"""Soustraction spectrale de puissance avec plancher et lissage du masque.

Aucun modèle appris. Le profil est explicitement fourni par l'utilisateur.
"""
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter
from scipy.signal import stft, istft

from .audio import AudioData


@dataclass(frozen=True)
class DenoiseSettings:
    strength: float = 1.5
    max_reduction_db: float = 18.0

    def __post_init__(self):
        if not np.isfinite(self.strength) or not 0 <= self.strength <= 4:
            raise ValueError("L’intensité doit être comprise entre 0 et 4.")
        if not np.isfinite(self.max_reduction_db) or not 0 <= self.max_reduction_db <= 36:
            raise ValueError("L’atténuation maximale doit être comprise entre 0 et 36 dB.")


def noise_segment(audio: AudioData, start: float, end: float) -> np.ndarray:
    """Extraire au moins 150 ms ; ne jamais présumer que le début est silencieux."""
    if not np.isfinite([start, end]).all() or not 0 <= start < end <= audio.duration:
        raise ValueError("Sélectionnez un intervalle valide à l’intérieur du fichier.")
    first, last = round(start * audio.sample_rate), round(end * audio.sample_rate)
    if last - first < round(.15 * audio.sample_rate):
        raise ValueError("Sélectionnez au moins 0,15 seconde contenant uniquement du bruit.")
    return audio.samples[first:last]


def denoise(audio: AudioData, noise_start: float, noise_end: float,
            settings: DenoiseSettings | None = None) -> AudioData:
    settings = settings or DenoiseSettings()
    noise = noise_segment(audio, noise_start, noise_end)
    if settings.strength == 0 or settings.max_reduction_db == 0:
        return AudioData(audio.samples.copy(), audio.sample_rate)

    # Fenêtre de 32 ms, arrondie à un nombre pair ; recouvrement de 75 %.
    frame = max(32, int(round(audio.sample_rate * .032 / 2)) * 2)
    overlap = frame - frame // 4
    kwargs = dict(fs=audio.sample_rate, window="hann", nperseg=frame, noverlap=overlap)
    gain_floor = 10 ** (-settings.max_reduction_db / 20)
    output = np.empty_like(audio.samples)
    for channel in range(audio.channels):
        _, _, z = stft(audio.samples[:, channel], **kwargs, boundary="zeros", padded=True)
        # Pas de remplissage par zéros du profil, qui sous-estimerait le bruit.
        _, _, nz = stft(noise[:, channel], **kwargs, boundary=None, padded=False)
        noise_power = np.mean(np.abs(nz) ** 2, axis=1, keepdims=True)
        power = np.abs(z) ** 2
        # G = sqrt(max(1 - alpha * Pbruit / Psignal, Gmin²)).
        ratio = settings.strength * noise_power / np.maximum(power, np.finfo(float).tiny)
        mask = np.sqrt(np.maximum(1 - ratio, gain_floor ** 2))
        mask = uniform_filter(mask, size=(3, 5), mode="nearest")
        mask = np.clip(mask, gain_floor, 1.0)
        _, restored = istft(z * mask, **kwargs, input_onesided=True, boundary=True)
        output[:, channel] = restored[:len(audio.samples)]
    return AudioData(output, audio.sample_rate)
