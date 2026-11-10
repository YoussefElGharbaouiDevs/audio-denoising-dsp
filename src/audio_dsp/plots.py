"""Comparaisons avec des échelles communes et un coût d'affichage borné."""
import numpy as np
from matplotlib.figure import Figure
from scipy.signal import spectrogram

from .audio import AudioData


def comparison_figure(before: AudioData, after: AudioData, channel: int = 0) -> Figure:
    fig = Figure(figsize=(11, 6), layout="constrained")
    axes = fig.subplots(2, 2)
    peak = max(float(np.max(abs(before.samples[:, channel]))), float(np.max(abs(after.samples[:, channel]))), .01)
    spectra = []
    for column, (audio, title, color) in enumerate([(before, "Original", "#64748b"), (after, "Résultat", "#087e8b")]):
        x = audio.samples[:, channel]
        # Min/max par bloc : conserver les pics même pour les longs enregistrements.
        step = max(1, int(np.ceil(len(x)/3000)))
        indices = np.arange(0, len(x), step)
        low = np.minimum.reduceat(x, indices)
        high = np.maximum.reduceat(x, indices)
        time = indices/audio.sample_rate
        ax = axes[0, column]
        if step == 1:
            ax.plot(time, low, color=color, linewidth=.7)
        else:
            ax.fill_between(time, low, high, color=color, alpha=.7)
        ax.set(title=title, xlabel="Temps (s)", ylabel="Amplitude", ylim=(-peak*1.05, peak*1.05), xlim=(0, before.duration))
        ax.grid(alpha=.15)
        frame = min(len(x), max(32, int(audio.sample_rate*.032)))
        hop = min(frame, max(frame//4, int(np.ceil(len(x)/700))))
        f, t, power = spectrogram(x, audio.sample_rate, window="hann", nperseg=frame,
                                  noverlap=frame-hop, scaling="spectrum", mode="psd")
        # Réduire aussi l'affichage lorsque hop est borné par la taille de fenêtre.
        stride = max(1, int(np.ceil(power.shape[1]/700)))
        spectra.append((f, t[::stride], 10*np.log10(np.maximum(power[:, ::stride], 1e-14))))
    vmax = max(float(np.max(s[2])) for s in spectra)
    for column, (f, t, db) in enumerate(spectra):
        im = axes[1, column].pcolormesh(t, f/1000, db, shading="auto", cmap="magma", vmin=vmax-80, vmax=vmax)
        axes[1, column].set(xlabel="Temps (s)", ylabel="Fréquence (kHz)", ylim=(0, max(before.sample_rate,after.sample_rate)/2000), xlim=(0,before.duration))
    fig.colorbar(im, ax=list(axes[1]), label="Puissance relative (dB)", shrink=.85)
    return fig
