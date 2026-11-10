"""Lecture contrôlée, export WAV et rééchantillonnage anti-repliement."""
from dataclasses import dataclass
from io import BytesIO
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

MAX_BYTES = 25 * 1024 * 1024
MAX_DURATION = 120
MAX_SAMPLES = 12_000_000  # Total de valeurs, tous canaux confondus.
MIN_RATE, MAX_RATE = 8_000, 96_000


@dataclass(frozen=True)
class AudioData:
    samples: np.ndarray  # (échantillons, canaux), amplitude flottante.
    sample_rate: int

    def __post_init__(self):
        x = np.asarray(self.samples, dtype=np.float64)
        if x.ndim == 1:
            x = x[:, None]
        if x.ndim != 2 or x.shape[0] == 0 or x.shape[1] not in (1, 2):
            raise ValueError("Un signal non vide, mono ou stéréo, est requis.")
        if not isinstance(self.sample_rate, (int, np.integer)) or not MIN_RATE <= self.sample_rate <= MAX_RATE:
            raise ValueError("La fréquence doit être un entier entre 8 000 et 96 000 Hz.")
        if x.shape[0] / self.sample_rate > MAX_DURATION or x.size > MAX_SAMPLES:
            raise ValueError("Enregistrement trop long ou trop volumineux pour cette version.")
        if not np.isfinite(x).all():
            raise ValueError("Le signal contient des valeurs audio non finies.")
        object.__setattr__(self, "samples", x)

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sample_rate

    @property
    def channels(self) -> int:
        return self.samples.shape[1]


def read_audio(data: bytes) -> AudioData:
    """Vérifier les métadonnées avant de décoder ; WAV et MP3 seulement."""
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Le fichier doit être non vide et ne pas dépasser 25 Mo.")
    try:
        with sf.SoundFile(BytesIO(data)) as f:
            if f.format not in ("WAV", "WAVEX", "RF64", "MP3"):
                raise ValueError("Utilisez un fichier WAV ou MP3.")
            if f.channels not in (1, 2) or not MIN_RATE <= f.samplerate <= MAX_RATE:
                raise ValueError("Format requis : mono ou stéréo, de 8 à 96 kHz.")
            if f.frames <= 0 or f.frames / f.samplerate > MAX_DURATION or f.frames * f.channels > MAX_SAMPLES:
                raise ValueError("Limite : 120 secondes et 12 millions de valeurs audio.")
            return AudioData(f.read(dtype="float64", always_2d=True), f.samplerate)
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise ValueError("Fichier illisible ou codec indisponible. Essayez un WAV PCM.") from exc


def wav_bytes(audio: AudioData) -> tuple[bytes, float]:
    """WAV PCM 16 bits ; gain commun seulement si nécessaire pour éviter l'écrêtage.

    Le gain est renvoyé pour rendre cette modification visible à l'utilisateur.
    Aucun relèvement automatique de niveau n'est appliqué.
    """
    peak = float(np.max(np.abs(audio.samples)))
    gain = min(1.0, (1.0 - 1 / 32768) / peak) if peak else 1.0
    stream = BytesIO()
    sf.write(stream, audio.samples * gain, audio.sample_rate, format="WAV", subtype="PCM_16")
    return stream.getvalue(), gain


def resample_audio(audio: AudioData, target_rate: int) -> AudioData:
    """Filtre FIR polyphasé ; conserve canaux, durée et hauteur de la voix."""
    if not isinstance(target_rate, (int, np.integer)) or not MIN_RATE <= target_rate <= MAX_RATE:
        raise ValueError("La fréquence cible doit être comprise entre 8 000 et 96 000 Hz.")
    if target_rate == audio.sample_rate:
        return AudioData(audio.samples.copy(), target_rate)
    size = (len(audio.samples) * target_rate + audio.sample_rate - 1) // audio.sample_rate
    if size * audio.channels > MAX_SAMPLES:
        raise ValueError("Le rééchantillonnage dépasserait la limite mémoire du projet.")
    factor = gcd(int(audio.sample_rate), int(target_rate))
    y = resample_poly(audio.samples, target_rate // factor, audio.sample_rate // factor, axis=0)
    # Une durée arrondie au prochain échantillon peut dépasser 120 s d'une fraction.
    y = y[:min(size, target_rate * MAX_DURATION)]
    return AudioData(y, target_rate)
