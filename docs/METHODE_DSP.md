# Méthode DSP

## Chaîne de débruitage

Le fichier est décodé en amplitudes flottantes, avec conservation de la fréquence et des canaux. L’utilisateur sélectionne explicitement un passage contenant uniquement du bruit (au moins 150 ms ; 0,5 à 1 s est préférable si disponible). Le début du fichier n’est jamais présumé être du bruit seul.

1. STFT avec fenêtre de Hann de 32 ms et recouvrement de 75 %.
2. Moyenne du spectre de puissance des trames du passage de bruit : `Pn(f) = moyenne(|N(f,t)|²)`.
3. Calcul du masque : `G(f,t) = sqrt(max(1 - alpha * Pn(f) / max(|X(f,t)|², epsilon), Gmin²))`.
4. Lissage sur 3 cases fréquentielles et 5 trames temporelles pour limiter les variations et le bruit musical.
5. Application du masque au spectre complexe, conservation de sa phase, puis STFT inverse.
6. Conservation du nombre d’échantillons initial. Chaque canal est traité séparément.

`alpha` règle la force de soustraction. `Gmin = 10^(-R/20)` fixe le plancher de gain, avec `R` l’atténuation maximale en dB. Une intensité de zéro désactive le traitement. Les bornes du masque n’assurent pas une limite exacte d’atténuation de chaque échantillon temporel.

Cette méthode suppose un bruit relativement stationnaire et un profil représentatif. Si le profil contient de la parole, certaines composantes vocales peuvent être supprimées. Le lissage et le plancher réduisent les artefacts sans les éliminer. Les bruits transitoires, la réverbération et les voix concurrentes restent difficiles.

## Échantillonnage

La fonction `scipy.signal.resample_poly` applique un filtre FIR polyphasé. Une réduction de fréquence élimine les composantes au-dessus de la nouvelle bande utile avant la décimation. La durée reste identique à l’arrondi près d’un échantillon ; la hauteur des sons est conservée. Augmenter la fréquence ne restaure pas les fréquences perdues. Cette expérience travaille sur l’original, indépendamment du débruitage.

## Niveaux et exportation

Le signal n’est pas normalisé automatiquement pour le rendre plus fort. L’export utilise du WAV PCM 16 bits. Si le pic dépasse la plage représentable, un gain commun aux canaux est appliqué et signalé. La quantification de sortie n’ajoute pas de dither dans cette première version.

Les comparaisons utilisent les mêmes échelles d’amplitude et de couleur. La baisse du niveau sur le passage de bruit sélectionné est descriptive : elle ne constitue pas un SNR ni une preuve de préservation de la parole.

## Évaluation et limites des résultats

Avec une référence propre et alignée : `SNR = 10 log10(sum(reference²) / sum((reference - résultat)²))`. Sans référence propre, aucun gain de SNR ne peut être affirmé directement à partir du seul résultat.

Les tests automatisés utilisent des signaux harmoniques modulés, trois graines aléatoires et deux bruits (blanc et coloré). Ce sont des tests contrôlés, pas une validation perceptive sur de vraies voix. La validation académique devra aussi inclure au moins trois extraits vocaux et deux types de bruit, des écoutes avant/après et les temps de traitement sur la machine utilisée.

## Références techniques

- [STFT dans SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.stft.html)
- [STFT inverse dans SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.istft.html)
- [Rééchantillonnage polyphasé dans SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html)

Les fonctions STFT historiques de SciPy sont utilisées ici pour rendre les étapes explicites. Aucun modèle neuronal, entraînement ou service distant n’intervient dans le traitement.
