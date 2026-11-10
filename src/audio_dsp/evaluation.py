"""Mesures avec référence alignée et signaux de démonstration reproductibles."""
import numpy as np
from scipy.signal import lfilter

from .audio import AudioData


def snr_db(reference: np.ndarray, estimate: np.ndarray) -> float:
    ref, est = np.asarray(reference), np.asarray(estimate)
    if ref.shape != est.shape or ref.size == 0 or not np.isfinite(ref).all() or not np.isfinite(est).all():
        raise ValueError("Le SNR requiert deux signaux finis, non vides et alignés de même forme.")
    energy = float(np.sum(ref**2))
    error = float(np.sum((ref-est)**2))
    if energy == 0:
        raise ValueError("Le SNR n’est pas défini pour une référence silencieuse.")
    return float('inf') if error == 0 else float(10*np.log10(energy/error))


def synthetic_demo(kind: str = 'white', seed: int = 42) -> tuple[AudioData, AudioData]:
    """Signal harmonique modulé, pas une voix réelle ; bruit seul de 0 à 0,6 s."""
    if kind not in ('white', 'colored'):
        raise ValueError("Type de bruit inconnu.")
    rate = 16000
    t = np.arange(4*rate)/rate
    envelope = np.zeros_like(t)
    for center, width in [(1., .22), (1.7, .28), (2.5, .24), (3.3, .3)]:
        distance = np.abs(t-center)/width
        envelope += np.where(distance < 1, .5*(1+np.cos(np.pi*np.minimum(distance, 1))), 0)
    phase = 2*np.pi*(160*t + 3*np.sin(2*np.pi*.7*t))
    clean = envelope * sum(np.sin(k*phase)/k for k in range(1, 9)) * .20
    rng = np.random.default_rng(seed)
    noise = rng.normal(size=len(t))
    if kind == 'colored': noise = lfilter([1.], [1., -.85], noise)
    active = clean != 0
    # SNR d'entrée 5 dB sur les intervalles actifs, pas sur les silences.
    noise *= np.sqrt(np.mean(clean[active]**2)) / (10**(5/20)*np.sqrt(np.mean(noise[active]**2)))
    return AudioData(clean, rate), AudioData(clean+noise, rate)
