# Résultats initiaux

Vérification du 10 novembre 2026, sous Windows 11 AMD64 avec Python 3.12.14, NumPy 2.2.6 et SciPy 1.15.3.

## Tests

34 tests automatisés réussis : lecture/export, rééchantillonnage, débruitage, erreurs d’entrée et parcours de l’interface. Le parcours de démonstration a également été vérifié dans le navigateur local : sélection du profil, traitement, affichage du résultat et présence du téléchargement WAV.

## Mesures sur signaux synthétiques

Signaux harmoniques modulés de 4 secondes à 16 kHz. Profil de bruit de 0 à 0,6 s ; intensité 1,5 ; atténuation maximale du masque 18 dB. SNR calculé sur les échantillons où l’amplitude absolue de la référence dépasse 0,005. Le seuil explique que le SNR mesuré soit différent du niveau de mélange nominal de 5 dB, défini sur l’ensemble des intervalles actifs.

| Bruit | Graine | SNR avant | SNR après | Amélioration |
|---|---:|---:|---:|---:|
| Blanc | 7 | 5,91 dB | 13,03 dB | 7,12 dB |
| Blanc | 42 | 5,90 dB | 13,16 dB | 7,26 dB |
| Blanc | 123 | 5,94 dB | 13,09 dB | 7,15 dB |
| Coloré | 7 | 5,90 dB | 9,37 dB | 3,47 dB |
| Coloré | 42 | 5,88 dB | 9,63 dB | 3,74 dB |
| Coloré | 123 | 5,90 dB | 9,44 dB | 3,54 dB |

Le temps du traitement DSP seul observé lors de cette exécution était de 0,011 à 0,012 seconde par extrait, sans inclure le décodage, l’interface ni les graphiques. Ce relevé indicatif n’est pas un benchmark matériel reproductible ; le processeur exact et les conditions de charge devront être consignés lors de l’évaluation finale.

Reproduction : `python scripts/evaluate.py`.

## Validation encore nécessaire

Ces signaux ne sont pas de vraies voix. La campagne d’écoute sur au moins trois extraits vocaux et deux types de bruit reste à effectuer selon [le protocole de validation](VALIDATION.md). Les chiffres ci-dessus ne garantissent pas une amélioration identique sur un message vocal réel.
