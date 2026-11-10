"""Évaluation reproductible sans fichier audio externe."""
import platform
import time

import numpy as np

from audio_dsp.denoise import denoise
from audio_dsp.evaluation import snr_db, synthetic_demo

print(f"Python {platform.python_version()} | {platform.system()} {platform.release()} | {platform.machine()}")
print("Signaux harmoniques synthetiques, PAS des voix reelles. SNR sur les echantillons actifs.")
print("bruit     graine   avant_dB   apres_dB   gain_dB   temps_s")
for kind in ('white', 'colored'):
    for seed in (7, 42, 123):
        clean, noisy = synthetic_demo(kind, seed)
        start = time.perf_counter()
        result = denoise(noisy, 0, .6)
        elapsed = time.perf_counter()-start
        active = np.abs(clean.samples[:, 0]) > .005
        before = snr_db(clean.samples[active], noisy.samples[active])
        after = snr_db(clean.samples[active], result.samples[active])
        print(f"{kind:8} {seed:6d} {before:10.2f} {after:10.2f} {after-before:9.2f} {elapsed:9.3f}")
