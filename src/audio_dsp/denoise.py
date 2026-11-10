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


def normalize_ranges(audio: AudioData, ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Valider, trier et fusionner les chevauchements pour ne pas compter deux fois le bruit."""
    if not ranges:
        raise ValueError("Sélectionnez au moins un passage de bruit.")
    for start, end in ranges:
        noise_segment(audio, start, end)
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _stft_parameters(audio: AudioData) -> dict:
    frame = max(32, int(round(audio.sample_rate * .032 / 2)) * 2)
    return dict(fs=audio.sample_rate, window="hann", nperseg=frame, noverlap=frame-frame//4)


def _apply_mask(z: np.ndarray, noise_power: np.ndarray, settings: DenoiseSettings) -> np.ndarray:
    gain_floor = 10 ** (-settings.max_reduction_db / 20)
    power = np.abs(z) ** 2
    ratio = settings.strength * noise_power / np.maximum(power, np.finfo(float).tiny)
    mask = np.sqrt(np.maximum(1 - ratio, gain_floor ** 2))
    mask = uniform_filter(mask, size=(3, 5), mode="nearest")
    return z * np.clip(mask, gain_floor, 1.0)


def denoise_ranges(audio: AudioData, ranges: list[tuple[float, float]],
                   settings: DenoiseSettings | None = None) -> AudioData:
    """Moyenner les spectres de plusieurs passages, sans raccorder leurs échantillons."""
    settings = settings or DenoiseSettings()
    ranges = normalize_ranges(audio, ranges)
    if settings.strength == 0 or settings.max_reduction_db == 0:
        return AudioData(audio.samples.copy(), audio.sample_rate)
    kwargs = _stft_parameters(audio)
    output = np.empty_like(audio.samples)
    for channel in range(audio.channels):
        _, _, z = stft(audio.samples[:, channel], **kwargs, boundary="zeros", padded=True)
        total_power = np.zeros((z.shape[0], 1))
        count = 0
        for start, end in ranges:
            noise = noise_segment(audio, start, end)[:, channel]
            _, _, nz = stft(noise, **kwargs, boundary=None, padded=False)
            total_power += np.sum(np.abs(nz) ** 2, axis=1, keepdims=True)
            count += nz.shape[1]
        _, restored = istft(_apply_mask(z, total_power/count, settings), **kwargs,
                             input_onesided=True, boundary=True)
        output[:, channel] = restored[:len(audio.samples)]
    return AudioData(output, audio.sample_rate)


def denoise(audio: AudioData, noise_start: float, noise_end: float,
            settings: DenoiseSettings | None = None) -> AudioData:
    """Compatibilité avec l'appel historique à un seul passage."""
    return denoise_ranges(audio, [(noise_start, noise_end)], settings)
