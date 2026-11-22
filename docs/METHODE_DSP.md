# Méthode DSP

## Chaîne de débruitage

Le fichier est décodé en amplitudes flottantes, avec conservation de la fréquence et des canaux. Le profil de bruit est estimé automatiquement par défaut, ou fourni par l’utilisateur via plusieurs passages en mode manuel (au moins 150 ms par passage ; 0,5 à 1 s est préférable). Le début du fichier n’est jamais présumé être du bruit seul.

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


## Plusieurs passages de bruit

Le mode manuel accepte de 1 à 5 intervalles, chacun d’au moins 150 ms. Les chevauchements sont fusionnés pour ne pas surpondérer les mêmes échantillons. La STFT est calculée séparément sur chaque passage : les extraits ne sont pas concaténés, ce qui évite une discontinuité artificielle. Le profil est la moyenne de toutes leurs trames. Il représente un bruit moyen, pas une estimation variant automatiquement avec le temps.


## Estimation automatique par faible énergie

Il s’agit d’une heuristique DSP hors ligne explicite, sans réseau neuronal et sans apprentissage. Elle ne constitue pas une implémentation de l’algorithme complet de minimum statistics de Martin, ni un détecteur de parole certifié.

1. Calculer une STFT sans remplissage aux bords pour analyser uniquement de vraies trames.
2. Calculer leur énergie spectrale ; en stéréo, moyenner les énergies, jamais les amplitudes (pour éviter les annulations de phase).
3. Relever les quantiles d’énergie Q20, Q35 et Q80 sur tout le fichier.
4. Sélectionner les trames d’énergie inférieure ou égale à `min(Q35, Q20 + 0.03 * (Q80 - Q20))`.
5. Estimer le profil spectral de chaque canal par la moyenne des puissances des trames candidates.
6. Appliquer la même soustraction spectrale et la même reconstruction que dans le mode manuel.

Les trames candidates peuvent se trouver avant, après ou entre les phrases. Aucun raccord d’extraits n’est réalisé. Le profil obtenu est global et suppose un bruit relativement stationnaire ; ce n’est pas un suivi continu de chaque changement de bruit.

Un contraste `10 log10(Q80 / Q20)` inférieur à 3 dB, ou moins de trois trames candidates, déclenche un repli conservateur : l’original est renvoyé, avec un message visible. Ce contraste n’est ni un SNR ni une probabilité de succès. Le silence et les réglages à zéro sont également préservés.

Une voix faible peut être sélectionnée par erreur. Des bruits transitoires très forts peuvent au contraire être exclus des trames candidates et rester audibles. Une parole continue sans pause, un bruit très variable ou plusieurs locuteurs limitent cette méthode. Le mode manuel permet de corriger le profil quand des passages fiables existent.

Pour situer le sujet dans la littérature : [R. Martin, Noise Power Spectral Density Estimation Based on Optimal Smoothing and Minimum Statistics, 2001](https://www.iks.rwth-aachen.de/publikationen/publications-detail//martin01c/). Cette référence décrit une méthode plus élaborée ; elle n’est pas présentée comme l’algorithme implémenté ici.
