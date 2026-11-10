# Audio Denoising DSP

Projet académique du module **Vision artificielle** : réduction du bruit dans les enregistrements vocaux et étude de l’échantillonnage, avec une approche classique de traitement numérique du signal (**DSP**).

## Objectif

Importer un enregistrement vocal bruité, atténuer le bruit de fond, écouter le résultat et exporter un fichier WAV. Le traitement est local et ne repose sur aucun modèle de deep learning.

## Périmètre

- Une voix principale et du bruit de fond, en priorité relativement stationnaire : souffle ou ventilation.
- Estimation du bruit à partir d’un passage explicitement sélectionné et contenant uniquement du bruit.
- Débruitage spectral avec transformée de Fourier à court terme, atténuation fréquentielle et reconstruction.
- Comparaison des formes d’onde et des spectrogrammes avant et après traitement.
- Expériences de rééchantillonnage avec filtrage anti-repliement.

La séparation de locuteurs, la séparation musicale, la transcription et le traitement temps réel sont hors périmètre. Une suppression parfaite du bruit n’est pas garantie.

## Développement progressif

Chaque partie fonctionnelle fait l’objet d’un commit et d’un push distincts :

1. Documentation initiale.
2. Structure Python, lecture/export WAV et rééchantillonnage.
3. Débruitage DSP et tests sur des signaux contrôlés.
4. Interface locale de comparaison et documentation d’utilisation.

## Technologies envisagées

Python, NumPy, SciPy, SoundFile, Matplotlib et Streamlit. Aucun entraînement, réseau neuronal ou service audio externe.

## Évaluation

Tests sur des signaux de référence auxquels du bruit est ajouté ; mesures du rapport signal sur bruit et écoute comparative. Des enregistrements réels permettront d’évaluer l’intelligibilité, le bruit résiduel et les artefacts. Aucun enregistrement personnel ne doit être versionné.

## État

La base Python est disponible : lecture WAV/MP3, export WAV PCM 16 bits et rééchantillonnage anti-repliement. Le débruitage spectral est disponible et testé. Voir [la méthode DSP](docs/METHODE_DSP.md). L’interface est la prochaine étape.

Installation : `python -m venv .venv`, puis `python -m pip install -r requirements.lock.txt` et `python -m pip install -e . --no-deps` dans l’environnement activé. Tests : `python -m pytest -q`.
